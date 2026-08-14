/**
 * API client.
 *
 * Two very different shapes live here. The catalogue and deals endpoints are
 * ordinary JSON GETs. The chat endpoint is Server-Sent Events, and it is parsed
 * by hand rather than with `EventSource` because `EventSource` cannot issue a
 * POST — and the request carries a message body, a session id, a tool seed, and
 * optionally the user's own API key in a header.
 */

import type { CatalogueResponse, DealsResponse, StreamEvent, ToolSeed } from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status?: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function getJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { Accept: "application/json", ...init?.headers },
  });
  if (!response.ok) {
    throw new ApiError(`${path} returned ${response.status}`, response.status);
  }
  return (await response.json()) as T;
}

/**
 * The curated destination set and facet vocabularies.
 *
 * Static for the lifetime of a deploy — it is a Python literal, not a query — so
 * it is cached for an hour rather than refetched on every navigation.
 */
export function fetchCatalogue(): Promise<CatalogueResponse> {
  return getJson<CatalogueResponse>("/api/destinations", {
    next: { revalidate: 3600 },
  } as RequestInit);
}

/**
 * Cached starting fares from one origin.
 *
 * Can legitimately come back empty: the endpoint never calls a flight provider,
 * so an unwarmed origin has nothing to show. Callers must render that as "cek
 * harga" rather than as a price.
 */
export function fetchDeals(origin?: string): Promise<DealsResponse> {
  const query = origin ? `?origin=${encodeURIComponent(origin)}` : "";
  return getJson<DealsResponse>(`/api/deals${query}`, {
    next: { revalidate: 900 },
  } as RequestInit);
}

export interface ChatOptions {
  message: string;
  sessionId?: string | null;
  seed?: ToolSeed;
  apiKey?: string | null;
  provider?: string | null;
  signal?: AbortSignal;
}

/**
 * Stream one turn from the agent.
 *
 * Yields decoded events as they arrive. The caller drives it with `for await`,
 * which means backpressure and cancellation both work the way they look like
 * they should — abort the signal and the loop ends.
 *
 * Frames are split on the blank line that terminates an SSE event, and the tail
 * of a chunk is held back until its terminator arrives. Parsing per-chunk
 * instead would corrupt any event unlucky enough to straddle a TCP boundary,
 * which in practice means the long ones: exactly the tool results that matter.
 */
export async function* streamChat(options: ChatOptions): AsyncGenerator<StreamEvent> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Accept: "text/event-stream",
  };
  if (options.apiKey) {
    headers["X-LLM-Api-Key"] = options.apiKey;
    if (options.provider) headers["X-LLM-Provider"] = options.provider;
  }

  const response = await fetch(`${BASE}/api/chat/stream`, {
    method: "POST",
    headers,
    signal: options.signal,
    body: JSON.stringify({
      message: options.message,
      session_id: options.sessionId ?? null,
      seed: options.seed ?? null,
    }),
  });

  if (!response.ok || !response.body) {
    throw new ApiError(`Chat stream failed (${response.status})`, response.status);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // An SSE event ends at a blank line. Anything after the last one is a
      // partial frame and stays in the buffer.
      const frames = buffer.split("\n\n");
      buffer = frames.pop() ?? "";

      for (const frame of frames) {
        const line = frame.split("\n").find((l) => l.startsWith("data: "));
        if (!line) continue;

        const payload = line.slice(6);
        if (payload === "[DONE]") return;

        try {
          yield JSON.parse(payload) as StreamEvent;
        } catch {
          // A frame we cannot parse is a bug on one side or the other, but it is
          // not worth tearing down a conversation over. Skip it and keep going.
          console.warn("Unparseable SSE frame", payload);
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}

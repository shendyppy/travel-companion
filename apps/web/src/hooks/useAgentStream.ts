"use client";

/**
 * The conversation engine, shared by the landing hero and /chat.
 *
 * There is exactly one of these on purpose. The hero and the companion screen
 * are two presentations of the same turn — a form submission and a typed
 * sentence enter the agent through the same door, so they had better come out of
 * the same hook. If the hero ever grows its own reduced copy of this, the two
 * will drift and the "same engine" claim stops being true.
 *
 * The interesting part is `parts`. The agent interleaves: it writes a sentence,
 * calls a tool, then keeps writing. So a message is an ordered list of text and
 * tool segments, and a `text_delta` appends to the *last* part only if that part
 * is text — otherwise it opens a new one after the tool. Flattening tools into a
 * separate array beside the text would lose the ordering, and the ordering is
 * the thing that makes the agent legible.
 */

import { useCallback, useRef, useState } from "react";
import { streamChat } from "@/lib/api";
import type { Message, MessagePart, StreamEvent, ToolActivity, ToolSeed } from "@/lib/types";

let counter = 0;
const nextId = () => `m${++counter}`;

export interface SendOptions {
  /** A tool call the caller already decided on — from a form, tile, or chip. */
  seed?: ToolSeed;
}

export interface AgentStreamState {
  messages: Message[];
  suggestions: string[];
  sessionId: string | null;
  /** Demo messages left today. null once the user brings their own key. */
  quotaRemaining: number | null;
  quotaExceeded: boolean;
  isStreaming: boolean;
  /** True once anything has been sent — the hero uses this to morph. */
  hasStarted: boolean;
  send: (message: string, options?: SendOptions) => Promise<void>;
  /** Continue a conversation started elsewhere, e.g. the landing hero. */
  adopt: (messages: Message[], sessionId: string | null) => void;
  stop: () => void;
  reset: () => void;
}

export function useAgentStream(apiKey?: string | null, provider?: string | null): AgentStreamState {
  const [messages, setMessages] = useState<Message[]>([]);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [quotaRemaining, setQuotaRemaining] = useState<number | null>(null);
  const [quotaExceeded, setQuotaExceeded] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [hasStarted, setHasStarted] = useState(false);

  const abortRef = useRef<AbortController | null>(null);
  // Read inside the stream loop, so it has to be a ref: `sessionId` state would
  // still be null on the first turn when the session event arrives mid-stream.
  const sessionRef = useRef<string | null>(null);

  const stop = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    setIsStreaming(false);
  }, []);

  /**
   * Take over a conversation that started somewhere else.
   *
   * The session id matters more than the messages: it is what keeps the *next*
   * turn attached to the history the server already holds, so the agent
   * remembers what was said in the hero. The messages are only what the user
   * sees while scrolling back.
   *
   * `counter` is bumped past the adopted ids so freshly generated ones cannot
   * collide with them and give React duplicate keys.
   */
  const adopt = useCallback((adopted: Message[], adoptedSession: string | null) => {
    if (!adopted.length) return;
    counter = Math.max(
      counter,
      ...adopted.map((m) => Number(m.id.replace(/\D/g, "")) || 0),
    );
    setMessages(adopted);
    sessionRef.current = adoptedSession;
    setSessionId(adoptedSession);
    setHasStarted(true);
  }, []);

  const reset = useCallback(() => {
    stop();
    setMessages([]);
    setSuggestions([]);
    setSessionId(null);
    sessionRef.current = null;
    setQuotaExceeded(false);
    setHasStarted(false);
  }, [stop]);

  const send = useCallback(
    async (message: string, options?: SendOptions) => {
      const text = message.trim();
      if (!text || abortRef.current) return;

      const controller = new AbortController();
      abortRef.current = controller;

      const agentId = nextId();
      setHasStarted(true);
      setIsStreaming(true);
      setSuggestions([]);
      setMessages((prev) => [
        ...prev,
        { id: nextId(), role: "user", parts: [{ kind: "text", text }], at: Date.now() },
        { id: agentId, role: "agent", parts: [], pending: true, at: Date.now() },
      ]);

      /** Rewrite the in-flight agent message. */
      const patch = (fn: (message: Message) => Message) =>
        setMessages((prev) => prev.map((m) => (m.id === agentId ? fn(m) : m)));

      const appendText = (chunk: string) =>
        patch((m) => {
          const parts = [...m.parts];
          const last = parts[parts.length - 1];
          if (last?.kind === "text") {
            parts[parts.length - 1] = { kind: "text", text: last.text + chunk };
          } else {
            parts.push({ kind: "text", text: chunk });
          }
          return { ...m, parts };
        });

      const openTool = (activity: ToolActivity) =>
        patch((m) => ({ ...m, parts: [...m.parts, { kind: "tool", activity }] }));

      const closeTool = (tool: string, result: ToolActivity["result"]) =>
        patch((m) => {
          const parts = [...m.parts];
          // Resolve the most recent unresolved call for this tool. Several can
          // run at once, and results do not necessarily arrive in call order.
          for (let i = parts.length - 1; i >= 0; i--) {
            const part = parts[i] as MessagePart;
            if (part.kind === "tool" && part.activity.tool === tool && !part.activity.result) {
              parts[i] = { kind: "tool", activity: { ...part.activity, result } };
              break;
            }
          }
          return { ...m, parts };
        });

      try {
        for await (const event of streamChat({
          message: text,
          sessionId: sessionRef.current,
          seed: options?.seed,
          apiKey,
          provider,
          signal: controller.signal,
        })) {
          handle(event);
        }
      } catch (error) {
        if ((error as Error)?.name !== "AbortError") {
          patch((m) => ({
            ...m,
            error: "Koneksi ke agent terputus. Coba lagi ya.",
          }));
          console.error(error);
        }
      } finally {
        patch((m) => ({ ...m, pending: false }));
        abortRef.current = null;
        setIsStreaming(false);
      }

      function handle(event: StreamEvent) {
        switch (event.type) {
          case "session":
            sessionRef.current = event.session_id;
            setSessionId(event.session_id);
            break;
          case "quota":
            setQuotaRemaining(event.remaining);
            break;
          case "quota_exceeded":
            setQuotaExceeded(true);
            patch((m) => ({ ...m, error: event.error }));
            break;
          case "seed_rejected":
            // Not a user-facing failure: the turn still runs on the message
            // alone. It does mean the client sent something wrong, so it should
            // be loud in development and invisible in production.
            console.warn(`Seed for ${event.tool} was rejected: ${event.reason}`);
            break;
          case "text_delta":
            appendText(event.content);
            break;
          case "tool_start":
            openTool({ id: nextId(), tool: event.tool, arguments: event.arguments });
            break;
          case "tool_result":
            closeTool(event.tool, event.result);
            break;
          case "suggestions":
            setSuggestions(event.suggestions);
            break;
          case "error":
            patch((m) => ({ ...m, error: event.error }));
            break;
        }
      }
    },
    [apiKey, provider],
  );

  return {
    messages,
    suggestions,
    sessionId,
    quotaRemaining,
    quotaExceeded,
    isStreaming,
    hasStarted,
    send,
    adopt,
    stop,
    reset,
  };
}

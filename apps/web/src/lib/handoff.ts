/**
 * Carrying the hero's conversation into /chat.
 *
 * The first exchange happens on the landing page, and the user then continues in
 * the companion. The session id alone is not enough: the server has the history,
 * but exposing it over a `GET /api/session/{id}` would make every conversation
 * readable to anyone holding an id, and that is a bad trade for one navigation.
 *
 * So the transcript rides in `sessionStorage`. It never leaves the tab, it dies
 * with it, and the handoff is a same-browser problem anyway. The session id goes
 * along too, so the *next* turn still lands on the same server-side history and
 * the agent keeps its memory.
 *
 * Read once and cleared, so a later visit to /chat starts fresh rather than
 * resurrecting a conversation the user thought they had left.
 */

import type { Message } from "./types";

const KEY = "tc:handoff";

export interface Handoff {
  sessionId: string | null;
  messages: Message[];
}

export function stashHandoff(handoff: Handoff): void {
  try {
    sessionStorage.setItem(KEY, JSON.stringify(handoff));
  } catch {
    // Private mode, storage full, or a browser that refuses. The handoff is a
    // convenience; losing it means /chat opens empty, which is survivable.
  }
}

export function takeHandoff(): Handoff | null {
  try {
    const raw = sessionStorage.getItem(KEY);
    if (!raw) return null;
    sessionStorage.removeItem(KEY);
    return JSON.parse(raw) as Handoff;
  } catch {
    return null;
  }
}

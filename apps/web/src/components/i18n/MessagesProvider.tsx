"use client";

/**
 * Makes the dictionary reachable from client components.
 *
 * The alternative was passing `messages` down through `LandingClient` into
 * `Hero` into `SearchCommandBar` into `FlightSearchForm`, which is four levels
 * of prop that exist only to carry a constant. Context is the right shape for a
 * value that never changes during a page's life and that almost every leaf
 * needs.
 *
 * Server components do not use this — they call `getMessages(locale)` directly,
 * which is cheaper and keeps the dictionary out of the client bundle for pages
 * that have no interactive parts.
 */

import { createContext, useContext, useMemo } from "react";
import { fill, type Locale, type Messages } from "@/lib/i18n";

interface Ctx {
  locale: Locale;
  m: Messages;
  /** Interpolate a translated string: `t(m.hero.quotaLeft, { n: 3 })`. */
  t: (template: string, values: Record<string, string | number>) => string;
}

const MessagesContext = createContext<Ctx | null>(null);

export function MessagesProvider({
  locale,
  messages,
  children,
}: {
  locale: Locale;
  messages: Messages;
  children: React.ReactNode;
}) {
  const value = useMemo<Ctx>(() => ({ locale, m: messages, t: fill }), [locale, messages]);
  return <MessagesContext.Provider value={value}>{children}</MessagesContext.Provider>;
}

/**
 * Throws rather than falling back to Indonesian when the provider is missing.
 *
 * A silent fallback would mean an English visitor sees one stray Indonesian
 * component and nobody finds out for months. Failing loudly in development is
 * the cheaper mistake.
 */
export function useMessages(): Ctx {
  const ctx = useContext(MessagesContext);
  if (!ctx) throw new Error("useMessages must be used inside <MessagesProvider>");
  return ctx;
}

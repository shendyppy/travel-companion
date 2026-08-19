"use client";

/**
 * The companion screen.
 *
 * Two columns on desktop: the conversation on the left, the trip panel on the
 * right. On mobile the conversation goes full-screen and the panel becomes a
 * bottom sheet with a peek showing how far along the plan is — buried behind a
 * button it would lose the companion feeling entirely, and mobile is where most
 * of the audience is.
 *
 * It picks up whatever the landing page hero already started, so continuing a
 * conversation is a navigation rather than a restart.
 */

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { ChevronUp, Compass } from "lucide-react";
import { cn } from "@/lib/utils";
import { useAgentStream } from "@/hooks/useAgentStream";
import { takeHandoff } from "@/lib/handoff";
import { ChatBubble } from "@/components/organisms/ChatBubble";
import { ChatInput } from "@/components/organisms/ChatInput";
import { TripPanel, deriveTrip } from "@/components/organisms/TripPanel";
import { Chip } from "@/components/ui/chip";
import { useMessages } from "@/components/i18n/MessagesProvider";

export function ChatClient() {
  const agent = useAgentStream();
  const [sheetOpen, setSheetOpen] = useState(false);
  const threadRef = useRef<HTMLDivElement>(null);
  const restored = useRef(false);
  const { m, t, locale } = useMessages();
  const openers = [m.chat.opener1, m.chat.opener2, m.chat.opener3];

  // Pick up the hero's conversation. Runs once — a later visit starts fresh
  // rather than resurrecting something the user thought they had left.
  useEffect(() => {
    if (restored.current) return;
    restored.current = true;
    const handoff = takeHandoff();
    if (handoff?.messages?.length) agent.adopt(handoff.messages, handoff.sessionId);
  }, [agent]);

  // Follow the stream. `end` rather than `start` so a long answer keeps its tail
  // in view as it grows.
  useEffect(() => {
    threadRef.current?.scrollTo({
      top: threadRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [agent.messages]);

  const trip = deriveTrip(agent.messages);
  const filled = [trip.destination, trip.departureDate, trip.flight].filter(Boolean).length;

  return (
    <div className="flex h-dvh flex-col">
      <header className="flex h-14 shrink-0 items-center gap-3 border-b border-border px-4">
        <Link href={`/${locale}`} className="flex items-center gap-2 font-semibold tracking-tight">
          <span className="grid size-7 place-items-center rounded-md bg-accent" aria-hidden>
            <Compass className="size-4 text-accent-fg" />
          </span>
          Travel Companion
        </Link>
        {agent.quotaRemaining !== null && (
          <span
            className={cn(
              "tabular ml-auto rounded-pill px-2.5 py-1 text-xs",
              agent.quotaRemaining <= 1
                ? "bg-warning-soft text-warning"
                : "text-fg-subtle",
            )}
          >
            {t(m.chat.freeMessages, { n: agent.quotaRemaining })}
          </span>
        )}
      </header>

      <div className="flex min-h-0 flex-1">
        <div className="flex min-w-0 flex-1 flex-col">
          <div ref={threadRef} className="min-h-0 flex-1 overflow-y-auto">
            <div className="mx-auto grid max-w-2xl gap-thread px-4 py-6">
              {agent.messages.length === 0 ? (
                <div className="pt-8">
                  <h1 className="text-2xl font-semibold tracking-tight">{m.chat.title}</h1>
                  <p className="mt-2 text-fg-muted">{m.chat.lead}</p>
                  <div className="mt-5 flex flex-wrap gap-2">
                    {openers.map((opener) => (
                      <Chip key={opener} onClick={() => void agent.send(opener)}>
                        {opener}
                      </Chip>
                    ))}
                  </div>
                </div>
              ) : (
                agent.messages.map((message) => (
                  <ChatBubble
                    key={message.id}
                    message={message}
                    onAsk={(text) => void agent.send(text)}
                  />
                ))
              )}

              {agent.suggestions.length > 0 && !agent.isStreaming && (
                <div className="flex flex-wrap gap-2 pl-11">
                  {agent.suggestions.map((suggestion) => (
                    <Chip key={suggestion} onClick={() => void agent.send(suggestion)}>
                      {suggestion}
                    </Chip>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="shrink-0 border-t border-border p-3 pb-20 lg:pb-3">
            <div className="mx-auto max-w-2xl">
              <ChatInput
                onSend={(message) => void agent.send(message)}
                onStop={agent.stop}
                busy={agent.isStreaming}
                autoFocus
              />
            </div>
          </div>
        </div>

        <div className="hidden w-80 shrink-0 overflow-y-auto border-l border-border p-panel lg:block">
          <TripPanel messages={agent.messages} />
        </div>
      </div>

      {/* Mobile: a peeking sheet. It has to stay visible — the plan filling in
          is the product, and hiding it behind a button loses that on the
          platform most of the audience uses. */}
      <div className="lg:hidden">
        {sheetOpen && (
          <button
            type="button"
            aria-label={m.chat.closePanel}
            onClick={() => setSheetOpen(false)}
            className="animate-fade fixed inset-0 z-40 bg-ink-950/40"
          />
        )}
        <div
          className={cn(
            "fixed inset-x-0 bottom-0 z-50 rounded-t-panel border-t border-border bg-surface shadow-sheet",
            "transition-transform duration-[--duration-normal] ease-[--ease-out]",
            sheetOpen ? "max-h-[70dvh] overflow-y-auto" : "",
          )}
        >
          <button
            type="button"
            onClick={() => setSheetOpen((v) => !v)}
            aria-expanded={sheetOpen}
            className="flex w-full items-center gap-3 px-4 py-3 text-left"
          >
            <span className="text-sm font-medium">{m.trip.title}</span>
            <span className="tabular text-xs text-fg-muted">{filled}/4</span>
            <span className="ml-auto flex gap-1" aria-hidden>
              {[0, 1, 2, 3].map((i) => (
                <span
                  key={i}
                  className={cn(
                    "h-1 w-6 rounded-pill",
                    i < filled ? "bg-accent" : "bg-surface-3",
                  )}
                />
              ))}
            </span>
            <ChevronUp
              className={cn(
                "size-4 shrink-0 text-fg-muted transition-transform",
                sheetOpen && "rotate-180",
              )}
              aria-hidden
            />
          </button>

          {sheetOpen && (
            <div className="border-t border-border p-4">
              <TripPanel messages={agent.messages} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

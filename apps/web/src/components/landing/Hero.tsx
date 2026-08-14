"use client";

/**
 * The hero, including the live agent.
 *
 * The non-negotiable from the brief: this contains a working agent, not a
 * screenshot. A visitor types or fills a form and watches the thing think, call
 * a real tool, and answer — roughly five seconds after landing, without signing
 * up for anything.
 *
 * Four states, and the container has to look composed in all of them: empty,
 * filled, streaming, resolved. Resolved is the tallest, which is why the answer
 * region reserves a minimum height the moment a turn starts. Letting it grow
 * from zero would shift the page under the reader at exactly the moment the
 * first token arrives.
 *
 * The conversation state itself lives in `LandingClient`, not here, because the
 * deals rail and the inspiration grid submit into the same turn. A hero that
 * owned the only copy would force those to be links to somewhere else.
 */

import { useRef } from "react";
import { ArrowRight, RotateCcw } from "lucide-react";
import { ChatBubble } from "@/components/chat/ChatBubble";
import { ChatInput } from "@/components/chat/ChatInput";
import { Chip } from "@/components/ui/chip";
import { SearchCommandBar } from "./SearchCommandBar";
import type { Submission } from "./FlightSearchForm";
import type { Facets } from "@/lib/types";
import type { AgentStreamState } from "@/hooks/useAgentStream";

export function Hero({
  facets,
  agent,
  run,
  summary,
  expanded,
  onExpand,
  onHandOff,
  answerRef,
}: {
  facets: Facets | null;
  agent: AgentStreamState;
  run: (submission: Submission) => void;
  summary: string;
  expanded: boolean;
  onExpand: () => void;
  onHandOff: () => void;
  answerRef: React.RefObject<HTMLDivElement | null>;
}) {
  const started = agent.hasStarted;
  const headingRef = useRef<HTMLDivElement>(null);

  return (
    <section className="mx-auto w-full max-w-3xl px-5 pb-12 pt-12 sm:pt-20">
      <div ref={headingRef} className={started ? "mb-6" : "mb-8 sm:mb-10"}>
        <h1 className="text-balance text-3xl font-semibold tracking-tight sm:text-4xl">
          Rencanain perjalanan, bukan cuma cari tiket.
        </h1>
        {!started && (
          <p className="animate-fade mt-3 text-pretty text-lg text-fg-muted">
            Ceritain budget dan vibe-nya. Dia cariin destinasi, ngecek harga penerbangan
            beneran, terus nyusun itinerary-nya.
          </p>
        )}
      </div>

      <SearchCommandBar
        facets={facets}
        onSubmit={run}
        busy={agent.isStreaming}
        collapsed={started && !expanded}
        summary={summary}
        onExpand={onExpand}
      />

      {started && (
        <div
          ref={answerRef}
          className="animate-rise mt-5 min-h-56 rounded-panel border border-border bg-surface p-4 sm:p-5"
        >
          <div className="grid gap-thread">
            {agent.messages
              .filter((message) => message.role === "agent")
              .map((message) => (
                <ChatBubble key={message.id} message={message} />
              ))}
          </div>

          {agent.suggestions.length > 0 && !agent.isStreaming && (
            <div className="mt-4 flex flex-wrap gap-2">
              {agent.suggestions.slice(0, 3).map((suggestion) => (
                <Chip key={suggestion} onClick={() => run({ message: suggestion } as Submission)}>
                  {suggestion}
                </Chip>
              ))}
            </div>
          )}

          {!agent.isStreaming && (
            <div className="mt-5 flex flex-wrap items-center gap-3 border-t border-border pt-4">
              <button
                type="button"
                onClick={onHandOff}
                className="inline-flex h-10 items-center gap-2 rounded-lg bg-accent px-5 text-sm font-medium text-accent-fg"
              >
                Lanjutkan di companion
                <ArrowRight className="size-4" aria-hidden />
              </button>
              <button
                type="button"
                onClick={agent.reset}
                className="inline-flex h-10 items-center gap-2 rounded-lg px-3 text-sm text-fg-muted hover:text-fg"
              >
                <RotateCcw className="size-3.5" aria-hidden />
                Mulai lagi
              </button>
              {agent.quotaRemaining !== null && (
                <span className="tabular ml-auto text-xs text-fg-subtle">
                  {agent.quotaRemaining} pesan gratis tersisa hari ini
                </span>
              )}
            </div>
          )}
        </div>
      )}

      {started && !agent.isStreaming && (
        <ChatInput
          className="mt-3"
          onSend={(message) => run({ message } as Submission)}
          placeholder="Tanya lanjutannya…"
        />
      )}
    </section>
  );
}

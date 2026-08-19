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
import { cn } from "@/lib/utils";
import { ChatBubble } from "@/components/organisms/ChatBubble";
import { ChatInput } from "@/components/organisms/ChatInput";
import { Button } from "@/components/ui/button";
import { Chip } from "@/components/ui/chip";
import { RouteScene } from "@/components/illustration/Scenes";
import { useMessages } from "@/components/i18n/MessagesProvider";
import { SearchCommandBar } from "@/components/organisms/SearchCommandBar";
import type { Submission } from "@/components/organisms/FlightSearchForm";
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
  const { m, t } = useMessages();

  return (
    // The wash lives on a full-width layer behind the column, not on the column
    // itself. Painted on `max-w-3xl` it stopped dead at 768px and drew a visible
    // rectangle down both sides. `overflow-hidden` keeps it from ever adding a
    // horizontal scrollbar, and `isolate` keeps the negative z-index from
    // escaping past the header.
    <section className="relative isolate overflow-hidden">
      <div className="bg-mesh pointer-events-none absolute inset-x-0 -top-14 bottom-0 -z-10" aria-hidden />
      <div className="relative mx-auto w-full max-w-3xl px-5 pb-12 pt-12 sm:pt-20">
      {/* Before a turn starts the block cascades in — illustration, headline,
          lead, 60ms apart. Once the agent is running the stagger comes off:
          re-animating the heading every time an answer arrives would be motion
          for its own sake, and it would pull the eye away from the tokens
          actually streaming in below. */}
      <div
        ref={headingRef}
        className={cn(started ? "mb-6" : "mb-8 stagger sm:mb-10")}
      >
        {!started && (
          <RouteScene className="mb-6 hidden h-24 w-full max-w-sm text-fg-muted sm:block" />
        )}
        {/* The accent half of the headline carries the warm ramp, not the brand
            ramp. Brand blue is the colour of things you can click; using it here
            would make a heading look like the primary action and quietly compete
            with the search bar directly beneath it. */}
        <h1 className="display text-4xl sm:text-5xl">
          {m.hero.titleLead} <span className="text-warm">{m.hero.titleAccent}</span>
        </h1>
        {!started && (
          <p className="animate-fade mt-4 max-w-xl text-pretty text-lg leading-relaxed text-fg-muted">
            {m.hero.lead}
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
              <Button type="button" onClick={onHandOff}>
                {m.hero.continueInCompanion}
                <ArrowRight className="size-4" aria-hidden />
              </Button>
              <Button type="button" variant="ghost" onClick={agent.reset}>
                <RotateCcw className="size-3.5" aria-hidden />
                {m.hero.startOver}
              </Button>
              {agent.quotaRemaining !== null && (
                <span className="tabular ml-auto text-xs text-fg-subtle">
                  {t(m.hero.quotaLeft, { n: agent.quotaRemaining })}
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
            placeholder={m.hero.followUp}
          />
        )}
      </div>
    </section>
  );
}

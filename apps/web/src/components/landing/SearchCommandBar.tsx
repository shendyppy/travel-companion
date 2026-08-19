"use client";

/**
 * The hero. A search bar that thinks.
 *
 * Traveloka's search widget has an affordance a chat box does not: visible
 * machinery, obvious inputs, no ambiguity about what the product can do. A chat
 * box has something the widget does not: it can answer anything. The synthesis
 * is one module with three modes where **all three submit to the same place** —
 * the form does not navigate to a results page, it seeds the agent and the
 * answer streams in underneath.
 *
 * That is the claim the whole landing page rests on, so it is worth being
 * precise about what makes it true: the structured modes send a validated tool
 * call *alongside* a human-readable message, the free mode sends only the
 * message, and both go through `useAgentStream` to `/api/chat/stream`. There is
 * no second code path and no "demo mode". What a visitor sees in the hero is the
 * product.
 *
 * Once a turn starts, the bar collapses to a single-line summary and hands the
 * vertical space to the answer. It does not disappear — a visitor who typed the
 * wrong city must be able to see what they asked for.
 */

import { useState } from "react";
import { MessageCircle, Plane, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";
import { ChatInput } from "@/components/chat/ChatInput";
import { useMessages } from "@/components/i18n/MessagesProvider";
import { FlightSearchForm, type Submission } from "./FlightSearchForm";
import { ExploreFacets } from "./ExploreFacets";
import type { Facets } from "@/lib/types";

type Mode = "flights" | "explore" | "ask";

const MODE_ICONS: Record<Mode, typeof Plane> = {
  flights: Plane,
  explore: Sparkles,
  ask: MessageCircle,
};

export function SearchCommandBar({
  facets,
  onSubmit,
  busy,
  collapsed,
  summary,
  onExpand,
}: {
  facets: Facets | null;
  onSubmit: (submission: Submission) => void;
  busy?: boolean;
  /** True once a turn has started — the bar yields space to the answer. */
  collapsed?: boolean;
  summary?: string;
  onExpand?: () => void;
}) {
  // "ask" is the default only when there is nothing structured to offer. A
  // visitor who sees a flight form immediately understands the product; a
  // visitor who sees a blank text box has to guess.
  const [mode, setMode] = useState<Mode>("flights");
  const { m } = useMessages();

  const modes: { id: Mode; label: string }[] = [
    { id: "flights", label: m.commandBar.modeFlights },
    { id: "explore", label: m.commandBar.modeExplore },
    { id: "ask", label: m.commandBar.modeAsk },
  ];

  if (collapsed) {
    return (
      <button
        type="button"
        onClick={onExpand}
        className="flex w-full items-center gap-3 rounded-panel border border-border bg-surface px-4 py-3 text-left transition-colors hover:border-border-strong"
      >
        <Plane className="size-4 shrink-0 text-accent" aria-hidden />
        <span className="min-w-0 flex-1 truncate text-sm text-fg-muted">{summary}</span>
        <span className="shrink-0 text-xs font-medium text-accent">{m.commandBar.change}</span>
      </button>
    );
  }

  return (
    <div
      data-tour="command-bar"
      className="rounded-panel border border-border bg-surface shadow-raised"
    >
      <div
        data-tour="modes"
        role="tablist"
        aria-label={m.commandBar.howToSearch}
        className="no-scrollbar flex gap-1 overflow-x-auto border-b border-border p-1.5"
      >
        {modes.map(({ id, label }) => {
          const Icon = MODE_ICONS[id];
          return (
            <button
              key={id}
              role="tab"
              type="button"
              aria-selected={mode === id}
              onClick={() => setMode(id)}
              className={cn(
                "inline-flex shrink-0 items-center gap-2 rounded-lg px-3.5 py-2 text-sm font-medium",
                "transition-[background-color,color] duration-[--duration-fast]",
                mode === id
                  ? "bg-accent-soft text-accent"
                  : "text-fg-muted hover:bg-surface-2 hover:text-fg",
              )}
            >
              <Icon className="size-4" aria-hidden />
              {label}
            </button>
          );
        })}
      </div>

      <div className="p-4 sm:p-5">
        {mode === "flights" && <FlightSearchForm onSubmit={onSubmit} busy={busy} />}

        {mode === "explore" &&
          (facets ? (
            <ExploreFacets facets={facets} onSubmit={onSubmit} busy={busy} />
          ) : (
            <FacetsSkeleton />
          ))}

        {mode === "ask" && (
          <div className="grid gap-3">
            <ChatInput
              onSend={(message) => onSubmit({ message } as Submission)}
              busy={busy}
              placeholder={m.commandBar.askPlaceholder}
            />
            <p className="text-xs text-fg-muted">{m.commandBar.askHint}</p>
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * The catalogue is fetched on the server, so this is only ever seen if that
 * request failed. It stays a skeleton rather than an error: the other two modes
 * still work, and the page should not announce a partial outage it can route
 * around.
 */
function FacetsSkeleton() {
  return (
    <div className="grid gap-4" aria-hidden>
      {[4, 8, 2].map((count, row) => (
        <div key={row} className="flex flex-wrap gap-2">
          {Array.from({ length: count }).map((_, i) => (
            <span
              key={i}
              className="animate-breathe h-8 rounded-pill bg-surface-2"
              style={{ width: `${70 + ((i * 23) % 50)}px` }}
            />
          ))}
        </div>
      ))}
    </div>
  );
}

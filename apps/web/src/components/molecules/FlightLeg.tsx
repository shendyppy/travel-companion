"use client";

import { cn } from "@/lib/utils";
import { clockTime, humanDuration, stopsLabel } from "@/lib/format";
import { useMessages } from "@/components/i18n/MessagesProvider";
import type { FlightInfo } from "@/lib/types";

/**
 * Departure, the journey, arrival.
 *
 * This block was duplicated line-for-line between the chat card and the results
 * row — about twenty-five lines each, down to the two dots and the hairline
 * between them. It reads as one idea and it is one idea, so it is one component.
 *
 * The line in the middle is `aria-hidden` on purpose. It carries no information
 * a screen reader needs: the duration and the stop count either side of it are
 * already words, and announcing a decorative rule between two times would only
 * get in the way of them.
 */
export function FlightLeg({ flight, className }: { flight: FlightInfo; className?: string }) {
  const { m, locale } = useMessages();

  return (
    <div className={cn("flex flex-1 items-center gap-3", className)}>
      <div>
        <p className="tabular text-lg font-semibold leading-none">
          {clockTime(flight.departure_time, locale)}
        </p>
        <p className="mt-1 font-mono text-xs text-fg-muted">{flight.origin}</p>
      </div>

      <div className="flex flex-1 flex-col items-center gap-1">
        <span className="text-2xs text-fg-muted">{humanDuration(flight.duration, m.common)}</span>
        <div className="flex w-full items-center gap-1" aria-hidden>
          <span className="size-1 rounded-full bg-border-strong" />
          <span className="h-px flex-1 bg-border" />
          <span className="size-1 rounded-full bg-border-strong" />
        </div>
        <span className="text-2xs text-fg-muted">{stopsLabel(flight.stops, m.common)}</span>
      </div>

      <div className="text-right">
        <p className="tabular text-lg font-semibold leading-none">
          {clockTime(flight.arrival_time, locale)}
        </p>
        <p className="mt-1 font-mono text-xs text-fg-muted">{flight.destination}</p>
      </div>
    </div>
  );
}

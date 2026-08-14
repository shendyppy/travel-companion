import { Plane } from "lucide-react";
import { cn } from "@/lib/utils";
import { clockTime, humanDuration, rupiah, stopsLabel } from "@/lib/format";
import type { FlightInfo } from "@/lib/types";

/**
 * One flight.
 *
 * The cheapest option gets a border and a label rather than a colour swap: on a
 * list of six near-identical cards, the eye needs one place to land, and price
 * is the thing Indonesian travellers sort on first. Everything else stays
 * uniform so the distinction reads.
 */
export function FlightCard({ flight, cheapest }: { flight: FlightInfo; cheapest?: boolean }) {
  return (
    <div
      className={cn(
        "rounded-card border bg-surface p-3.5",
        cheapest ? "border-accent" : "border-border",
      )}
    >
      <div className="mb-3 flex items-center justify-between gap-2">
        <div className="flex min-w-0 items-center gap-2">
          <span className="grid size-6 shrink-0 place-items-center rounded-md bg-accent-soft">
            <Plane className="size-3.5 text-accent" aria-hidden />
          </span>
          <span className="truncate text-sm font-medium">{flight.airline}</span>
        </div>
        {cheapest && (
          <span className="shrink-0 rounded-pill bg-accent-soft px-2 py-0.5 text-2xs font-medium text-accent">
            Termurah
          </span>
        )}
      </div>

      <div className="flex items-center gap-3">
        <div>
          <p className="tabular text-lg font-semibold leading-none">
            {clockTime(flight.departure_time)}
          </p>
          <p className="mt-1 font-mono text-xs text-fg-muted">{flight.origin}</p>
        </div>

        <div className="flex flex-1 flex-col items-center gap-1">
          <span className="text-2xs text-fg-muted">{humanDuration(flight.duration)}</span>
          <div className="flex w-full items-center gap-1" aria-hidden>
            <span className="size-1 rounded-full bg-border-strong" />
            <span className="h-px flex-1 bg-border" />
            <span className="size-1 rounded-full bg-border-strong" />
          </div>
          <span className="text-2xs text-fg-muted">{stopsLabel(flight.stops)}</span>
        </div>

        <div className="text-right">
          <p className="tabular text-lg font-semibold leading-none">
            {clockTime(flight.arrival_time)}
          </p>
          <p className="mt-1 font-mono text-xs text-fg-muted">{flight.destination}</p>
        </div>
      </div>

      <p className="tabular mt-3 border-t border-border pt-2.5 font-mono text-base font-semibold text-price">
        {flight.currency === "IDR" ? rupiah(flight.price) : `${flight.currency} ${flight.price}`}
      </p>
    </div>
  );
}

"use client";

import { ArrowUpRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { clockTime, humanDuration, rupiah, stopsLabel } from "@/lib/format";
import { useMessages } from "@/components/i18n/MessagesProvider";
import type { FlightInfo } from "@/lib/types";

/**
 * One flight, in a list of twenty.
 *
 * The denser sibling of `ChatBubble`'s `FlightCard`. That one appears two or
 * three at a time inside a conversation and can afford to be a card; this one is
 * scanned vertically against nineteen others, so everything sits on one line at
 * desktop width and the eye can run straight down a single column of prices.
 *
 * The booking link is the product's only outbound commercial act, and it is
 * deliberately not styled as the loudest thing on the row. This page's job is to
 * help someone decide, not to push them out of it.
 */
export function FlightRow({
  flight,
  cheapest,
  fastest,
  bookingUrl,
}: {
  flight: FlightInfo;
  cheapest?: boolean;
  fastest?: boolean;
  bookingUrl?: string;
}) {
  const { m, locale } = useMessages();

  return (
    <article
      className={cn(
        "rounded-card border bg-surface p-3.5 transition-colors duration-[--duration-fast]",
        cheapest ? "border-accent" : "border-border hover:border-border-strong",
      )}
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:gap-5">
        <div className="flex min-w-0 items-center gap-2.5 sm:w-44">
          <span
            className="tabular grid size-8 shrink-0 place-items-center rounded-md bg-surface-2 font-mono text-2xs font-semibold text-fg-muted"
            aria-hidden
          >
            {flight.airline_code}
          </span>
          <div className="min-w-0">
            <p className="truncate text-sm font-medium">{flight.airline}</p>
            {(cheapest || fastest) && (
              <p className="mt-0.5 flex gap-1.5">
                {cheapest && <Tag>{m.flights.cheapest}</Tag>}
                {fastest && <Tag>{m.flights.fastest}</Tag>}
              </p>
            )}
          </div>
        </div>

        <div className="flex flex-1 items-center gap-3">
          <div>
            <p className="tabular text-lg font-semibold leading-none">
              {clockTime(flight.departure_time, locale)}
            </p>
            <p className="mt-1 font-mono text-xs text-fg-muted">{flight.origin}</p>
          </div>

          <div className="flex flex-1 flex-col items-center gap-1">
            <span className="text-2xs text-fg-muted">
              {humanDuration(flight.duration, m.common)}
            </span>
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

        <div className="flex items-center justify-between gap-3 border-t border-border pt-3 sm:w-48 sm:flex-col sm:items-end sm:gap-1.5 sm:border-0 sm:pt-0">
          <p className="tabular font-mono text-base font-semibold text-price">
            {flight.currency === "IDR"
              ? rupiah(flight.price)
              : `${flight.currency} ${Math.round(flight.price)}`}
          </p>
          {bookingUrl && (
            <a
              href={bookingUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-xs font-medium text-accent hover:underline"
            >
              {m.flights.bookAt}
              <ArrowUpRight className="size-3.5" aria-hidden />
            </a>
          )}
        </div>
      </div>
    </article>
  );
}

function Tag({ children }: { children: React.ReactNode }) {
  return (
    <span className="rounded-pill bg-accent-soft px-1.5 py-0.5 text-2xs font-medium text-accent">
      {children}
    </span>
  );
}

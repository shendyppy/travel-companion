"use client";

import { ArrowUpRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { useMessages } from "@/components/i18n/MessagesProvider";
import { AirlineMark } from "@/components/molecules/AirlineMark";
import { FlightLeg } from "@/components/molecules/FlightLeg";
import { Price } from "@/components/molecules/Price";
import { Pill } from "@/components/molecules/Pill";
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
  const { m } = useMessages();

  return (
    <article
      className={cn(
        "rounded-card border bg-surface p-3.5 transition-colors duration-[--duration-fast]",
        cheapest ? "border-accent" : "border-border hover:border-border-strong",
      )}
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:gap-5">
        <div className="flex min-w-0 items-center gap-2.5 sm:w-44">
          <AirlineMark code={flight.airline_code} name={flight.airline} />
          <div className="min-w-0">
            <p className="truncate text-sm font-medium">{flight.airline}</p>
            {(cheapest || fastest) && (
              <p className="mt-0.5 flex gap-1.5">
                {cheapest && <Pill className="px-1.5">{m.flights.cheapest}</Pill>}
                {fastest && <Pill className="px-1.5">{m.flights.fastest}</Pill>}
              </p>
            )}
          </div>
        </div>

        <FlightLeg flight={flight} />

        <div className="flex items-center justify-between gap-3 border-t border-border pt-3 sm:w-48 sm:flex-col sm:items-end sm:gap-1.5 sm:border-0 sm:pt-0">
          <Price amount={flight.price} currency={flight.currency} />
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

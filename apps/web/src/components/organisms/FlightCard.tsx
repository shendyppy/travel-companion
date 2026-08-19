"use client";

import { cn } from "@/lib/utils";
import { useMessages } from "@/components/i18n/MessagesProvider";
import { AirlineMark } from "@/components/molecules/AirlineMark";
import { FlightLeg } from "@/components/molecules/FlightLeg";
import { Price } from "@/components/molecules/Price";
import { Pill } from "@/components/molecules/Pill";
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
  const { m } = useMessages();

  return (
    <div
      className={cn(
        "rounded-card border bg-surface p-3.5",
        cheapest ? "border-accent" : "border-border",
      )}
    >
      <div className="mb-3 flex items-center justify-between gap-2">
        <div className="flex min-w-0 items-center gap-2">
          {/* The carrier tile rather than a generic plane icon, so a card in the
              conversation and a row on the results page identify the same
              airline the same way. */}
          <AirlineMark code={flight.airline_code} name={flight.airline} className="size-6" />
          <span className="truncate text-sm font-medium">{flight.airline}</span>
        </div>
        {cheapest && <Pill>{m.flights.cheapest}</Pill>}
      </div>

      <FlightLeg flight={flight} />

      <p className="mt-3 border-t border-border pt-2.5">
        <Price amount={flight.price} currency={flight.currency} />
      </p>
    </div>
  );
}

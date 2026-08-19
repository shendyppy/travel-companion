"use client";

/**
 * The trip taking shape.
 *
 * This is what makes the product feel like a companion rather than a chatbot:
 * the user watches their plan fill in instead of scrolling back through the
 * thread to find what was decided.
 *
 * It is derived, not stored. Everything here is read out of the tool results
 * already in the conversation, which means it cannot disagree with what the
 * agent said — there is no second copy of the plan to keep in sync, and no
 * write path that could drift from the transcript.
 *
 * The empty state is not an edge case. The panel is empty for the first minute
 * of every session, so it is the state most users see first and it gets real
 * design rather than a shrug.
 */

import { CalendarDays, CircleDashed, MapPin, Plane } from "lucide-react";
import { cn } from "@/lib/utils";
import { clockTime, longDate, stopsLabel } from "@/lib/format";
import { useMessages } from "@/components/i18n/MessagesProvider";
import { Price } from "@/components/molecules/Price";
import type { FlightInfo, Message } from "@/lib/types";

interface Trip {
  destination?: string;
  country?: string;
  departureDate?: string;
  origin?: string;
  flight?: FlightInfo;
  flightCount?: number;
}

/**
 * Walk the transcript newest-first and take the first answer for each slot.
 *
 * Newest wins because a conversation is a series of corrections: if the user
 * changed their mind from Bali to Lombok, the panel has to show Lombok. Reading
 * oldest-first would pin it to whatever was mentioned earliest.
 */
export function deriveTrip(messages: Message[]): Trip {
  const trip: Trip = {};

  for (let i = messages.length - 1; i >= 0; i--) {
    for (const part of [...messages[i].parts].reverse()) {
      if (part.kind !== "tool" || !part.activity.result?.ok) continue;
      const { tool, result } = part.activity;
      const data = result.data as Record<string, unknown> | undefined;
      if (!data) continue;

      if (tool === "search_flights" && !trip.flight) {
        const flights = (data.flights as FlightInfo[] | undefined) ?? [];
        const cheapest = data.cheapest as FlightInfo | undefined;
        if (cheapest || flights.length) {
          trip.flight = cheapest ?? flights[0];
          trip.flightCount = flights.length;
          trip.origin ??= data.origin as string | undefined;
          trip.destination ??= data.destination as string | undefined;
          trip.departureDate ??= data.departure_date as string | undefined;
        }
      }

      if (tool === "get_destination_info" && !trip.country) {
        const destination = data.destination as Record<string, unknown> | undefined;
        if (destination) {
          trip.destination = destination.name as string;
          trip.country = destination.country as string;
        }
      }
    }
  }

  return trip;
}

export function TripPanel({ messages, className }: { messages: Message[]; className?: string }) {
  const { m, t, locale } = useMessages();
  const trip = deriveTrip(messages);
  const steps = [
    Boolean(trip.destination),
    Boolean(trip.departureDate),
    Boolean(trip.flight),
    false, // itinerary — phase 5
  ];
  const done = steps.filter(Boolean).length;

  return (
    <aside className={cn("flex flex-col gap-4", className)}>
      <header>
        <div className="flex items-baseline justify-between gap-2">
          <h2 className="font-semibold tracking-tight">{m.trip.title}</h2>
          <span className="tabular text-xs text-fg-muted">{done}/4</span>
        </div>
        <div
          className="mt-2 flex gap-1"
          role="progressbar"
          aria-valuenow={done}
          aria-valuemin={0}
          aria-valuemax={4}
          aria-label={m.trip.progress}
        >
          {steps.map((filled, i) => (
            <span
              key={i}
              className={cn(
                "h-1 flex-1 rounded-pill transition-colors duration-[--duration-normal]",
                filled ? "bg-accent" : "bg-surface-3",
              )}
            />
          ))}
        </div>
      </header>

      {done === 0 ? (
        <EmptyState
          lead={m.trip.emptyLead}
          steps={[m.trip.destination, m.trip.date, m.trip.flight, m.trip.itinerary]}
        />
      ) : (
        <div className="grid gap-3">
          {trip.destination && (
            <Section icon={MapPin} label={m.trip.destination}>
              <p className="font-medium">{trip.destination}</p>
              {trip.country && <p className="text-sm text-fg-muted">{trip.country}</p>}
            </Section>
          )}

          {trip.departureDate && (
            <Section icon={CalendarDays} label={m.trip.date}>
              <p className="font-medium">{longDate(trip.departureDate, locale)}</p>
            </Section>
          )}

          {trip.flight && (
            <Section icon={Plane} label={m.trip.flight}>
              <p className="font-medium">{trip.flight.airline}</p>
              <p className="tabular mt-1 text-sm text-fg-muted">
                {clockTime(trip.flight.departure_time, locale)} {trip.flight.origin} →{" "}
                {clockTime(trip.flight.arrival_time, locale)} {trip.flight.destination}
              </p>
              <p className="mt-2">
                <Price amount={trip.flight.price} currency={trip.flight.currency} />
              </p>
              <p className="text-2xs text-fg-muted">
                {stopsLabel(trip.flight.stops, m.common)}
                {trip.flightCount && trip.flightCount > 1
                  ? t(m.trip.optionsFound, { n: trip.flightCount })
                  : ""}
              </p>
            </Section>
          )}

          <Section icon={CircleDashed} label={m.trip.itinerary} muted>
            <p className="text-sm text-fg-muted">{m.trip.itineraryEmpty}</p>
          </Section>
        </div>
      )}
    </aside>
  );
}

function Section({
  icon: Icon,
  label,
  children,
  muted,
}: {
  icon: typeof MapPin;
  label: string;
  children: React.ReactNode;
  muted?: boolean;
}) {
  return (
    <div
      className={cn(
        "animate-rise rounded-card border p-3.5",
        muted ? "border-dashed border-border bg-transparent" : "border-border bg-surface",
      )}
    >
      <p className="mb-2 flex items-center gap-1.5 text-2xs font-medium uppercase tracking-wide text-fg-subtle">
        <Icon className="size-3" aria-hidden />
        {label}
      </p>
      {children}
    </div>
  );
}

function EmptyState({ lead, steps }: { lead: string; steps: string[] }) {
  return (
    <div className="rounded-card border border-dashed border-border p-5">
      <p className="text-sm text-fg-muted">{lead}</p>
      <ol className="mt-4 grid gap-2 text-sm text-fg-subtle">
        {steps.map((step, i) => (
          <li key={step} className="flex items-center gap-2.5">
            <span className="tabular grid size-5 shrink-0 place-items-center rounded-full border border-border text-2xs">
              {i + 1}
            </span>
            {step}
          </li>
        ))}
      </ol>
    </div>
  );
}

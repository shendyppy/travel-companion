"use client";

/**
 * Renders whatever a tool returned, as cards.
 *
 * Sits directly under its `ToolActivity` line so results stay in the position
 * the tool was called from. The agent interleaves — sentence, tool, sentence —
 * and pulling results out into a sidebar would break the thread of the answer.
 *
 * A tool with no card treatment renders nothing at all. That is intentional: the
 * agent narrates every result in prose anyway, so a tool without a card is not a
 * gap, and dumping unrecognised JSON on screen is precisely the debug-console
 * failure mode this design is trying to avoid.
 */

import { FlightCard } from "@/components/organisms/FlightCard";
import { DestinationCard } from "@/components/organisms/DestinationCard";
import { useMessages } from "@/components/i18n/MessagesProvider";
import type { Destination, FlightInfo, ToolActivity } from "@/lib/types";

const MAX_FLIGHTS = 4;
const MAX_DESTINATIONS = 3;

export function ToolResult({
  activity,
  onAsk,
}: {
  activity: ToolActivity;
  onAsk?: (message: string) => void;
}) {
  const { m, t } = useMessages();
  const result = activity.result;
  if (!result?.ok) return null;

  const data = result.data as Record<string, unknown> | undefined;
  if (!data) return null;

  if (activity.tool === "search_flights") {
    const flights = (data.flights as FlightInfo[] | undefined) ?? [];
    if (!flights.length) return null;
    const cheapest = data.cheapest as FlightInfo | undefined;

    return (
      <div className="mt-2 grid gap-2">
        {flights.slice(0, MAX_FLIGHTS).map((flight, index) => (
          <FlightCard
            key={`${flight.airline_code}-${flight.departure_time}-${index}`}
            flight={flight}
            cheapest={Boolean(cheapest) && flight.price === cheapest!.price && index === 0}
          />
        ))}
        {flights.length > MAX_FLIGHTS && (
          <p className="text-xs text-fg-muted">
            {t(m.tool.moreFlights, { n: flights.length - MAX_FLIGHTS })}
          </p>
        )}
      </div>
    );
  }

  if (activity.tool === "recommend_destinations") {
    const destinations = (data.destinations as Destination[] | undefined) ?? [];
    if (!destinations.length) return null;

    return (
      <div className="mt-2 grid gap-2">
        {destinations.slice(0, MAX_DESTINATIONS).map((destination) => (
          <DestinationCard
            key={destination.name}
            destination={destination}
            onAsk={onAsk ? (city) => onAsk(t(m.tool.tellMeMore, { city })) : undefined}
          />
        ))}
      </div>
    );
  }

  return null;
}

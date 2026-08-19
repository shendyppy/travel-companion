"use client";

/**
 * The route, the date, and a way to change them.
 *
 * Collapsed by default. On a results page the search is settled — the user's
 * attention belongs to the list, and a full form pinned above it would push the
 * first price below the fold on a phone. But "change one thing and search again"
 * is the second most common action here after scrolling, so it is one tap away
 * and prefilled with what was actually searched.
 */

import { useRouter } from "next/navigation";
import { useState } from "react";
import { ArrowRight, PencilLine, Users } from "lucide-react";
import { longDate } from "@/lib/format";
import { FlightSearchForm } from "@/components/organisms/FlightSearchForm";
import { useMessages } from "@/components/i18n/MessagesProvider";
import { flightsHref } from "@/lib/flightsHref";
import type { FlightQuery } from "@/lib/types";

export function SearchHeader({ query }: { query: FlightQuery }) {
  const router = useRouter();
  const [editing, setEditing] = useState(false);
  const { m, locale } = useMessages();

  return (
    <div className="rounded-panel border border-border bg-surface">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-2 px-4 py-3">
        <h1 className="flex items-center gap-2 text-base font-semibold tracking-tight">
          <span className="truncate">{query.origin}</span>
          <ArrowRight className="size-4 shrink-0 text-fg-subtle" aria-hidden />
          <span className="truncate">{query.destination}</span>
        </h1>

        <p className="flex items-center gap-3 text-sm text-fg-muted">
          <span>{longDate(query.departure_date, locale)}</span>
          <span className="flex items-center gap-1">
            <Users className="size-3.5" aria-hidden />
            <span className="tabular">{query.adults}</span>
          </span>
        </p>

        <button
          type="button"
          onClick={() => setEditing((open) => !open)}
          aria-expanded={editing}
          className="ml-auto inline-flex items-center gap-1.5 text-xs font-medium text-accent hover:underline"
        >
          <PencilLine className="size-3.5" aria-hidden />
          {editing ? m.flights.closeEdit : m.flights.editSearch}
        </button>
      </div>

      {editing && (
        <div className="border-t border-border p-4">
          <FlightSearchForm
            initial={query}
            submitLabel={m.flightForm.searchAgain}
            allowFlexible={false}
            onSubmit={({ flightQuery }) => {
              if (flightQuery) router.push(flightsHref(flightQuery, locale));
            }}
          />
          <p className="mt-3 text-xs text-fg-muted">{m.flights.flexibleHint}</p>
        </div>
      )}
    </div>
  );
}

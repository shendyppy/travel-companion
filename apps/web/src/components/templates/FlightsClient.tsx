"use client";

/**
 * Owns the filter state for one result set.
 *
 * Filtering happens here rather than on the server, and the URL is updated with
 * `history.replaceState` rather than `router.push`. Both follow from the same
 * observation: the whole result set is already in the browser, so a checkbox
 * should be instant. Routing on every click would send a request, re-render the
 * server component, and repaint the page to hide four rows the client was
 * already holding.
 *
 * The URL still gets written, because a search someone spent a minute narrowing
 * should survive a refresh and be pasteable into a group chat.
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { SlidersHorizontal } from "lucide-react";
import {
  applyFilters,
  filtersToParams,
  isFiltered,
  parseFilters,
  type FlightFilters,
  type SortKey,
} from "@/lib/flightFilters";
import { FilterRail } from "@/components/organisms/FilterRail";
import { ResultsList } from "@/components/organisms/ResultsList";
import { useMessages } from "@/components/i18n/MessagesProvider";
import type { FlightQuery, FlightSearchResponse } from "@/lib/types";

export function FlightsClient({
  results,
  query,
}: {
  results: FlightSearchResponse;
  query: FlightQuery;
}) {
  const searchParams = useSearchParams();
  const { m } = useMessages();

  // Seeded from the URL once. After that this is the source of truth and the URL
  // follows it — reading back from `searchParams` every render would fight the
  // `replaceState` below.
  const [filters, setFilters] = useState<FlightFilters>(() =>
    parseFilters(new URLSearchParams(searchParams.toString())),
  );

  useEffect(() => {
    const params = new URLSearchParams({
      origin: query.origin,
      destination: query.destination,
      departure_date: query.departure_date,
      adults: String(query.adults),
    });
    if (query.return_date) params.set("return_date", query.return_date);
    for (const [key, value] of filtersToParams(filters)) params.set(key, value);

    window.history.replaceState(null, "", `?${params}`);
  }, [filters, query]);

  const visible = useMemo(() => applyFilters(results.flights, filters), [results.flights, filters]);

  const clearFilters = useCallback(
    () => setFilters((f) => ({ ...f, airlines: [], stops: [], buckets: [], maxPrice: null })),
    [],
  );
  const setSort = useCallback((sort: SortKey) => setFilters((f) => ({ ...f, sort })), []);

  const hasFilters =
    results.facets.airlines.length > 1 ||
    results.facets.stops.length > 1 ||
    results.facets.departure_buckets.length > 1;

  return (
    <div className="grid gap-6 lg:grid-cols-[15rem_1fr] lg:items-start lg:gap-8">
      {hasFilters && (
        <>
          {/* Mobile: a disclosure, so the rail never costs a screen of scrolling
              before the first price. Desktop: always open in the margin. */}
          <details className="rounded-panel border border-border bg-surface lg:hidden" name="rail">
            <summary className="flex cursor-pointer list-none items-center gap-2 px-4 py-3 text-sm font-medium">
              <SlidersHorizontal className="size-4 text-fg-muted" aria-hidden />
              {m.flights.filters}
              {isFiltered(filters) && (
                <span className="ml-auto rounded-pill bg-accent-soft px-2 py-0.5 text-2xs font-medium text-accent">
                  {m.flights.filtersActive}
                </span>
              )}
            </summary>
            <div className="border-t border-border p-4">
              <FilterRail facets={results.facets} filters={filters} onChange={setFilters} />
            </div>
          </details>

          <FilterRail
            facets={results.facets}
            filters={filters}
            onChange={setFilters}
            className="sticky top-20 hidden lg:flex"
          />
        </>
      )}

      <div className={hasFilters ? "" : "lg:col-span-2"}>
        <ResultsList
          results={results}
          visible={visible}
          filters={filters}
          onSort={setSort}
          onClearFilters={clearFilters}
        />
      </div>
    </div>
  );
}

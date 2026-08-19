"use client";

/**
 * The result set: sort control, summary line, rows.
 *
 * Three empty states, and they are genuinely different things that deserve
 * different words:
 *
 *   - the provider found nothing on this route and date
 *   - the provider found flights, but the current filters hide all of them
 *   - the provider could not be reached
 *
 * Collapsing them into one "no results" message is the fastest way to make a
 * working product feel broken. The middle one in particular is not a failure at
 * all — it is a filter the user set thirty seconds ago and can undo.
 */

import { AlertTriangle, SearchX, SlidersHorizontal } from "lucide-react";
import { cn } from "@/lib/utils";
import { humanDuration, longDate, rupiah, staleness } from "@/lib/format";
import { SORT_KEYS, type FlightFilters, type SortKey } from "@/lib/flightFilters";
import { useMessages } from "@/components/i18n/MessagesProvider";
import { FlightRow } from "./FlightRow";
import type { Messages } from "@/lib/i18n";
import type { FlightInfo, FlightSearchResponse } from "@/lib/types";

function sortLabel(m: Messages, key: SortKey): string {
  return {
    cheapest: m.flights.sortCheapest,
    fastest: m.flights.sortFastest,
    earliest: m.flights.sortEarliest,
    latest: m.flights.sortLatest,
  }[key];
}

export function ResultsList({
  results,
  visible,
  filters,
  onSort,
  onClearFilters,
}: {
  results: FlightSearchResponse;
  visible: FlightInfo[];
  filters: FlightFilters;
  onSort: (sort: SortKey) => void;
  onClearFilters: () => void;
}) {
  const { m, t, locale } = useMessages();

  // Computed over what is on screen, not over everything the provider returned:
  // a "termurah" badge on a row the filters just hid would be pointing at
  // nothing.
  const cheapest = visible.reduce<number | null>(
    (min, f) => (f.price && (min === null || f.price < min) ? f.price : min),
    null,
  );
  const quickest = visible.reduce<number | null>(
    (min, f) =>
      f.duration_minutes && (min === null || f.duration_minutes < min) ? f.duration_minutes : min,
    null,
  );

  const age = staleness(results.cached_at, locale);

  return (
    <section className="grid gap-4">
      {/* Optional-chained even though the type says it is always there: web and
          api deploy separately, so a browser can be one release ahead of the
          server it is talking to. A missing field must degrade to "no warning",
          never to a blank page. */}
      {results.dates_returned?.length ? <WrongDateNotice results={results} /> : null}

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="min-w-0">
          <p className="text-sm">
            <span className="tabular font-semibold">{visible.length}</span>
            {visible.length !== results.total_found && (
              <span className="text-fg-muted">
                {" "}
                {t(m.flights.ofTotal, { total: results.total_found })}
              </span>
            )}{" "}
            <span className="text-fg-muted">{m.flights.count}</span>
            {cheapest !== null && (
              <>
                <span className="text-fg-subtle"> · </span>
                <span className="text-fg-muted">{m.flights.startingFrom} </span>
                <span className="tabular font-mono font-semibold text-price">
                  {rupiah(cheapest)}
                </span>
              </>
            )}
          </p>
          {age && (
            <p className="mt-0.5 text-2xs text-fg-subtle">
              {results.cached ? t(m.flights.priceFetched, { age }) : m.flights.priceFresh} ·{" "}
              {m.flights.verifyNote}
            </p>
          )}
        </div>

        <div
          role="tablist"
          aria-label={m.flights.sortBy}
          className="no-scrollbar flex shrink-0 gap-1 overflow-x-auto rounded-pill border border-border bg-surface p-1"
        >
          {SORT_KEYS.map((key) => (
            <button
              key={key}
              role="tab"
              type="button"
              aria-selected={filters.sort === key}
              onClick={() => onSort(key)}
              className={cn(
                "shrink-0 rounded-pill px-3 py-1 text-xs font-medium",
                "transition-[background-color,color] duration-[--duration-fast]",
                filters.sort === key
                  ? "bg-accent-soft text-accent"
                  : "text-fg-muted hover:bg-surface-2 hover:text-fg",
              )}
            >
              {sortLabel(m, key)}
            </button>
          ))}
        </div>
      </div>

      {visible.length === 0 ? (
        results.total_found === 0 ? (
          <Empty icon={SearchX} title={m.flights.emptyTitle} body={m.flights.emptyBody} />
        ) : (
          <Empty
            icon={SlidersHorizontal}
            title={m.flights.filteredOutTitle}
            body={t(m.flights.filteredOutBody, { total: results.total_found })}
            action={{ label: m.flights.resetFilters, onClick: onClearFilters }}
          />
        )
      ) : (
        <div className="grid gap-2">
          {visible.map((flight, index) => (
            <FlightRow
              key={`${flight.airline_code}-${flight.departure_time}-${index}`}
              flight={flight}
              cheapest={cheapest !== null && flight.price === cheapest}
              fastest={
                quickest !== null &&
                flight.duration_minutes === quickest &&
                // Only worth calling out when it is not simply the same row.
                flight.price !== cheapest
              }
              bookingUrl={results.booking_links.traveloka}
            />
          ))}
        </div>
      )}

      {quickest !== null && visible.length > 1 && (
        <p className="text-2xs text-fg-subtle">
          {t(m.flights.fastestNote, {
            duration: humanDuration(
              `${Math.floor(quickest / 60)}h ${quickest % 60}m`,
              m.common,
            ),
          })}
        </p>
      )}
    </section>
  );
}

/**
 * The provider answered with a different day than the one asked for.
 *
 * Prominent on purpose. These are real fares for real flights, so hiding them
 * would throw away useful information — but a price shown under the wrong date
 * is the one thing this product promises never to do, and a footnote is not
 * enough to undo a page heading that says "20 September".
 */
function WrongDateNotice({ results }: { results: FlightSearchResponse }) {
  const { m, t, locale } = useMessages();

  return (
    <div className="flex gap-3 rounded-card border border-warning bg-warning-soft p-3.5">
      <AlertTriangle className="mt-0.5 size-4 shrink-0 text-warning" aria-hidden />
      <div className="min-w-0 text-sm">
        <p className="font-medium">{m.flights.wrongDateTitle}</p>
        <p className="mt-1 text-fg-muted">
          {t(m.flights.wrongDateBody, {
            requested: longDate(results.departure_date, locale),
            actual: results.dates_returned.map((date) => longDate(date, locale)).join(", "),
          })}
        </p>
      </div>
    </div>
  );
}

function Empty({
  icon: Icon,
  title,
  body,
  action,
}: {
  icon: typeof SearchX;
  title: string;
  body: string;
  action?: { label: string; onClick: () => void };
}) {
  return (
    <div className="rounded-card border border-dashed border-border p-8 text-center">
      <Icon className="mx-auto size-5 text-fg-subtle" aria-hidden />
      <p className="mt-3 font-medium">{title}</p>
      <p className="mx-auto mt-1.5 max-w-md text-sm text-fg-muted">{body}</p>
      {action && (
        <button
          type="button"
          onClick={action.onClick}
          className="mt-4 text-sm font-medium text-accent hover:underline"
        >
          {action.label}
        </button>
      )}
    </div>
  );
}

"use client";

/**
 * The filter rail.
 *
 * Every control here is built from the server's facets, which only ever describe
 * values the result set actually contains. That is what keeps the page's rule
 * intact — nothing is clickable that does not work — without any checking in
 * this component: an airline with no flights simply never gets a checkbox.
 *
 * Counts sit next to every option because they are what makes filtering a
 * decision rather than a guess. "Garuda (12)" tells you what you are about to
 * lose; "Garuda" does not.
 */

import { RotateCcw } from "lucide-react";
import { cn } from "@/lib/utils";
import { rupiah, rupiahShort, stopsLabel } from "@/lib/format";
import { isFiltered, toggle, type FlightFilters } from "@/lib/flightFilters";
import { useMessages } from "@/components/i18n/MessagesProvider";
import type { Messages } from "@/lib/i18n";
import type { DepartureBucket, FlightFacets } from "@/lib/types";

export function FilterRail({
  facets,
  filters,
  onChange,
  className,
}: {
  facets: FlightFacets;
  filters: FlightFilters;
  onChange: (next: FlightFilters) => void;
  className?: string;
}) {
  const { m, t } = useMessages();
  const set = (patch: Partial<FlightFilters>) => onChange({ ...filters, ...patch });

  return (
    <div className={cn("flex flex-col gap-5", className)}>
      <div className="flex items-center justify-between gap-2">
        <h2 className="text-sm font-semibold tracking-tight">{m.flights.filters}</h2>
        {isFiltered(filters) && (
          <button
            type="button"
            onClick={() =>
              set({ airlines: [], stops: [], buckets: [], maxPrice: null })
            }
            className="inline-flex items-center gap-1 text-xs font-medium text-accent hover:underline"
          >
            <RotateCcw className="size-3" aria-hidden />
            {m.flights.reset}
          </button>
        )}
      </div>

      {facets.airlines.length > 1 && (
        <Group label={m.flights.airline}>
          {facets.airlines.map((airline) => (
            <Check
              key={airline.code}
              checked={filters.airlines.includes(airline.code)}
              onChange={() => set({ airlines: toggle(filters.airlines, airline.code) })}
              label={airline.name}
              count={airline.count}
              hint={
                airline.min_price
                  ? t(m.flights.from, { amount: rupiahShort(airline.min_price) })
                  : undefined
              }
            />
          ))}
        </Group>
      )}

      {facets.stops.length > 1 && (
        <Group label={m.flights.stopsLabel}>
          {facets.stops.map((stop) => (
            <Check
              key={stop.value}
              checked={filters.stops.includes(stop.value)}
              onChange={() => set({ stops: toggle(filters.stops, stop.value) })}
              label={stopsLabel(stop.value, m.common)}
              count={stop.count}
            />
          ))}
        </Group>
      )}

      {facets.departure_buckets.length > 1 && (
        <Group label={m.flights.departureTime}>
          {facets.departure_buckets.map((bucket) => (
            <Check
              key={bucket.value}
              checked={filters.buckets.includes(bucket.value)}
              onChange={() =>
                set({ buckets: toggle<DepartureBucket>(filters.buckets, bucket.value) })
              }
              // The API sends an Indonesian label with the facet. It is used as
              // the fallback rather than the source so a bucket added server-side
              // still renders something, but a translated one wins.
              label={BUCKET_LABELS(m)[bucket.value] ?? bucket.label}
              count={bucket.count}
            />
          ))}
        </Group>
      )}

      {facets.price && facets.price.max > facets.price.min && (
        <Group label={m.flights.maxPrice}>
          <input
            type="range"
            min={facets.price.min}
            max={facets.price.max}
            step={Math.max(50_000, Math.round((facets.price.max - facets.price.min) / 40))}
            value={filters.maxPrice ?? facets.price.max}
            onChange={(e) => {
              const value = Number(e.target.value);
              // Dragging back to the ceiling clears the filter rather than
              // pinning it at the maximum, so the URL stays clean and the reset
              // affordance disappears when nothing is actually filtered.
              set({ maxPrice: value >= facets.price!.max ? null : value });
            }}
            className="w-full accent-[var(--color-accent)]"
            aria-label={m.flights.maxPrice}
          />
          <p className="tabular mt-1 font-mono text-xs text-fg-muted">
            {filters.maxPrice
              ? t(m.flights.upTo, { amount: rupiah(filters.maxPrice) })
              : t(m.flights.allPrices, {
                  min: rupiahShort(facets.price.min),
                  max: rupiahShort(facets.price.max),
                })}
          </p>
        </Group>
      )}
    </div>
  );
}

function BUCKET_LABELS(m: Messages): Record<string, string> {
  return {
    pagi: m.flights.bucketPagi,
    siang: m.flights.bucketSiang,
    sore: m.flights.bucketSore,
    malam: m.flights.bucketMalam,
  };
}

function Group({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <fieldset className="grid gap-2">
      <legend className="mb-1.5 text-2xs font-medium uppercase tracking-wide text-fg-subtle">
        {label}
      </legend>
      {children}
    </fieldset>
  );
}

function Check({
  checked,
  onChange,
  label,
  count,
  hint,
}: {
  checked: boolean;
  onChange: () => void;
  label: string;
  count: number;
  hint?: string;
}) {
  return (
    <label className="flex cursor-pointer items-center gap-2.5 text-sm">
      <input
        type="checkbox"
        checked={checked}
        onChange={onChange}
        className="size-4 shrink-0 accent-[var(--color-accent)]"
      />
      <span className={cn("min-w-0 flex-1 truncate", checked ? "text-fg" : "text-fg-muted")}>
        {label}
        {hint && <span className="ml-1.5 text-2xs text-fg-subtle">{hint}</span>}
      </span>
      <span className="tabular shrink-0 text-2xs text-fg-subtle">{count}</span>
    </label>
  );
}

/**
 * Filtering and sorting for the results page.
 *
 * Pure functions over a plain filter object, kept out of the components for two
 * reasons: they are the only logic on the page worth testing, and the companion
 * dock needs to describe the *filtered* view to the agent ("dari 23, kamu lagi
 * lihat 6 Garuda pagi") — which means something other than the list itself has
 * to be able to compute it.
 *
 * Filters live in the URL. A search someone spent a minute narrowing down should
 * survive a refresh and be pasteable into a group chat, and both fall out of
 * that for free.
 */

import type { DepartureBucket, FlightInfo } from "./types";

export type SortKey = "cheapest" | "fastest" | "earliest" | "latest";

/** Order the sort control renders in. Labels come from the dictionary. */
export const SORT_KEYS: SortKey[] = ["cheapest", "fastest", "earliest", "latest"];

export interface FlightFilters {
  airlines: string[];
  stops: number[];
  buckets: DepartureBucket[];
  maxPrice: number | null;
  sort: SortKey;
}

export const EMPTY_FILTERS: FlightFilters = {
  airlines: [],
  stops: [],
  buckets: [],
  maxPrice: null,
  sort: "cheapest",
};

const VALID_SORTS = new Set<string>(SORT_KEYS);
const BUCKETS = new Set<string>(["pagi", "siang", "sore", "malam"]);

function list(params: URLSearchParams, key: string): string[] {
  const raw = params.get(key);
  return raw ? raw.split(",").filter(Boolean) : [];
}

/**
 * Read filters out of a query string.
 *
 * Every field is validated rather than trusted. A URL is user-editable and gets
 * shared, mangled by chat apps, and truncated — a `sort=lol` should quietly fall
 * back to the default, not render an empty page.
 */
export function parseFilters(params: URLSearchParams): FlightFilters {
  const sort = params.get("sort");
  const maxPrice = Number(params.get("max_price"));

  return {
    airlines: list(params, "airlines"),
    stops: list(params, "stops")
      .map(Number)
      .filter((n) => Number.isInteger(n) && n >= 0),
    buckets: list(params, "dep").filter((b): b is DepartureBucket => BUCKETS.has(b)),
    maxPrice: Number.isFinite(maxPrice) && maxPrice > 0 ? maxPrice : null,
    sort: sort && VALID_SORTS.has(sort) ? (sort as SortKey) : "cheapest",
  };
}

/** Filters as query params, omitting anything at its default. */
export function filtersToParams(filters: FlightFilters): URLSearchParams {
  const params = new URLSearchParams();
  if (filters.airlines.length) params.set("airlines", filters.airlines.join(","));
  if (filters.stops.length) params.set("stops", filters.stops.join(","));
  if (filters.buckets.length) params.set("dep", filters.buckets.join(","));
  if (filters.maxPrice) params.set("max_price", String(filters.maxPrice));
  if (filters.sort !== "cheapest") params.set("sort", filters.sort);
  return params;
}

export function isFiltered(filters: FlightFilters): boolean {
  return Boolean(
    filters.airlines.length || filters.stops.length || filters.buckets.length || filters.maxPrice,
  );
}

/** Departure time as minutes past midnight; null when it will not parse. */
function departureMinutes(flight: FlightInfo): number | null {
  const raw = flight.departure_time;
  if (!raw) return null;
  const match = /(\d{1,2}):(\d{2})/.exec(raw.includes("T") ? raw.split("T")[1] : raw);
  return match ? Number(match[1]) * 60 + Number(match[2]) : null;
}

/**
 * Missing values sort last in every order.
 *
 * A flight whose duration the provider mangled is still a real flight and must
 * stay in the list, but putting it first under "tercepat" would be a lie. Infinity
 * is the honest position for "we do not know".
 */
function sortValue(flight: FlightInfo, sort: SortKey): number {
  if (sort === "cheapest") return flight.price || Infinity;
  if (sort === "fastest") return flight.duration_minutes ?? Infinity;
  const minutes = departureMinutes(flight);
  if (minutes === null) return Infinity;
  return sort === "earliest" ? minutes : -minutes;
}

export function applyFilters(flights: FlightInfo[], filters: FlightFilters): FlightInfo[] {
  const kept = flights.filter((flight) => {
    if (filters.airlines.length && !filters.airlines.includes(flight.airline_code)) return false;
    if (filters.stops.length && !filters.stops.includes(flight.stops)) return false;
    if (filters.maxPrice && flight.price > filters.maxPrice) return false;
    if (filters.buckets.length) {
      // An untagged flight is hidden once a time filter is on. Showing it would
      // mean "malam" quietly includes departures nobody could place.
      if (!flight.departure_bucket || !filters.buckets.includes(flight.departure_bucket)) {
        return false;
      }
    }
    return true;
  });

  return [...kept].sort((a, b) => sortValue(a, filters.sort) - sortValue(b, filters.sort));
}

/** Toggle one value in a multi-select facet. */
export function toggle<T>(values: T[], value: T): T[] {
  return values.includes(value) ? values.filter((v) => v !== value) : [...values, value];
}

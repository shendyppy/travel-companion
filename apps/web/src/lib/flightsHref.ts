/**
 * The one place a `/flights` URL is built.
 *
 * Three surfaces navigate here — the landing form, the results page's own "cari
 * lagi", and (from phase B) the companion dock — and the query string is also
 * what the dock reads back to tell the agent what the user is looking at. A
 * second hand-built URL somewhere would be a param name away from silently
 * dropping the passenger count.
 */

import type { Locale } from "./i18n";
import type { FlightQuery } from "./types";

export function flightsHref(query: FlightQuery, locale: Locale): string {
  const params = new URLSearchParams({
    origin: query.origin,
    destination: query.destination,
    departure_date: query.departure_date,
    adults: String(query.adults),
  });
  if (query.return_date) params.set("return_date", query.return_date);
  return `/${locale}/flights?${params}`;
}

/**
 * Read a query back out of URL params, or null when it is not a real search.
 *
 * Returns null rather than a half-filled object: a results page with no
 * destination has nothing to render, and letting a blank string through would
 * spend a provider call finding that out.
 */
export function parseFlightQuery(params: {
  origin?: string;
  destination?: string;
  departure_date?: string;
  return_date?: string;
  adults?: string;
}): FlightQuery | null {
  const origin = params.origin?.trim();
  const destination = params.destination?.trim();
  const departure_date = params.departure_date?.trim();

  if (!origin || !destination || !departure_date) return null;
  if (!/^\d{4}-\d{2}-\d{2}$/.test(departure_date)) return null;

  const adults = Number(params.adults ?? 1);

  return {
    origin,
    destination,
    departure_date,
    return_date: params.return_date?.trim() || null,
    adults: Number.isInteger(adults) && adults >= 1 && adults <= 9 ? adults : 1,
  };
}

/**
 * Formatting helpers.
 *
 * Money lives here because IDR shows up on nearly every surface and has to look
 * the same on all of them. Prices run to seven digits — `Rp 1.250.000` — so the
 * separators are not decoration, they are what makes the number readable at a
 * glance. Everything that renders a price goes through `rupiah` or `rupiahShort`
 * and gets the `.tabular` utility.
 *
 * Dates take a locale; money does not. That asymmetry is deliberate. A date is
 * read in the reader's language, so "Sabtu, 20 September" and "Saturday, 20
 * September" are both correct. A price is a fact about Indonesian rupiah, and
 * reformatting `Rp 1.250.000` as `IDR 1,250,000` for an English reader would
 * make it harder to check against the seller's own site, which will always show
 * the Indonesian form.
 */

import { DEFAULT_LOCALE, type Locale } from "./i18n";

const idr = new Intl.NumberFormat("id-ID", {
  style: "currency",
  currency: "IDR",
  maximumFractionDigits: 0,
});

/** `Rp 1.250.000`. Full precision, for anything a user might act on. */
export function rupiah(amount: number): string {
  return idr.format(Math.round(amount)).replace(/ /g, " ");
}

/**
 * `1,2jt` / `450rb`. For chips and rails where the exact digit does not matter
 * and the space does. Never use this on a card the user is choosing between —
 * rounding away twenty thousand rupiah to save four pixels is a bad trade.
 *
 * The suffixes stay Indonesian in both languages. "rb" and "jt" are how the
 * amounts are written on every Indonesian price tag, and an English reader
 * comparing against Traveloka is better served by the form they will see there.
 */
export function rupiahShort(amount: number): string {
  if (amount >= 1_000_000) {
    const millions = amount / 1_000_000;
    const rounded = millions >= 10 ? Math.round(millions) : Math.round(millions * 10) / 10;
    return `${String(rounded).replace(".", ",")}jt`;
  }
  if (amount >= 1_000) return `${Math.round(amount / 1_000)}rb`;
  return String(Math.round(amount));
}

const BCP47: Record<Locale, string> = { id: "id-ID", en: "en-GB" };

/**
 * en-GB rather than en-US: day-before-month matches the Indonesian order, so
 * switching language reorders words without reordering the numbers. "20
 * September" reads the same way round in both, which matters when someone is
 * cross-checking a date against a booking site.
 */
function tag(locale: Locale = DEFAULT_LOCALE): string {
  return BCP47[locale] ?? BCP47[DEFAULT_LOCALE];
}

/** `08:45` from an ISO datetime. Returns the input unchanged if it will not parse. */
export function clockTime(iso: string, locale: Locale = DEFAULT_LOCALE): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return new Intl.DateTimeFormat(tag(locale), { hour: "2-digit", minute: "2-digit" }).format(date);
}

/** `20 Sep`. */
export function shortDate(iso: string, locale: Locale = DEFAULT_LOCALE): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return new Intl.DateTimeFormat(tag(locale), { day: "numeric", month: "short" }).format(date);
}

/** `Sabtu, 20 September` / `Saturday, 20 September`. */
export function longDate(iso: string, locale: Locale = DEFAULT_LOCALE): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return new Intl.DateTimeFormat(tag(locale), {
    weekday: "long",
    day: "numeric",
    month: "long",
  }).format(date);
}

/**
 * How stale a cached fare is, in words.
 *
 * The deals rail is cached and the card has to say so. This reads as a normal
 * part of the card rather than a warning — hiding it is the only way the cache
 * becomes dishonest, so it needs phrasing that a designer will not want to
 * delete.
 *
 * Uses `Intl.RelativeTimeFormat` rather than hand-built strings so both
 * languages get correct grammar from one code path.
 */
export function staleness(updatedAt: string | null, locale: Locale = DEFAULT_LOCALE): string | null {
  if (!updatedAt) return null;
  const then = new Date(updatedAt);
  if (Number.isNaN(then.getTime())) return null;

  const rtf = new Intl.RelativeTimeFormat(tag(locale), { numeric: "auto" });
  const minutes = Math.floor((Date.now() - then.getTime()) / 60_000);

  if (minutes < 1) return rtf.format(0, "minute");
  if (minutes < 60) return rtf.format(-minutes, "minute");

  const hours = Math.floor(minutes / 60);
  if (hours < 24) return rtf.format(-hours, "hour");
  return rtf.format(-Math.floor(hours / 24), "day");
}

/**
 * `2 jam 15 menit` / `2h 15m` — the API returns durations like `2h 15m`.
 *
 * Takes the unit words from the caller rather than hardcoding them, because the
 * dictionary is where translations belong and this file should not import one.
 */
export function humanDuration(
  raw: string,
  units?: { hours: string; minutes: string },
): string {
  const match = /(?:(\d+)h)?\s*(?:(\d+)m)?/.exec(raw.trim());
  if (!match || (!match[1] && !match[2])) return raw;
  if (!units) return raw;

  const parts: string[] = [];
  if (match[1]) parts.push(units.hours.replace("{n}", match[1]));
  if (match[2]) parts.push(units.minutes.replace("{n}", match[2]));
  return parts.join(" ");
}

/**
 * `Langsung` / `2 transit`, or `Direct` / `2 stops`.
 *
 * Same shape as `humanDuration`: the words come from the dictionary, the logic
 * lives here. Keeping the strings out means this file never imports a message
 * bundle and stays usable from anywhere.
 */
export function stopsLabel(stops: number, labels: { direct: string; stops: string }): string {
  return stops === 0 ? labels.direct : labels.stops.replace("{n}", String(stops));
}

/** Today plus `days`, as `YYYY-MM-DD` — the format every flight tool expects. */
export function isoDateIn(days: number): string {
  const date = new Date();
  date.setDate(date.getDate() + days);
  return date.toISOString().slice(0, 10);
}

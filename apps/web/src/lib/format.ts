/**
 * Formatting helpers.
 *
 * Money lives here because IDR shows up on nearly every surface and has to look
 * the same on all of them. Prices run to seven digits — `Rp 1.250.000` — so the
 * separators are not decoration, they are what makes the number readable at a
 * glance. Everything that renders a price goes through `rupiah` or `rupiahShort`
 * and gets the `.tabular` utility.
 */

const idr = new Intl.NumberFormat("id-ID", {
  style: "currency",
  currency: "IDR",
  maximumFractionDigits: 0,
});

/** `Rp 1.250.000`. Full precision, for anything a user might act on. */
export function rupiah(amount: number): string {
  return idr.format(Math.round(amount)).replace(/ /g, " ");
}

/**
 * `1,2jt` / `450rb`. For chips and rails where the exact digit does not matter
 * and the space does. Never use this on a card the user is choosing between —
 * rounding away twenty thousand rupiah to save four pixels is a bad trade.
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

const timeFmt = new Intl.DateTimeFormat("id-ID", { hour: "2-digit", minute: "2-digit" });
const dayFmt = new Intl.DateTimeFormat("id-ID", { day: "numeric", month: "short" });
const longDayFmt = new Intl.DateTimeFormat("id-ID", {
  weekday: "long",
  day: "numeric",
  month: "long",
});

/** `08:45` from an ISO datetime. Returns the input unchanged if it will not parse. */
export function clockTime(iso: string): string {
  const date = new Date(iso);
  return Number.isNaN(date.getTime()) ? iso : timeFmt.format(date);
}

/** `20 Sep` from an ISO date. */
export function shortDate(iso: string): string {
  const date = new Date(iso);
  return Number.isNaN(date.getTime()) ? iso : dayFmt.format(date);
}

/** `Sabtu, 20 September`. */
export function longDate(iso: string): string {
  const date = new Date(iso);
  return Number.isNaN(date.getTime()) ? iso : longDayFmt.format(date);
}

/**
 * How stale a cached fare is, in Indonesian.
 *
 * The deals rail is cached and the card has to say so. This reads as a normal
 * part of the card rather than a warning — hiding it is the only way the cache
 * becomes dishonest, so it needs phrasing that a designer will not want to
 * delete.
 */
export function staleness(updatedAt: string | null): string | null {
  if (!updatedAt) return null;
  const then = new Date(updatedAt);
  if (Number.isNaN(then.getTime())) return null;

  const minutes = Math.floor((Date.now() - then.getTime()) / 60_000);
  if (minutes < 1) return "baru saja";
  if (minutes < 60) return `${minutes} menit lalu`;

  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} jam lalu`;
  return `${Math.floor(hours / 24)} hari lalu`;
}

/** `2 jam 15 menit` — the API returns durations like `2h 15m`. */
export function humanDuration(raw: string): string {
  const match = /(?:(\d+)h)?\s*(?:(\d+)m)?/.exec(raw.trim());
  if (!match || (!match[1] && !match[2])) return raw;
  const parts: string[] = [];
  if (match[1]) parts.push(`${match[1]} jam`);
  if (match[2]) parts.push(`${match[2]} menit`);
  return parts.join(" ");
}

export function stopsLabel(stops: number): string {
  return stops === 0 ? "Langsung" : `${stops} transit`;
}

/** Today plus `days`, as `YYYY-MM-DD` — the format every flight tool expects. */
export function isoDateIn(days: number): string {
  const date = new Date();
  date.setDate(date.getDate() + days);
  return date.toISOString().slice(0, 10);
}

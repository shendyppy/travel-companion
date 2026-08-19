/**
 * Two languages, no library.
 *
 * next-intl and its peers target Next 15; Next 16 is weeks old. For two locales
 * with static dictionaries the whole mechanism is a typed object lookup and a
 * string replace, so taking a dependency here would buy a migration risk against
 * a moving major and very little else.
 *
 * The dictionaries are imported, not fetched. They are a few kilobytes, they are
 * needed on the first paint of every page, and importing them means TypeScript
 * checks that `en` and `id` have the same shape — a missing translation is a
 * build error rather than the word "undefined" appearing on the landing page.
 *
 * Note what is *not* here: the agent's own replies. Those have always been
 * bilingual, because the model answers in whatever language the user wrote in.
 * This file only translates the chrome around it.
 */

import en from "@/messages/en.json";
import id from "@/messages/id.json";

export const LOCALES = ["id", "en"] as const;
export type Locale = (typeof LOCALES)[number];

/** Indonesian is the default: this is an Indonesian travel product first. */
export const DEFAULT_LOCALE: Locale = "id";

/**
 * `id` is the source of truth for the shape. Typing `en` as `Messages` means
 * adding a key to Indonesian and forgetting English fails `tsc`.
 */
export type Messages = typeof id;

const DICTIONARIES: Record<Locale, Messages> = { id, en: en as Messages };

export function isLocale(value: string | undefined): value is Locale {
  return LOCALES.includes(value as Locale);
}

export function getMessages(locale: string | undefined): Messages {
  return isLocale(locale) ? DICTIONARIES[locale] : DICTIONARIES[DEFAULT_LOCALE];
}

/**
 * Fill `{placeholders}` in a translated string.
 *
 * Deliberately tiny and deliberately not a template engine. Anything needing
 * pluralisation or a date belongs in `format.ts`, which already knows about
 * locale, rather than being smuggled into a message key.
 */
export function fill(template: string, values: Record<string, string | number>): string {
  return template.replace(/\{(\w+)\}/g, (match, key) =>
    key in values ? String(values[key]) : match,
  );
}

/**
 * Best locale for an `Accept-Language` header.
 *
 * Quality values are ignored on purpose: with two options, the first supported
 * tag that appears is the right answer, and parsing q-weights to choose between
 * "id" and "en" is precision nobody can perceive.
 */
export function matchLocale(header: string | null): Locale {
  if (!header) return DEFAULT_LOCALE;

  for (const part of header.split(",")) {
    const tag = part.split(";")[0].trim().toLowerCase();
    const base = tag.split("-")[0];
    if (isLocale(base)) return base;
  }

  return DEFAULT_LOCALE;
}

/** Swap the locale segment of a path, keeping everything after it. */
export function localePath(pathname: string, locale: Locale): string {
  const segments = pathname.split("/");
  // ["", "id", "flights"] — index 1 is the locale when the middleware has done
  // its job, which it always has by the time this runs in the browser.
  if (isLocale(segments[1])) {
    segments[1] = locale;
    return segments.join("/");
  }
  return `/${locale}${pathname}`;
}

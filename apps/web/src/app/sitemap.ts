import type { MetadataRoute } from "next";
import { DEFAULT_LOCALE, LOCALES } from "@/lib/i18n";

const SITE = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";

/**
 * Only the landing page, in both languages.
 *
 * `/chat` and `/flights` are deliberately absent and both already carry
 * `robots: { index: false }`. A conversation is not a document, and flight
 * results are a different page every hour — listing them would invite a crawler
 * to walk the date space, which on `/flights` means spending real provider quota
 * to index prices that are stale before the crawl finishes.
 */
export default function sitemap(): MetadataRoute.Sitemap {
  return LOCALES.map((locale) => ({
    url: `${SITE}/${locale}`,
    lastModified: new Date(),
    changeFrequency: "weekly" as const,
    priority: locale === DEFAULT_LOCALE ? 1 : 0.9,
    alternates: {
      languages: Object.fromEntries(LOCALES.map((l) => [l, `${SITE}/${l}`])),
    },
  }));
}

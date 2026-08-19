import { Suspense } from "react";
import { fetchCatalogue, fetchDeals } from "@/lib/api";
import { getMessages, LOCALES } from "@/lib/i18n";
import { SiteNav } from "@/components/organisms/SiteNav";
import { BelowFold } from "@/components/organisms/BelowFold";
import { LandingClient } from "@/components/templates/LandingClient";

const SITE = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";

/**
 * The landing page.
 *
 * Catalogue and deals are fetched here, on the server, so the first paint has
 * real destinations and real cached prices in it. Both are allowed to fail: the
 * API is a separate service, and a page whose hero works is worth serving even
 * when the fare cache is unreachable. `null` flows down and each surface renders
 * its own honest fallback rather than the page 500ing over a rail.
 */
export default async function LandingPage({
  params,
  searchParams,
}: {
  params: Promise<{ locale: string }>;
  searchParams: Promise<{ origin?: string }>;
}) {
  const [{ locale }, { origin }] = await Promise.all([params, searchParams]);
  const m = getMessages(locale);

  const [catalogue, deals] = await Promise.all([
    fetchCatalogue().catch(() => null),
    fetchDeals(origin).catch(() => null),
  ]);

  /*
   * Described as a WebApplication rather than a TravelAgency, which is the
   * schema.org type a travel site would normally reach for. It would be the
   * wrong claim: an agency sells travel, and this sells nothing. Getting that
   * right in the structured data matters more than qualifying for a richer
   * search result, because the whole positioning rests on not being an agency.
   */
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "WebApplication",
    name: "Travel Companion",
    url: `${SITE}/${locale}`,
    applicationCategory: "TravelApplication",
    description: m.meta.description,
    inLanguage: LOCALES,
    isAccessibleForFree: true,
    offers: { "@type": "Offer", price: "0", priceCurrency: "IDR" },
    author: { "@type": "Person", name: "Shendy Putra Perdana Yohansah" },
  };

  return (
    <>
      <script
        type="application/ld+json"
        // Every value here is one of our own strings rather than user input, and
        // JSON.stringify escapes the rest.
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <SiteNav />
      <main>
        <Suspense>
          <LandingClient catalogue={catalogue} deals={deals} />
        </Suspense>
        <BelowFold />
      </main>
    </>
  );
}

import { Suspense } from "react";
import { fetchCatalogue, fetchDeals } from "@/lib/api";
import { SiteNav } from "@/components/landing/SiteNav";
import { BelowFold } from "@/components/landing/BelowFold";
import { LandingClient } from "@/components/landing/LandingClient";

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
  searchParams,
}: {
  searchParams: Promise<{ origin?: string }>;
}) {
  const { origin } = await searchParams;

  const [catalogue, deals] = await Promise.all([
    fetchCatalogue().catch(() => null),
    fetchDeals(origin).catch(() => null),
  ]);

  return (
    <>
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

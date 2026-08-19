import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";
import { CloudOff, Timer } from "lucide-react";
import { ApiError, fetchFlights } from "@/lib/api";
import { parseFlightQuery } from "@/lib/flightsHref";
import { getMessages, type Messages } from "@/lib/i18n";
import { SiteNav } from "@/components/landing/SiteNav";
import { SearchHeader } from "@/components/flights/SearchHeader";
import { FlightsClient } from "@/components/flights/FlightsClient";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  return {
    title: getMessages(locale).meta.flightsTitle,
    // Results are personal and change hourly; there is nothing here worth
    // indexing, and a crawler walking the date space would spend real provider
    // quota.
    robots: { index: false, follow: true },
  };
}

type Params = Record<string, string | string[] | undefined>;

function one(params: Params, key: string): string | undefined {
  const value = params[key];
  return Array.isArray(value) ? value[0] : value;
}

/**
 * The results page.
 *
 * Fetched on the server so the first paint has real prices in it — the whole
 * reason for a results page rather than a loading spinner that fills in. The
 * filters that run over these results are client-side (see `FlightsClient`);
 * only the search itself costs a round trip.
 *
 * Both failure modes render as an explanation rather than an error page. A
 * provider that timed out and a rate limit that fired are normal things for this
 * product to say out loud, and the companion still works in both cases.
 */
export default async function FlightsPage({
  params: routeParams,
  searchParams,
}: {
  params: Promise<{ locale: string }>;
  searchParams: Promise<Params>;
}) {
  const [{ locale }, params] = await Promise.all([routeParams, searchParams]);
  const m = getMessages(locale);
  const query = parseFlightQuery({
    origin: one(params, "origin"),
    destination: one(params, "destination"),
    departure_date: one(params, "departure_date"),
    return_date: one(params, "return_date"),
    adults: one(params, "adults"),
  });

  // Nothing to search for. The landing page has the form; this page has no
  // business rendering an empty shell of one.
  if (!query) redirect(`/${locale}`);

  let results = null;
  let failure: FailureProps | null = null;

  try {
    results = await fetchFlights(query);
  } catch (error) {
    const status = error instanceof ApiError ? error.status : undefined;
    const reason = error instanceof Error ? error.message : "";

    failure =
      status === 429
        ? {
            kind: "rate-limited",
            title: m.flights.rateLimitedTitle,
            body: reason || m.flights.rateLimitedBody,
          }
        : {
            kind: "provider-down",
            title: m.flights.providerDownTitle,
            body: reason || m.flights.providerDownBody,
          };
  }

  return (
    <>
      <SiteNav />
      <main className="mx-auto grid max-w-6xl gap-5 px-5 py-6">
        <SearchHeader query={query} />

        {results ? (
          <FlightsClient results={results} query={query} />
        ) : (
          <Failure {...failure!} m={m} locale={locale} />
        )}
      </main>
    </>
  );
}

interface FailureProps {
  kind: "rate-limited" | "provider-down";
  title: string;
  body: string;
}

function Failure({
  kind,
  title,
  body,
  m,
  locale,
}: FailureProps & { m: Messages; locale: string }) {
  const Icon = kind === "rate-limited" ? Timer : CloudOff;

  return (
    <div className="rounded-card border border-dashed border-border p-8 text-center">
      <Icon className="mx-auto size-5 text-fg-subtle" aria-hidden />
      <p className="mt-3 font-medium">{title}</p>
      <p className="mx-auto mt-1.5 max-w-md text-sm text-fg-muted">{body}</p>
      <p className="mx-auto mt-4 max-w-md text-sm text-fg-muted">
        {m.flights.companionStillWorks}
      </p>
      <Link
        href={`/${locale}/chat`}
        className="mt-4 inline-block text-sm font-medium text-accent hover:underline"
      >
        {m.flights.openCompanion}
      </Link>
    </div>
  );
}

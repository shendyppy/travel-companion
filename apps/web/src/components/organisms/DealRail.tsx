"use client";

/**
 * Starting fares from wherever the visitor is.
 *
 * The biggest "this is a real travel product" win on the page, and the one most
 * easily made dishonest. Two rules it enforces:
 *
 * 1. **The staleness marker is not optional.** These fares come from a cache the
 *    server warms on a schedule; the card says how old they are, in the same
 *    type as everything else on it. A designer who wants to delete it is asking
 *    to present a twelve-hour-old number as live.
 *
 * 2. **A cold rail shows no prices at all.** `updated_at: null` means the cache
 *    was never warmed for this origin, and the cards become "cek harga" buttons
 *    that run a real search instead. A placeholder price here would be the exact
 *    thing the agent is built never to do.
 *
 * Clicking a card does not navigate. It seeds a flight search into the hero,
 * which is the whole point of the rail existing on this page rather than being a
 * link to a search results screen.
 */

import { ArrowRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { isoDateIn, rupiah, shortDate, staleness } from "@/lib/format";
import { Price } from "@/components/molecules/Price";
import { Section } from "@/components/molecules/Section";
import { OriginPicker } from "@/components/molecules/OriginPicker";
import { TravelTypeMark } from "@/components/molecules/TravelTypeMark";
import { FareScene } from "@/components/illustration/Scenes";
import { useMessages } from "@/components/i18n/MessagesProvider";
import type { CatalogueResponse, DealsResponse, Destination, ToolSeed } from "@/lib/types";
import type { Submission } from "@/components/organisms/FlightSearchForm";

/** How many cards the cold rail shows before it stops being a rail and starts being a list. */
const COLD_LIMIT = 8;

export function DealRail({
  deals,
  originLabel,
  onRun,
  catalogue,
}: {
  deals: DealsResponse;
  originLabel: string;
  onRun: (submission: Submission) => void;
  /**
   * Only read when there are no cached fares. The catalogue is what lets the
   * cold rail say something real instead of eight cards repeating "no price
   * yet" — see `ColdRail`.
   */
  catalogue?: CatalogueResponse | null;
}) {
  const { m, t, locale } = useMessages();
  const cold = !deals.updated_at || deals.deals.length === 0;

  // Only destinations we can actually search: a card with no IATA has nothing to
  // put in the tool call behind it.
  const coldPlaces = (catalogue?.destinations ?? [])
    .filter((place) => place.iata)
    .slice(0, COLD_LIMIT);

  const typeLabels = Object.fromEntries(
    (catalogue?.facets.travel_types ?? []).map((type) => [type.value, type.label]),
  );
  const age = staleness(deals.updated_at, locale);

  const search = (city: string, iata: string, date: string) => {
    const seed: ToolSeed = {
      tool: "search_flights",
      arguments: {
        origin: deals.origin,
        destination: iata,
        departure_date: date,
        adults: 1,
      },
    };
    onRun({
      message: t(m.deals.message, {
        origin: originLabel,
        destination: city,
        date: shortDate(date, locale),
      }),
      seed,
    });
  };

  return (
    <Section
      eyebrow={m.deals.eyebrow}
      title={t(m.deals.title, { origin: originLabel })}
      lead={
        cold
          ? m.deals.leadCold
          : t(m.deals.leadWarm, {
              date: deals.departure_date
                ? shortDate(deals.departure_date, locale)
                : m.deals.nextMonth,
              age: age ? t(m.deals.leadAge, { age }) : "",
            })
      }
      aside={<OriginPicker value={deals.origin} />}
      illustration={<FareScene className="size-24" />}
    >
      {deals.requested_origin && deals.requested_origin !== deals.origin && (
        <p className="mb-4 rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm text-fg-muted">
          {t(m.deals.clamped, { requested: deals.requested_origin, served: originLabel })}
        </p>
      )}

      <div className="no-scrollbar -mx-5 flex snap-x snap-mandatory gap-3 overflow-x-auto px-5 pb-1">
        {cold ? (
          <ColdRail destinations={coldPlaces} typeLabels={typeLabels} onPick={search} />
        ) : (
          deals.deals.map((deal) => (
            <button
              key={deal.iata}
              type="button"
              onClick={() => search(deal.city, deal.iata, deals.departure_date ?? isoDateIn(30))}
              className={cn(
                "group lift pressable w-52 shrink-0 snap-start rounded-card border border-border bg-surface p-4 text-left",
                "transition-[border-color,box-shadow,transform] duration-[--duration-fast]",
                "hover:-translate-y-0.5 hover:border-border-strong hover:shadow-card",
              )}
            >
              <p className="font-medium">{deal.city}</p>
              <p className="text-xs text-fg-muted">{deal.country}</p>

              <p className="mt-4">
                <Price amount={deal.price_idr} size="lg" />
              </p>
              <p className="text-2xs text-fg-muted">
                {deal.airline ?? m.deals.oneWay} ·{" "}
                {deal.stops === 0 ? m.deals.direct : t(m.deals.stops, { n: deal.stops })}
              </p>

              {deal.daily_cost_idr ? (
                <p className="tabular mt-2 border-t border-border pt-2 text-2xs text-fg-muted">
                  {t(m.deals.dailyThere, { amount: rupiah(deal.daily_cost_idr) })}
                </p>
              ) : null}

              <span className="mt-3 inline-flex items-center gap-1 text-xs font-medium text-accent">
                {m.deals.checkFlights}
                <ArrowRight
                  className="size-3 transition-transform group-hover:translate-x-0.5"
                  aria-hidden
                />
              </span>
            </button>
          ))
        )}
      </div>
    </Section>
  );
}

/**
 * What the rail looks like with nothing cached.
 *
 * A worse card, and an honest one. These are the curated destinations without
 * prices attached — still useful as a starting point, and each one runs a real
 * search when clicked.
 */
/**
 * Last resort: the catalogue itself failed to load.
 *
 * Shaped as `Destination` so `ColdRail` has one code path. The missing fields
 * are what the catalogue would have supplied, and each renders its own absence
 * rather than needing a branch.
 */
const FALLBACK: Destination[] = (
  [
    ["Yogyakarta", "Indonesia", "YIA"],
    ["Bali", "Indonesia", "DPS"],
    ["Lombok", "Indonesia", "LOP"],
    ["Kuala Lumpur", "Malaysia", "KUL"],
    ["Bangkok", "Thailand", "BKK"],
    ["Tokyo", "Japan", "HND"],
  ] as const
).map(([name, country, iata]) => ({
  name,
  country,
  iata,
  region: "",
  description: "",
  budget_category: "",
  travel_types: [],
  best_season: "",
  estimated_daily_cost_idr: {},
  estimated_daily_total_idr: null,
  highlights: [],
  why_budget_friendly: "",
}));

/**
 * The rail before any fare has been cached.
 *
 * It used to render six hardcoded city names, each card saying "harga belum
 * tersimpan" and nothing else — eight identical dead tiles, which is why the
 * section read as pointless. The fare is genuinely unknown until someone asks
 * for it, but the fare was never the only thing worth showing: the catalogue
 * already knows what each place costs per day, what kind of trip it is, and one
 * concrete reason to go, none of which needs a provider call.
 *
 * So the cold state now carries more information than a price would, not less.
 */
function ColdRail({
  destinations,
  typeLabels,
  onPick,
}: {
  destinations: Destination[];
  /** facet value → translated label, from the catalogue. */
  typeLabels: Record<string, string>;
  onPick: (city: string, iata: string, date: string) => void;
}) {
  const date = isoDateIn(30);
  const { m, t } = useMessages();

  // Catalogue unreachable as well as the cache being cold. Rare, and the page
  // above it is already degraded, so this stays minimal rather than clever.
  const places = destinations.length ? destinations : FALLBACK;

  return (
    <>
      {places.map((place) => {
        const type = place.travel_types?.[0];
        const daily = place.estimated_daily_total_idr;

        return (
          <button
            key={place.iata ?? place.name}
            type="button"
            onClick={() => onPick(place.name, place.iata ?? "", date)}
            className="lift pressable flex h-auto w-56 shrink-0 snap-start flex-col items-start gap-2 rounded-card border border-border bg-surface p-4 text-left"
          >
            {type && <TravelTypeMark value={type} label={typeLabels[type] ?? type} />}

            <div className="min-w-0 self-stretch">
              <p className="truncate font-medium">{place.name}</p>
              <p className="truncate text-xs text-fg-muted">{place.country}</p>
            </div>

            {daily ? (
              <p className="text-2xs text-fg-muted">
                {t(m.deals.dailyThere, { amount: rupiah(daily) })}
              </p>
            ) : (
              <p className="text-2xs text-fg-subtle">{m.deals.noPriceYet}</p>
            )}

            <span className="mt-1 inline-flex items-center gap-1 text-xs font-medium text-accent">
              {m.deals.checkPriceNow}
              <ArrowRight className="size-3" aria-hidden />
            </span>
          </button>
        );
      })}
    </>
  );
}

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
import type { DealsResponse, ToolSeed } from "@/lib/types";
import type { Submission } from "./FlightSearchForm";

export function DealRail({
  deals,
  originLabel,
  onRun,
}: {
  deals: DealsResponse;
  originLabel: string;
  onRun: (submission: Submission) => void;
}) {
  const cold = !deals.updated_at || deals.deals.length === 0;
  const age = staleness(deals.updated_at);

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
      message: `Cari penerbangan ${originLabel} ke ${city} tanggal ${shortDate(date)}`,
      seed,
    });
  };

  return (
    <section className="border-t border-border py-12">
      <div className="mx-auto max-w-6xl px-5">
        <header className="mb-5 flex flex-wrap items-end justify-between gap-3">
          <div>
            <h2 className="text-xl font-semibold tracking-tight">
              Berangkat dari {originLabel}
            </h2>
            <p className="mt-1 text-sm text-fg-muted">
              {cold
                ? "Harga belum tersimpan untuk kota ini — klik buat cari langsung."
                : `Harga mulai untuk ${deals.departure_date ? shortDate(deals.departure_date) : "sebulan ke depan"}.`}
            </p>
          </div>
          {age && (
            <p className="text-xs text-fg-subtle">
              Diperbarui {age}
            </p>
          )}
        </header>

        {deals.requested_origin && deals.requested_origin !== deals.origin && (
          <p className="mb-4 rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm text-fg-muted">
            Kami belum nyimpen harga dari {deals.requested_origin}, jadi yang tampil dari{" "}
            {originLabel}.
          </p>
        )}

        <div className="no-scrollbar -mx-5 flex snap-x snap-mandatory gap-3 overflow-x-auto px-5 pb-1">
          {cold ? (
            <ColdRail onPick={search} />
          ) : (
            deals.deals.map((deal) => (
              <button
                key={deal.iata}
                type="button"
                onClick={() =>
                  search(deal.city, deal.iata, deals.departure_date ?? isoDateIn(30))
                }
                className={cn(
                  "group w-52 shrink-0 snap-start rounded-card border border-border bg-surface p-4 text-left",
                  "transition-[border-color,box-shadow] hover:border-border-strong hover:shadow-card",
                )}
              >
                <p className="font-medium">{deal.city}</p>
                <p className="text-xs text-fg-muted">{deal.country}</p>

                <p className="tabular mt-4 font-mono text-lg font-semibold text-price">
                  {rupiah(deal.price_idr)}
                </p>
                <p className="text-2xs text-fg-muted">
                  {deal.airline ?? "sekali jalan"} · {deal.stops === 0 ? "langsung" : `${deal.stops} transit`}
                </p>

                {deal.daily_cost_idr ? (
                  <p className="tabular mt-2 border-t border-border pt-2 text-2xs text-fg-muted">
                    Di sana ~{rupiah(deal.daily_cost_idr)}/hari
                  </p>
                ) : null}

                <span className="mt-3 inline-flex items-center gap-1 text-xs font-medium text-accent">
                  Cek penerbangan
                  <ArrowRight
                    className="size-3 transition-transform group-hover:translate-x-0.5"
                    aria-hidden
                  />
                </span>
              </button>
            ))
          )}
        </div>
      </div>
    </section>
  );
}

/**
 * What the rail looks like with nothing cached.
 *
 * A worse card, and an honest one. These are the curated destinations without
 * prices attached — still useful as a starting point, and each one runs a real
 * search when clicked.
 */
const FALLBACK = [
  { city: "Yogyakarta", iata: "YIA" },
  { city: "Bali", iata: "DPS" },
  { city: "Lombok", iata: "LOP" },
  { city: "Kuala Lumpur", iata: "KUL" },
  { city: "Bangkok", iata: "BKK" },
  { city: "Tokyo", iata: "HND" },
];

function ColdRail({ onPick }: { onPick: (city: string, iata: string, date: string) => void }) {
  const date = isoDateIn(30);
  return (
    <>
      {FALLBACK.map((place) => (
        <button
          key={place.iata}
          type="button"
          onClick={() => onPick(place.city, place.iata, date)}
          className="w-52 shrink-0 snap-start rounded-card border border-dashed border-border bg-surface p-4 text-left transition-colors hover:border-border-strong"
        >
          <p className="font-medium">{place.city}</p>
          <p className="font-mono text-xs text-fg-muted">{place.iata}</p>
          <p className="mt-4 text-sm text-fg-subtle">Harga belum tersimpan</p>
          <span className="mt-3 inline-flex items-center gap-1 text-xs font-medium text-accent">
            Cek harga sekarang
            <ArrowRight className="size-3" aria-hidden />
          </span>
        </button>
      ))}
    </>
  );
}

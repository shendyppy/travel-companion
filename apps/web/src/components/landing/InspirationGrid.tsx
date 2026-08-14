"use client";

/**
 * "Mau liburan yang kayak gimana?"
 *
 * Structurally this is the category row every OTA has. The difference is what a
 * tile does: Traveloka's categories are landing pages for SEO terms, these run a
 * live `recommend_destinations` query against curated data and stream an answer
 * into the hero.
 *
 * The tiles are built from the `TravelType` enum served by `/api/destinations`,
 * not from a hardcoded list, so adding a travel type in Python adds a tile here.
 *
 * Sizing note: labels are Indonesian and vary a lot — "Kota" against
 * "Petualangan". The grid is sized to the longest, not the average, because a
 * tile that wraps to two lines in a row of one-liners looks broken.
 */

import { rupiahShort } from "@/lib/format";
import type { BudgetBand, FacetOption, ToolSeed } from "@/lib/types";
import type { Submission } from "./FlightSearchForm";

const EMOJI: Record<string, string> = {
  beach: "🏖️",
  mountain: "⛰️",
  cultural: "🏛️",
  city: "🌃",
  adventure: "🧗",
  nature: "🌿",
  foodie: "🍜",
  shopping: "🛍️",
};

export function InspirationGrid({
  travelTypes,
  budgetBands,
  onRun,
}: {
  travelTypes: FacetOption[];
  budgetBands: BudgetBand[];
  onRun: (submission: Submission) => void;
}) {
  const byType = (type: FacetOption) => {
    const seed: ToolSeed = {
      tool: "recommend_destinations",
      arguments: { travel_types: [type.value] },
    };
    onRun({
      message: `Kasih rekomendasi destinasi yang ${type.label.toLowerCase()} dong`,
      seed,
    });
  };

  const byBudget = (band: BudgetBand) => {
    const seed: ToolSeed = {
      tool: "recommend_destinations",
      arguments: { budget: band.value },
    };
    const ceiling = band.max_idr ? `di bawah ${rupiahShort(band.max_idr)}` : "bebas";
    onRun({
      message: `Ke mana ya yang budget-nya ${ceiling} per hari?`,
      seed,
    });
  };

  return (
    <section className="border-t border-border py-12">
      <div className="mx-auto max-w-6xl px-5">
        <h2 className="text-xl font-semibold tracking-tight">Mau liburan yang kayak gimana?</h2>
        <p className="mt-1 text-sm text-fg-muted">
          Pilih satu, langsung dicariin — bukan halaman kategori, tapi jawaban beneran.
        </p>

        <ul className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
          {travelTypes.map((type) => (
            <li key={type.value}>
              <button
                type="button"
                onClick={() => byType(type)}
                className="flex h-full w-full flex-col items-start gap-2 rounded-card border border-border bg-surface p-4 text-left transition-[border-color,background-color] hover:border-border-strong hover:bg-surface-2"
              >
                <span className="text-2xl leading-none" aria-hidden>
                  {EMOJI[type.value] ?? "✈️"}
                </span>
                <span className="text-sm font-medium">{type.label}</span>
              </button>
            </li>
          ))}
        </ul>

        {/* Budget picker. Indonesian travellers lead with a number far more
            often than with a destination, and no OTA lets them start there. */}
        <div className="mt-10">
          <h3 className="text-xl font-semibold tracking-tight">Budget kamu berapa sehari?</h3>
          <p className="mt-1 text-sm text-fg-muted">
            Angka di sini termasuk makan, transport lokal, dan penginapan.
          </p>

          <ul className="mt-5 grid gap-3 sm:grid-cols-4">
            {budgetBands.map((band) => (
              <li key={band.value}>
                <button
                  type="button"
                  onClick={() => byBudget(band)}
                  className="flex h-full w-full flex-col items-start gap-1 rounded-card border border-border bg-surface p-4 text-left transition-[border-color,background-color] hover:border-border-strong hover:bg-surface-2"
                >
                  <span className="text-sm font-medium">{band.label}</span>
                  <span className="tabular font-mono text-lg font-semibold text-price">
                    {band.range_label}
                  </span>
                  <span className="text-2xs text-fg-muted">per hari</span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}

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

import { cn } from "@/lib/utils";
import { rupiahShort } from "@/lib/format";
import { Price } from "@/components/molecules/Price";
import { Section } from "@/components/molecules/Section";
import { categoryStyle } from "@/components/molecules/TravelTypeMark";
import { CompassScene } from "@/components/illustration/Scenes";
import { useMessages } from "@/components/i18n/MessagesProvider";
import type { BudgetBand, FacetOption, ToolSeed } from "@/lib/types";
import type { Submission } from "@/components/organisms/FlightSearchForm";

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

/**
 * The per-type hues now live in `molecules/TravelTypeMark`, so the fare rail can
 * label a destination with the same colour this grid uses for its tiles.
 */

export function InspirationGrid({
  travelTypes,
  budgetBands,
  onRun,
}: {
  travelTypes: FacetOption[];
  budgetBands: BudgetBand[];
  onRun: (submission: Submission) => void;
}) {
  const { m, t } = useMessages();

  const byType = (type: FacetOption) => {
    const seed: ToolSeed = {
      tool: "recommend_destinations",
      arguments: { travel_types: [type.value] },
    };
    onRun({
      message: t(m.inspiration.messageType, { label: type.label.toLowerCase() }),
      seed,
    });
  };

  const byBudget = (band: BudgetBand) => {
    const seed: ToolSeed = {
      tool: "recommend_destinations",
      arguments: { budget: band.value },
    };
    const ceiling = band.max_idr
      ? t(m.inspiration.ceilingUnder, { amount: rupiahShort(band.max_idr) })
      : m.inspiration.ceilingAny;
    onRun({
      message: t(m.inspiration.messageBudget, { ceiling }),
      seed,
    });
  };

  return (
    <Section
      id="inspirasi"
      tourId="inspiration"
      eyebrow={m.inspiration.eyebrow}
      title={m.inspiration.title}
      lead={m.inspiration.lead}
      illustration={<CompassScene className="size-24" />}
    >
      <ul className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {travelTypes.map((type) => {
          const style = categoryStyle(type.value);
          return (
            <li key={type.value}>
              <button
                type="button"
                onClick={() => byType(type)}
                className="group lift pressable flex h-full w-full flex-col items-start gap-2.5 rounded-card border border-border bg-surface p-4 text-left"
              >
                <span
                  className={cn(
                    "grid size-10 place-items-center rounded-lg text-xl leading-none transition-transform duration-[--duration-fast] group-hover:scale-105",
                    style.tint,
                  )}
                  aria-hidden
                >
                  {EMOJI[type.value] ?? "✈️"}
                </span>
                <span className={cn("text-sm font-medium", style.mark)}>{type.label}</span>
              </button>
            </li>
          );
        })}
      </ul>

      {/* Budget picker. Indonesian travellers lead with a number far more
          often than with a destination, and no OTA lets them start there. */}
      <div className="mt-10">
        <h3 className="text-lg font-semibold tracking-tight">{m.inspiration.budgetTitle}</h3>
        <p className="mt-1 text-sm text-fg-muted">{m.inspiration.budgetLead}</p>

        <ul className="mt-4 grid gap-3 sm:grid-cols-4">
          {budgetBands.map((band) => (
            <li key={band.value}>
              <button
                type="button"
                onClick={() => byBudget(band)}
                className="lift pressable flex h-full w-full flex-col items-start gap-1 rounded-card border border-border bg-surface p-4 text-left"
              >
                <span className="text-sm font-medium">{band.label}</span>
                <Price size="lg">{band.range_label}</Price>
                <span className="text-2xs text-fg-muted">{m.inspiration.perDay}</span>
              </button>
            </li>
          ))}
        </ul>
      </div>
    </Section>
  );
}

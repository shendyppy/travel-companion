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
import { Section } from "./Section";
import { CompassScene } from "@/components/illustration/Scenes";
import { useMessages } from "@/components/i18n/MessagesProvider";
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

/**
 * One hue per travel type.
 *
 * All eight sit at identical lightness and chroma in `globals.css` — only the
 * hue moves. That is what stops this reading as a pile of stickers: nothing is
 * louder than anything else, which is honest, because no travel type is more
 * important than another. Colour here is a label, not a ranking.
 *
 * Written as full class strings because Tailwind scans source text; a template
 * literal like `bg-cat-${value}-soft` produces no CSS at all.
 */
const CATEGORY_STYLE: Record<string, { tint: string; mark: string }> = {
  beach: { tint: "bg-cat-beach-soft", mark: "text-cat-beach" },
  mountain: { tint: "bg-cat-mountain-soft", mark: "text-cat-mountain" },
  cultural: { tint: "bg-cat-cultural-soft", mark: "text-cat-cultural" },
  city: { tint: "bg-cat-city-soft", mark: "text-cat-city" },
  adventure: { tint: "bg-cat-adventure-soft", mark: "text-cat-adventure" },
  nature: { tint: "bg-cat-nature-soft", mark: "text-cat-nature" },
  foodie: { tint: "bg-cat-foodie-soft", mark: "text-cat-foodie" },
  shopping: { tint: "bg-cat-shopping-soft", mark: "text-cat-shopping" },
};

const NEUTRAL_STYLE = { tint: "bg-surface-2", mark: "text-fg-muted" };

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
          const style = CATEGORY_STYLE[type.value] ?? NEUTRAL_STYLE;
          return (
            <li key={type.value}>
              <button
                type="button"
                onClick={() => byType(type)}
                className="group flex h-full w-full flex-col items-start gap-2.5 rounded-card border border-border bg-surface p-4 text-left transition-[border-color,box-shadow,transform] duration-[--duration-fast] hover:-translate-y-0.5 hover:border-border-strong hover:shadow-card"
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
                className="flex h-full w-full flex-col items-start gap-1 rounded-card border border-border bg-surface p-4 text-left transition-[border-color,box-shadow,transform] duration-[--duration-fast] hover:-translate-y-0.5 hover:border-border-strong hover:shadow-card"
              >
                <span className="text-sm font-medium">{band.label}</span>
                <span className="tabular font-mono text-lg font-semibold text-price">
                  {band.range_label}
                </span>
                <span className="text-2xs text-fg-muted">{m.inspiration.perDay}</span>
              </button>
            </li>
          ))}
        </ul>
      </div>
    </Section>
  );
}

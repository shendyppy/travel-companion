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
import { TravelTypeScene } from "@/components/illustration/TravelTypes";
import { useCarousel } from "@/hooks/useCarousel";
import { useMessages } from "@/components/i18n/MessagesProvider";
import type { BudgetBand, FacetOption, ToolSeed } from "@/lib/types";
import type { Submission } from "@/components/organisms/FlightSearchForm";

/**
 * The eight tiles used to be emoji, which rendered differently on every platform,
 * could not take a brand colour, and were the clearest possible signal that
 * nobody had drawn anything. They are `TravelTypeScene` drawings now.
 *
 * The per-type hues live in `molecules/TravelTypeMark`, so the fare rail can
 * label a destination with the same colour this section uses for its tiles.
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
  const carousel = useCarousel(travelTypes.length);
  const active = travelTypes[carousel.index];
  const activeStyle = categoryStyle(active?.value);

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
      full
    >
      <div
        ref={carousel.ref}
        className="grid items-center gap-8 lg:grid-cols-[1.1fr_1fr] lg:gap-14"
        onPointerEnter={() => carousel.take()}
        onFocusCapture={() => carousel.take()}
      >
        {/* The stage. One type at a time, big enough to actually look at — the
            eight tiles all competing at 40px each was the version that read as a
            settings screen rather than an invitation. */}
        <div
          className={cn(
            "relative flex aspect-[4/3] items-center justify-center overflow-hidden rounded-panel transition-colors duration-[--duration-slow] sm:aspect-[16/10]",
            activeStyle.tint,
          )}
        >
          {travelTypes.map((type, i) => (
            <TravelTypeScene
              key={type.value}
              type={type.value}
              className={cn(
                "absolute w-3/5 max-w-sm transition-all duration-[--duration-slow] ease-[--ease-out]",
                categoryStyle(type.value).mark,
                i === carousel.index
                  ? "translate-x-0 opacity-100"
                  : i < carousel.index
                    ? "-translate-x-6 opacity-0"
                    : "translate-x-6 opacity-0",
              )}
            />
          ))}

          <p
            className={cn(
              "display absolute bottom-5 left-6 text-2xl sm:text-3xl",
              activeStyle.mark,
            )}
          >
            {active?.label}
          </p>
        </div>

        <ul className="grid grid-cols-2 gap-2 sm:grid-cols-4 lg:grid-cols-2">
          {travelTypes.map((type, i) => {
            const style = categoryStyle(type.value);
            const on = i === carousel.index;
            return (
              <li key={type.value}>
                <button
                  type="button"
                  onClick={() => byType(type)}
                  onPointerEnter={() => carousel.take(i)}
                  onFocus={() => carousel.take(i)}
                  aria-current={on}
                  className={cn(
                    "pressable flex h-full w-full items-center gap-2.5 rounded-card border p-3 text-left transition-[border-color,background-color] duration-[--duration-normal]",
                    on ? "border-current bg-surface" : "border-border bg-surface hover:border-border-strong",
                    on ? style.mark : "text-fg",
                  )}
                >
                  <span
                    className={cn("grid size-9 shrink-0 place-items-center rounded-lg", style.tint)}
                    aria-hidden
                  >
                    <TravelTypeScene type={type.value} className={cn("size-6", style.mark)} />
                  </span>
                  <span className="text-sm font-medium">{type.label}</span>
                </button>
              </li>
            );
          })}
        </ul>
      </div>

      {/* Budget picker. Indonesian travellers lead with a number far more
          often than with a destination, and no OTA lets them start there.
          Kept small and secondary: it answers a different question from the one
          the stage above is asking, and giving it equal weight made the section
          read as two unrelated things stacked. */}
      <div className="mt-12 border-t border-border pt-8">
        <div className="flex flex-wrap items-end justify-between gap-x-6 gap-y-1">
          <h3 className="text-lg font-semibold tracking-[--tracking-heading]">
            {m.inspiration.budgetTitle}
          </h3>
          <p className="text-sm text-fg-muted">{m.inspiration.budgetLead}</p>
        </div>

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

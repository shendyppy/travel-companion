"use client";

/**
 * What actually happens, shown rather than described.
 *
 * This replaces the three capability cards and the "cara kerjanya" stack table
 * that used to sit here. Both told the visitor things; neither showed them
 * anything, and a page about a product that *does* something should demonstrate
 * rather than assert.
 *
 * Built from markup, not a video or a GIF. Three reasons, in order of how much
 * they matter: it stays sharp at any density, it costs kilobytes instead of
 * megabytes on the mobile connections most of this audience is on, and it cannot
 * silently go stale — it uses the same tokens as the real UI, so a change to the
 * design system moves this too.
 *
 * **The reader drives it.** It used to advance itself every 3.8 seconds, and a
 * timer is the wrong mechanism for a sequence someone is reading: it moved while
 * you were still on step two, then moved again while you were looking for where
 * step two went. Now the step is a function of scroll position — the panel
 * sticks, the track scrolls behind it, and the demo only ever advances because
 * someone asked. It runs backwards just as willingly, which a carousel never
 * does.
 *
 * Every step is still a real button. Clicking one scrolls to its segment rather
 * than setting state directly, because with scroll as the source of truth,
 * state set any other way is undone by the very next scroll event.
 *
 * One non-obvious dependency: the sticky panel only works because `useInView`
 * fires once and disconnects, leaving `reveal` at `transform: none`. A non-none
 * transform on an ancestor becomes the containing block for its descendants and
 * silently kills `position: sticky` — so if `reveal` is ever changed to
 * re-trigger on scroll, this section stops sticking and nothing will say why.
 */

import { CalendarCheck, Filter, MessageCircle, Search } from "lucide-react";
import { cn } from "@/lib/utils";
import { Section } from "@/components/molecules/Section";
import { Price } from "@/components/molecules/Price";
import { AirlineMark } from "@/components/molecules/AirlineMark";
import { Skeleton } from "@/components/ui/skeleton";
import { PlanScene } from "@/components/illustration/Scenes";
import { useMessages } from "@/components/i18n/MessagesProvider";
import { useScrollSteps } from "@/hooks/useScrollSteps";
import type { Messages } from "@/lib/i18n";

const STEP_ICONS = [Search, Filter, MessageCircle, CalendarCheck] as const;

/**
 * Scroll distance per step, in viewport heights.
 *
 * Tuned by feel rather than derived: much below this and a normal wheel flick
 * skips a step entirely; much above and the section overstays its welcome on a
 * page people are scrolling to reach prices.
 */
const VH_PER_STEP = 62;

function steps(m: Messages) {
  return [
    { title: m.demo.step1Title, body: m.demo.step1Body },
    { title: m.demo.step2Title, body: m.demo.step2Body },
    { title: m.demo.step3Title, body: m.demo.step3Body },
    { title: m.demo.step4Title, body: m.demo.step4Body },
  ];
}

export function DemoSection() {
  const { m } = useMessages();
  const STEPS = steps(m);
  const { ref, index: step, scrollTo } = useScrollSteps<HTMLDivElement>(STEPS.length);

  return (
    <Section
      eyebrow={m.demo.eyebrow}
      title={m.demo.title}
      lead={m.demo.lead}
      illustration={<PlanScene className="size-24" />}
    >
      {/* The track. Its only job is to be tall — that height is the scrub
          distance. Everything visible lives in the sticky child. */}
      <div ref={ref} style={{ height: `${STEPS.length * VH_PER_STEP}dvh` }}>
        {/* The sticky child fills the viewport and centres its content. Left at
            its natural height it pinned near the top and left most of a screen
            empty underneath for the whole length of the track — the panel was
            fine, the hole below it was the problem. */}
        <div className="sticky top-14 flex min-h-[calc(100dvh-3.5rem)] items-center">
          <div className="grid w-full gap-6 lg:grid-cols-[1fr_1.15fr] lg:items-center lg:gap-10">
          <ol className="grid gap-2">
            {STEPS.map((item, i) => {
              const active = i === step;
              const Icon = STEP_ICONS[i];
              return (
                <li key={item.title}>
                  <button
                    type="button"
                    onClick={() => scrollTo(i)}
                    aria-current={active}
                    className={cn(
                      "pressable relative flex w-full gap-3 overflow-hidden rounded-card border p-3.5 text-left",
                      "transition-[border-color,background-color] duration-[--duration-normal]",
                      active
                        ? "border-accent bg-accent-soft"
                        : "border-border bg-surface hover:border-border-strong",
                    )}
                  >
                    {/* A rule down the left edge that fills on the active step.
                        Scroll-driven sequences need somewhere for the eye to
                        register "this one", and a border colour alone is too
                        quiet once four cards are stacked. */}
                    <span
                      className={cn(
                        "absolute inset-y-0 left-0 w-0.5 origin-top bg-accent transition-transform duration-[--duration-slow] ease-[--ease-out]",
                        active ? "scale-y-100" : "scale-y-0",
                      )}
                      aria-hidden
                    />
                    <span
                      className={cn(
                        "grid size-8 shrink-0 place-items-center rounded-lg transition-colors duration-[--duration-normal]",
                        active ? "bg-accent text-accent-fg" : "bg-surface-2 text-fg-muted",
                      )}
                      aria-hidden
                    >
                      <Icon className="size-4" />
                    </span>
                    <span className="min-w-0">
                      <span className="block text-sm font-medium">{item.title}</span>
                      <span
                        className={cn(
                          "mt-1 block text-sm text-fg-muted",
                          // Collapsed when inactive so four steps fit without
                          // becoming a wall of text.
                          active ? "" : "hidden sm:line-clamp-1",
                        )}
                      >
                        {item.body}
                      </span>
                    </span>
                  </button>
                </li>
              );
            })}
          </ol>

          <div className="overflow-hidden rounded-panel border border-border bg-surface-2 p-4 shadow-card sm:p-6">
              <Stage step={step} label={STEPS[step].title} />
            </div>
          </div>
        </div>
      </div>
    </Section>
  );
}

/** The little pretend product. Same tokens as the real thing, one tenth the code. */
function Stage({ step, label }: { step: number; label: string }) {
  const { m } = useMessages();

  return (
    // The height is fixed rather than min-, and generously: the four steps hold
    // different amounts of content, and letting the panel resize under a sticky
    // layout means the page shifts while you scroll it. Step 0 used to be a
    // single line of text in a 256px box, which is what made the section read as
    // empty — it is now the same shape as the steps after it.
    <div className="grid h-[26rem] content-start gap-2.5 sm:h-[24rem]" role="img" aria-label={label}>
      <MockBar step={step} />

      {step === 0 && (
        <div className="animate-fade grid gap-2.5">
          <p className="px-1 pt-2 text-sm text-fg-muted">{m.demo.mockQuery}</p>

          {/* What the wait actually looks like. Skeletons rather than a spinner,
              and shaped like the rows that replace them, so the transition into
              step 1 is the placeholder filling in rather than one thing being
              swapped for another. */}
          {[0, 1, 2].map((row) => (
            <div
              key={row}
              className="flex items-center gap-3 rounded-card border border-border bg-surface px-3 py-2.5"
              style={{ opacity: 1 - row * 0.22 }}
            >
              <Skeleton className="size-7 shrink-0 rounded-md" />
              <Skeleton className="h-3.5 w-10" />
              <span className="h-px flex-1 bg-border" />
              <Skeleton className="h-3.5 w-20" />
            </div>
          ))}
        </div>
      )}

      {step >= 1 && (
        <div className="grid gap-2">
          {MOCK_FLIGHTS.map((flight, index) => {
            // Step 2 is the filter landing: the row that does not match fades
            // back rather than vanishing, so the effect of the filter is legible.
            const dimmed = step >= 2 && !flight.keep;
            return (
              <div
                key={flight.code}
                className={cn(
                  "animate-rise flex items-center gap-3 rounded-card border bg-surface px-3 py-2.5",
                  dimmed ? "border-border opacity-35" : "border-border",
                  step >= 2 && flight.cheapest && "border-accent",
                )}
                style={{ animationDelay: `${index * 70}ms` }}
              >
                <AirlineMark code={flight.code} className="size-7" />
                <span className="tabular text-sm font-medium">{flight.time}</span>
                <span className="h-px flex-1 bg-border" />
                <Price size="sm">{flight.price}</Price>
              </div>
            );
          })}
        </div>
      )}

      {step === 3 && (
        <div className="animate-rise mt-1 grid gap-2">
          <p className="ml-auto max-w-[85%] rounded-bubble bg-accent px-3.5 py-2 text-sm text-accent-fg">
            {m.demo.mockAsk}
          </p>
          <p className="max-w-[85%] rounded-bubble border border-border bg-surface px-3.5 py-2 text-sm">
            {m.demo.mockReply}
          </p>
          <span className="mt-1 inline-flex w-fit items-center gap-1.5 rounded-pill bg-warm-tint px-3 py-1 text-xs font-medium text-warm">
            <CalendarCheck className="size-3.5" aria-hidden />
            {m.demo.mockCalendar}
          </span>
        </div>
      )}
    </div>
  );
}

const MOCK_FLIGHTS = [
  { code: "GA", time: "06:10", price: "Rp 1.310.000", keep: true, cheapest: true },
  { code: "JT", time: "13:40", price: "Rp 1.415.000", keep: false, cheapest: false },
  { code: "QG", time: "08:25", price: "Rp 1.590.000", keep: true, cheapest: false },
] as const;

function MockBar({ step }: { step: number }) {
  const { m } = useMessages();
  return (
    <div className="flex items-center gap-2 rounded-lg border border-border bg-surface px-3 py-2">
      <Search className="size-3.5 shrink-0 text-fg-subtle" aria-hidden />
      <span className="min-w-0 flex-1 truncate text-sm">
        {step === 0 ? (
          <>
            Jakarta → Bali
            <span className="animate-caret ml-0.5 inline-block h-4 w-px translate-y-0.5 bg-accent" />
          </>
        ) : (
          <span className="text-fg-muted">{m.demo.mockSearch}</span>
        )}
      </span>
      {step >= 2 && (
        <span className="hidden shrink-0 items-center gap-1 rounded-pill bg-accent-soft px-2 py-0.5 text-2xs font-medium text-accent sm:inline-flex">
          <Filter className="size-3" aria-hidden />
          {m.demo.mockFilter}
        </span>
      )}
    </div>
  );
}

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
 * Motion rules it obeys:
 *   - stops when scrolled out of view, so it is not burning battery in a
 *     background tab or below the fold
 *   - stops entirely under `prefers-reduced-motion`, which turns it into a
 *     plain, clickable set of steps
 *   - every step is a real button, so the animation is a convenience and never
 *     the only way to see a step
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { CalendarCheck, Filter, MessageCircle, Search } from "lucide-react";
import { cn } from "@/lib/utils";
import { Section } from "./Section";
import { PlanScene } from "@/components/illustration/Scenes";
import { useMessages } from "@/components/i18n/MessagesProvider";
import type { Messages } from "@/lib/i18n";

const STEP_MS = 3800;

const STEP_ICONS = [Search, Filter, MessageCircle, CalendarCheck] as const;

function steps(m: Messages) {
  return [
    { title: m.demo.step1Title, body: m.demo.step1Body },
    { title: m.demo.step2Title, body: m.demo.step2Body },
    { title: m.demo.step3Title, body: m.demo.step3Body },
    { title: m.demo.step4Title, body: m.demo.step4Body },
  ];
}

export function DemoSection() {
  const [step, setStep] = useState(0);
  const [playing, setPlaying] = useState(false);
  const stageRef = useRef<HTMLDivElement>(null);
  const { m } = useMessages();
  const STEPS = steps(m);

  // Only runs while the section is actually on screen. An animation ticking
  // away under the fold is pure waste on a phone.
  useEffect(() => {
    const node = stageRef.current;
    if (!node) return;

    if (window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) return;
    if (typeof IntersectionObserver === "undefined") return;

    const observer = new IntersectionObserver(
      ([entry]) => setPlaying(entry.isIntersecting),
      { threshold: 0.35 },
    );
    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (!playing) return;
    const timer = setInterval(() => setStep((s) => (s + 1) % STEP_ICONS.length), STEP_MS);
    return () => clearInterval(timer);
  }, [playing]);

  // A click is a deliberate choice, so it stops the carousel moving on its own.
  // Nothing is more irritating than an auto-advance that fights the reader.
  const pick = useCallback((index: number) => {
    setStep(index);
    setPlaying(false);
  }, []);

  return (
    <Section
      eyebrow={m.demo.eyebrow}
      title={m.demo.title}
      lead={m.demo.lead}
      illustration={<PlanScene className="size-24" />}
    >
      <div className="grid gap-6 lg:grid-cols-[1fr_1.15fr] lg:items-start lg:gap-10">
        <ol className="grid gap-2">
          {STEPS.map((item, index) => {
            const active = index === step;
            const Icon = STEP_ICONS[index];
            return (
              <li key={item.title}>
                <button
                  type="button"
                  onClick={() => pick(index)}
                  aria-current={active}
                  className={cn(
                    "flex w-full gap-3 rounded-card border p-3.5 text-left",
                    "transition-[border-color,background-color] duration-[--duration-fast]",
                    active
                      ? "border-accent bg-accent-soft"
                      : "border-border bg-surface hover:border-border-strong",
                  )}
                >
                  <span
                    className={cn(
                      "grid size-8 shrink-0 place-items-center rounded-lg",
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

        <div
          ref={stageRef}
          className="overflow-hidden rounded-panel border border-border bg-surface-2 p-4 shadow-card sm:p-6"
        >
          <Stage step={step} label={STEPS[step].title} />
        </div>
      </div>
    </Section>
  );
}

/** The little pretend product. Same tokens as the real thing, one tenth the code. */
function Stage({ step, label }: { step: number; label: string }) {
  const { m } = useMessages();

  return (
    <div className="grid min-h-64 gap-2.5" role="img" aria-label={label}>
      <MockBar step={step} />

      {step === 0 && (
        <p className="animate-fade px-1 pt-6 text-center text-sm text-fg-muted">
          {m.demo.mockQuery}
        </p>
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
                <span className="tabular grid size-7 shrink-0 place-items-center rounded-md bg-surface-2 font-mono text-2xs font-semibold text-fg-muted">
                  {flight.code}
                </span>
                <span className="tabular text-sm font-medium">{flight.time}</span>
                <span className="h-px flex-1 bg-border" />
                <span className="tabular font-mono text-sm font-semibold text-price">
                  {flight.price}
                </span>
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

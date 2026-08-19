"use client";

/**
 * A four-step tour for a first-time visitor.
 *
 * Tours are usually annoying, and the reasons are predictable. This one is built
 * against each of them:
 *
 *   - **Shown once, ever.** A flag in localStorage, written the moment it opens
 *     rather than when it finishes, so abandoning it counts as having seen it.
 *   - **Skippable at every step**, with Escape as well as a button.
 *   - **Never on a phone.** A spotlight overlay on a 375px screen covers the
 *     thing it is pointing at. Mobile visitors get the page instead.
 *   - **Never for someone who arrived with intent.** A `?ref=` in the URL means
 *     they followed a link to something specific; interrupting that with a
 *     product tour is the rudest possible greeting.
 *   - **Delayed a beat.** Firing during hydration means competing with the page
 *     still settling, and it feels like a popup rather than an offer.
 *
 * Targets are found by `data-tour` attribute rather than by ref, so a step whose
 * element is missing — a rail that failed to load, a section behind a flag —
 * simply gets skipped instead of pointing at nothing.
 */

import { useCallback, useEffect, useState } from "react";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";
import { useMessages } from "@/components/i18n/MessagesProvider";

const SEEN_KEY = "tc:tour-seen";
const OPEN_DELAY_MS = 900;

/** Breakpoint below which the tour never runs. Matches Tailwind's `lg`. */
const MIN_WIDTH = 1024;

interface Rect {
  top: number;
  left: number;
  width: number;
  height: number;
}

export function OnboardingTour() {
  const { m, t } = useMessages();
  const [step, setStep] = useState(0);
  const [open, setOpen] = useState(false);
  const [rect, setRect] = useState<Rect | null>(null);

  const steps = [
    { target: "command-bar", title: m.tour.step1Title, body: m.tour.step1Body },
    { target: "modes", title: m.tour.step2Title, body: m.tour.step2Body },
    { target: "inspiration", title: m.tour.step3Title, body: m.tour.step3Body },
    { target: "companion", title: m.tour.step4Title, body: m.tour.step4Body },
  ];

  const close = useCallback(() => {
    setOpen(false);
    try {
      localStorage.setItem(SEEN_KEY, "1");
    } catch {
      // Private mode, storage disabled. The tour showing twice is a far smaller
      // problem than the page throwing, so this is swallowed on purpose.
    }
  }, []);

  useEffect(() => {
    if (window.innerWidth < MIN_WIDTH) return;
    if (new URLSearchParams(window.location.search).has("ref")) return;

    try {
      if (localStorage.getItem(SEEN_KEY)) return;
    } catch {
      return; // Cannot remember having shown it ⇒ do not show it.
    }

    const timer = setTimeout(() => {
      setOpen(true);
      try {
        localStorage.setItem(SEEN_KEY, "1");
      } catch {
        /* see above */
      }
    }, OPEN_DELAY_MS);

    return () => clearTimeout(timer);
  }, []);

  // Measure on every step, and again if the window moves under us. Scrolling the
  // target into view first means a step below the fold still works.
  useEffect(() => {
    if (!open) return;

    const measure = () => {
      const node = document.querySelector(`[data-tour="${steps[step].target}"]`);
      if (!node) {
        // Nothing to point at — skip rather than render a floating box.
        setStep((s) => (s + 1 < steps.length ? s + 1 : s));
        setRect(null);
        return;
      }
      const box = node.getBoundingClientRect();
      setRect({ top: box.top, left: box.left, width: box.width, height: box.height });
    };

    const node = document.querySelector(`[data-tour="${steps[step].target}"]`);
    node?.scrollIntoView({ behavior: "smooth", block: "center" });

    // After the smooth scroll settles, not during it.
    const timer = setTimeout(measure, 380);
    window.addEventListener("resize", measure);
    return () => {
      clearTimeout(timer);
      window.removeEventListener("resize", measure);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, step]);

  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") close();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, close]);

  if (!open || !rect) return null;

  const current = steps[step];
  const last = step === steps.length - 1;

  // Below the target unless that would fall off the bottom, in which case above.
  const below = rect.top + rect.height + 190 < window.innerHeight;
  const cardTop = below ? rect.top + rect.height + 14 : rect.top - 14;

  return (
    <div className="fixed inset-0 z-[60]" role="dialog" aria-modal="true" aria-label={current.title}>
      {/* The dim and the spotlight are one element: an enormous box-shadow
          around a transparent rectangle. Cheaper than four positioned overlays
          and it animates as a single box when the step changes. */}
      <div
        onClick={close}
        className="absolute rounded-panel transition-all duration-[--duration-normal] ease-[--ease-out]"
        style={{
          top: rect.top - 8,
          left: rect.left - 8,
          width: rect.width + 16,
          height: rect.height + 16,
          boxShadow: "0 0 0 9999px oklch(17% 0.014 255 / 0.62)",
        }}
      />

      <div
        className={cn(
          "absolute w-80 rounded-panel border border-border bg-surface p-4 shadow-overlay",
          "animate-rise",
        )}
        style={{
          top: cardTop,
          left: Math.min(rect.left, window.innerWidth - 340),
          transform: below ? undefined : "translateY(-100%)",
        }}
      >
        <div className="flex items-start justify-between gap-3">
          <p className="font-medium">{current.title}</p>
          <button
            type="button"
            onClick={close}
            aria-label={m.tour.skip}
            className="-m-1 shrink-0 rounded-md p-1 text-fg-subtle hover:bg-surface-2 hover:text-fg"
          >
            <X className="size-4" aria-hidden />
          </button>
        </div>

        <p className="mt-1.5 text-sm text-fg-muted">{current.body}</p>

        <div className="mt-4 flex items-center gap-3">
          <span className="tabular text-2xs text-fg-subtle">
            {t(m.tour.step, { current: step + 1, total: steps.length })}
          </span>
          <button
            type="button"
            onClick={close}
            className="ml-auto text-sm text-fg-muted hover:text-fg"
          >
            {m.tour.skip}
          </button>
          <button
            type="button"
            onClick={() => (last ? close() : setStep((s) => s + 1))}
            className="inline-flex h-8 items-center rounded-lg bg-accent px-4 text-sm font-medium text-accent-fg"
          >
            {last ? m.tour.done : m.tour.next}
          </button>
        </div>
      </div>
    </div>
  );
}

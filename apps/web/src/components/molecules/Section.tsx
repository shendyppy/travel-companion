"use client";

/**
 * One band of the landing page.
 *
 * Exists so the page reads as a sequence rather than a stack. Every section
 * below the hero answers the question the previous one leaves you with, and each
 * gets the same furniture: an eyebrow that names the step, a heading that asks
 * the question in the reader's own words, one line of context, and an
 * illustration that stays out of the way.
 *
 * The reveal-on-scroll lives here rather than in each section, which means it is
 * consistent by construction and there is exactly one place to remove it if it
 * ever becomes annoying.
 */

import { cn } from "@/lib/utils";
import { useInView } from "@/hooks/useInView";

export function Section({
  id,
  tourId,
  eyebrow,
  title,
  lead,
  aside,
  illustration,
  children,
  className,
  full,
}: {
  id?: string;
  /** Marks this section as a stop on the onboarding tour. */
  tourId?: string;
  /** The step marker — "01", "02". Numbering makes the sequence legible at a glance. */
  eyebrow?: string;
  title: string;
  lead?: React.ReactNode;
  /** Controls that belong to the heading, like the origin picker. */
  aside?: React.ReactNode;
  illustration?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
  /**
   * Give the section a full viewport to itself, with its content vertically
   * centred in whatever is left over.
   *
   * The sections used to run straight into each other, so the page read as one
   * long scroll of loosely related blocks rather than as a sequence of answers.
   * `min-h` rather than `h`: a section with more content than fits must grow, and
   * clipping a rail because it did not agree with a round number is worse than an
   * uneven page.
   *
   * `dvh`, not `vh` — on mobile Safari `100vh` is taller than the visible area
   * while the address bar is showing, which puts the bottom of every section
   * under the browser chrome.
   */
  full?: boolean;
}) {
  const { ref, props } = useInView<HTMLElement>();

  return (
    <section
      ref={ref}
      id={id}
      data-tour={tourId}
      {...props}
      className={cn(
        "reveal border-t border-border",
        full
          ? "flex min-h-[100dvh] flex-col justify-center py-16 sm:py-20"
          : "py-16 sm:py-24",
        className,
      )}
    >
      <div className="mx-auto w-full max-w-6xl px-5">
        <header className="mb-8 flex flex-wrap items-start justify-between gap-x-6 gap-y-3 sm:mb-10">
          <div className="min-w-0 max-w-2xl">
            {eyebrow && (
              <p className="eyebrow mb-2 font-mono text-2xs font-semibold text-warm">{eyebrow}</p>
            )}
            <h2 className="display text-2xl sm:text-3xl">{title}</h2>
            {lead && (
              <p className="mt-2.5 text-pretty text-base leading-relaxed text-fg-muted">{lead}</p>
            )}
          </div>

          {aside && <div className="shrink-0">{aside}</div>}

          {illustration && (
            // Hidden below `lg` rather than shrunk. On a phone the space belongs
            // to the content; a 40px decoration is worse than none.
            <div className="hidden shrink-0 text-fg-muted lg:block" aria-hidden>
              {illustration}
            </div>
          )}
        </header>

        {children}
      </div>
    </section>
  );
}

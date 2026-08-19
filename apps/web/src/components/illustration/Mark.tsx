/**
 * The mark.
 *
 * What it replaced was a Lucide compass in a rounded blue square, which is the
 * logo every generated product has. A compass is also the wrong idea: it points
 * at a direction, and this product is about the leg between two named places and
 * the decision of which one to take.
 *
 * So the mark is the same shape as `RouteScene` in this file's neighbour — an
 * arc from an origin node to a destination node. The product's whole argument in
 * one glyph, and it means the logo and the hero illustration are visibly the
 * same drawing rather than two unrelated pieces of art.
 *
 * Two colours, both tokens: the origin takes brand, the destination takes warm.
 * That is the palette's own logic — you start in the blue and you arrive in the
 * warm one — and it recolours itself in dark mode for free.
 */

export function Mark({
  className,
  animated = false,
}: {
  className?: string;
  /**
   * Draw the arc on mount. For the one place the mark is introduced, not for
   * every header on every route — a logo that redraws itself on each navigation
   * stops reading as a logo and starts reading as a loading state.
   */
  animated?: boolean;
}) {
  return (
    <svg viewBox="0 0 32 32" fill="none" className={className} aria-hidden role="presentation">
      {/* pathLength normalises the dash animation, so the `draw` utility works
          on this curve without anyone measuring it. */}
      <path
        d="M6 23C10 9 22 9 26 19"
        pathLength={1}
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinecap="round"
        className={animated ? "draw" : undefined}
      />
      <circle cx="6" cy="23" r="3.5" fill="var(--color-accent)" />
      <circle cx="26" cy="19" r="3.5" fill="var(--color-warm)" />
    </svg>
  );
}

/**
 * The mark plus the name, for the header.
 *
 * One component rather than two elements assembled at each call site, because
 * the relationship between the glyph and the word — the gap, the optical
 * alignment, the tracking on the word — is the lockup, and a lockup that is
 * re-derived per page is one that drifts.
 */
export function Wordmark({ className, animated }: { className?: string; animated?: boolean }) {
  return (
    <span className={className}>
      <Mark className="size-7 shrink-0 text-accent" animated={animated} />
      <span className="font-semibold tracking-[--tracking-heading]">Travel Companion</span>
    </span>
  );
}

/**
 * Illustrations, drawn rather than sourced.
 *
 * The rule they all follow: geometry and tokens only. No stock photography, no
 * mascots, no gradients that mean nothing. Every stroke uses `currentColor` or a
 * theme token, so these are correct in dark mode without a second asset and
 * without anyone remembering to make one.
 *
 * They are also all inline SVG rather than files. At this size that is fewer
 * bytes than the request would cost, it survives any CDN, and it means an
 * illustration can be recoloured by its container the same way an icon is.
 *
 * Kept deliberately plain: these support a section heading, they are not the
 * point of it. Anything that pulls attention away from the prices is wrong here.
 */

interface SceneProps {
  className?: string;
}

/**
 * The hero arc, declared once.
 *
 * Used twice in `RouteScene` — as the stroke that is drawn and as the
 * `offset-path` the plane flies. Two copies of these coordinates is two chances
 * for the plane to end up flying beside the line instead of along it.
 */
const ROUTE = "M24 78C68 20 168 20 214 66";

/**
 * Hero: a route between two points over a horizon.
 *
 * The arc is the whole idea of the product in one shape — two places and the
 * decision of how to get between them.
 */
export function RouteScene({ className }: SceneProps) {
  return (
    <svg viewBox="0 0 240 120" fill="none" className={className} aria-hidden role="presentation">
      <path
        d="M8 96h224"
        stroke="var(--color-border)"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
      {[28, 62, 96, 130, 164, 198].map((x, i) => (
        <rect
          key={x}
          x={x}
          y={96 - (10 + ((i * 7) % 22))}
          width="14"
          height={10 + ((i * 7) % 22)}
          rx="2"
          fill="var(--color-surface-2)"
          stroke="var(--color-border)"
          strokeWidth="1"
        />
      ))}

      {/* The arc draws itself on load, left to right, so the first thing the
          page does is trace the journey the product is about. pathLength={1}
          lets the shared `draw` utility handle any curve without measuring. */}
      <path
        d={ROUTE}
        pathLength={1}
        className="draw"
        stroke="var(--color-accent)"
        strokeWidth="2"
        strokeLinecap="round"
      />

      {/* Origin lands first, destination a beat later — the same order the arc
          is drawn in, so the three read as one gesture instead of three. */}
      <circle cx="24" cy="78" r="5" fill="var(--color-accent)" className="pop" />
      <circle
        cx="214"
        cy="66"
        r="5"
        fill="var(--color-warm)"
        className="pop"
        style={{ animationDelay: "1.2s", transformOrigin: "214px 66px" }}
      />

      {/* Then something flies it, on the exact curve the arc was drawn from —
          `offset-path` takes the same `d`, so the plane can never drift off the
          line when the art is edited. `offset-rotate: auto` banks it into the
          turn, which is the detail that sells the whole thing. */}
      <path
        d="M-8 -5L9 0-8 5-4 0Z"
        fill="var(--color-warm)"
        className="travel"
        style={{ offsetPath: `path("${ROUTE}")` }}
      />
    </svg>
  );
}

/** Inspiration: unequal tiles, because a curated set is not a grid of sameness. */
export function CompassScene({ className }: SceneProps) {
  return (
    <svg viewBox="0 0 120 120" fill="none" className={className} aria-hidden role="presentation">
      <circle cx="60" cy="60" r="44" stroke="var(--color-border)" strokeWidth="1.5" />
      <circle cx="60" cy="60" r="30" stroke="var(--color-border)" strokeWidth="1" strokeDasharray="3 5" />
      <path d="M60 26v-8M60 102v-8M26 60h-8M102 60h8" stroke="var(--color-border-strong)" strokeWidth="1.5" strokeLinecap="round" />
      <path d="M74 46L52 54l-6 22 22-8z" fill="var(--color-accent-soft)" stroke="var(--color-accent)" strokeWidth="1.5" strokeLinejoin="round" />
      <circle cx="60" cy="60" r="3.5" fill="var(--color-warm)" />
    </svg>
  );
}

/** Deals: a price tag on a fare, with the cheapest called out. */
export function FareScene({ className }: SceneProps) {
  return (
    <svg viewBox="0 0 120 120" fill="none" className={className} aria-hidden role="presentation">
      {[0, 1, 2].map((row) => (
        <rect
          key={row}
          x="16"
          y={30 + row * 22}
          width="88"
          height="16"
          rx="4"
          fill={row === 1 ? "var(--color-accent-soft)" : "var(--color-surface-2)"}
          stroke={row === 1 ? "var(--color-accent)" : "var(--color-border)"}
          strokeWidth="1.25"
        />
      ))}
      <rect x="24" y="35" width="30" height="6" rx="3" fill="var(--color-border-strong)" />
      <rect x="24" y="57" width="38" height="6" rx="3" fill="var(--color-accent)" opacity="0.55" />
      <rect x="24" y="79" width="26" height="6" rx="3" fill="var(--color-border-strong)" />
      <path d="M84 55l6 5 6-5" stroke="var(--color-price)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

/** The artefact: a plan that leaves the app and lands in a calendar. */
export function PlanScene({ className }: SceneProps) {
  return (
    <svg viewBox="0 0 120 120" fill="none" className={className} aria-hidden role="presentation">
      <rect x="18" y="24" width="84" height="72" rx="8" fill="var(--color-surface-2)" stroke="var(--color-border)" strokeWidth="1.5" />
      <path d="M18 44h84" stroke="var(--color-border)" strokeWidth="1.5" />
      <path d="M40 24v-8M80 24v-8" stroke="var(--color-border-strong)" strokeWidth="2.5" strokeLinecap="round" />
      {[0, 1, 2].map((row) =>
        [0, 1, 2, 3].map((col) => {
          const filled = row === 1 && col === 2;
          return (
            <rect
              key={`${row}-${col}`}
              x={28 + col * 17}
              y={54 + row * 14}
              width="11"
              height="8"
              rx="2"
              fill={filled ? "var(--color-warm)" : "var(--color-border)"}
              opacity={filled ? 1 : 0.6}
            />
          );
        }),
      )}
    </svg>
  );
}

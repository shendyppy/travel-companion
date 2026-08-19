/**
 * One drawn scene per travel type.
 *
 * These replaced emoji. Emoji looked like a placeholder because they are one —
 * they render differently on every platform, they cannot take a brand colour,
 * and eight of them in a row is the single clearest tell that nobody drew
 * anything. These are the same geometric language as the landmarks and the hero
 * route, so the whole page reads as one hand.
 *
 * Everything is `currentColor`, so a tile tints its scene with the type's own
 * hue from `TravelTypeMark` and dark mode needs no second asset.
 *
 * Drawn at 120×90 because these render large — the carousel panel gives one of
 * them most of a viewport, which is a different job from the 96×64 landmarks
 * that sit on a card.
 */

interface SceneProps {
  className?: string;
}

function Frame({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <svg viewBox="0 0 120 90" fill="none" className={className} aria-hidden role="presentation">
      {children}
    </svg>
  );
}

function Beach({ className }: SceneProps) {
  return (
    <Frame className={className}>
      <circle cx="88" cy="24" r="12" fill="currentColor" opacity="0.35" />
      <path d="M6 58h108" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" opacity="0.5" />
      <path d="M6 68c8-4 16-4 24 0s16 4 24 0 16-4 24 0 16 4 24 0" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
      <path d="M6 78c8-4 16-4 24 0s16 4 24 0 16-4 24 0 16 4 24 0" stroke="currentColor" strokeWidth="2" strokeLinecap="round" opacity="0.55" />
      <path d="M32 58V34" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
      <path d="M32 34c-8-6-16-4-18 2 6-2 12 0 18 2zM32 34c8-6 16-4 18 2-6-2-12 0-18 2zM32 34c-2-9 2-15 8-16-3 5-4 11-4 16z" fill="currentColor" opacity="0.7" />
    </Frame>
  );
}

function Mountain({ className }: SceneProps) {
  return (
    <Frame className={className}>
      <path d="M4 74L36 26l20 26 14-18 42 40H4z" fill="currentColor" opacity="0.22" />
      <path d="M4 74L36 26l20 26 14-18 42 40" stroke="currentColor" strokeWidth="2.5" strokeLinejoin="round" />
      <path d="M28 38h16l-8-12z" fill="currentColor" opacity="0.75" />
      <path d="M62 42h16l-8-10z" fill="currentColor" opacity="0.55" />
      <path d="M8 82h104" stroke="currentColor" strokeWidth="2" strokeLinecap="round" opacity="0.3" />
    </Frame>
  );
}

function Cultural({ className }: SceneProps) {
  return (
    <Frame className={className}>
      <path d="M10 78h100" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
      <path d="M60 10v8" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
      <path d="M60 18l16 12H44zM60 30l22 14H38zM60 44l28 16H32z" fill="currentColor" opacity="0.3" />
      <path d="M60 18l16 12H44zM60 30l22 14H38zM60 44l28 16H32z" stroke="currentColor" strokeWidth="2.5" strokeLinejoin="round" />
      <path d="M46 60h28v18H46z" fill="currentColor" opacity="0.2" stroke="currentColor" strokeWidth="2.5" />
      <path d="M56 78V68h8v10" stroke="currentColor" strokeWidth="2" opacity="0.7" />
    </Frame>
  );
}

function City({ className }: SceneProps) {
  return (
    <Frame className={className}>
      <path d="M6 80h108" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
      <path d="M14 80V52h18v28zM38 80V34h16v46zM60 80V44h20v36zM86 80V60h18v20z" fill="currentColor" opacity="0.28" />
      <path d="M14 80V52h18v28zM38 80V34h16v46zM60 80V44h20v36zM86 80V60h18v20z" stroke="currentColor" strokeWidth="2.5" strokeLinejoin="round" />
      <path d="M46 34V24" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
      <path d="M20 60h6M20 68h6M44 44h6M44 54h6M44 64h6M66 54h8M66 64h8M92 68h6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" opacity="0.6" />
    </Frame>
  );
}

function Adventure({ className }: SceneProps) {
  return (
    <Frame className={className}>
      <path d="M4 80h112" stroke="currentColor" strokeWidth="2" strokeLinecap="round" opacity="0.35" />
      <path d="M10 80C26 62 34 46 52 40s28-14 34-26" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeDasharray="5 7" />
      <path d="M86 14v22" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
      <path d="M86 14l20 6-20 6z" fill="currentColor" />
      <path d="M34 74l10-16 10 16z" fill="currentColor" opacity="0.4" />
      <circle cx="52" cy="40" r="4.5" fill="currentColor" opacity="0.8" />
    </Frame>
  );
}

function Nature({ className }: SceneProps) {
  return (
    <Frame className={className}>
      <path d="M8 78h104" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
      <path d="M36 78V52" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
      <path d="M36 22l18 32H18zM36 38l22 26H14z" fill="currentColor" opacity="0.32" />
      <path d="M36 22l18 32H18zM36 38l22 26H14z" stroke="currentColor" strokeWidth="2.5" strokeLinejoin="round" />
      <path d="M82 78V56" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
      <circle cx="82" cy="42" r="16" fill="currentColor" opacity="0.28" />
      <circle cx="82" cy="42" r="16" stroke="currentColor" strokeWidth="2.5" />
    </Frame>
  );
}

function Foodie({ className }: SceneProps) {
  return (
    <Frame className={className}>
      <path d="M22 48h60c0 18-13 30-30 30S22 66 22 48z" fill="currentColor" opacity="0.3" />
      <path d="M22 48h60c0 18-13 30-30 30S22 66 22 48z" stroke="currentColor" strokeWidth="2.5" strokeLinejoin="round" />
      <path d="M14 80h76" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
      <path d="M40 34c0-6 6-8 6-14M56 34c0-6 6-8 6-14" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" opacity="0.6" />
      <path d="M92 26l10 4-24 26" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" opacity="0.75" />
    </Frame>
  );
}

function Shopping({ className }: SceneProps) {
  return (
    <Frame className={className}>
      <path d="M8 82h104" stroke="currentColor" strokeWidth="2" strokeLinecap="round" opacity="0.35" />
      <path d="M26 36h40l6 44H20z" fill="currentColor" opacity="0.3" />
      <path d="M26 36h40l6 44H20z" stroke="currentColor" strokeWidth="2.5" strokeLinejoin="round" />
      <path d="M36 42V30c0-6 4-10 10-10s10 4 10 10v12" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
      <path d="M76 54h24l4 26H72z" fill="currentColor" opacity="0.2" />
      <path d="M76 54h24l4 26H72z" stroke="currentColor" strokeWidth="2.5" strokeLinejoin="round" />
      <path d="M82 58v-6c0-4 3-7 6-7s6 3 6 7v6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" opacity="0.7" />
    </Frame>
  );
}

/** Anything the catalogue adds before someone draws it. */
function GenericType({ className }: SceneProps) {
  return (
    <Frame className={className}>
      <path d="M8 62h104" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" opacity="0.4" />
      <path d="M20 54C38 22 82 22 100 48" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeDasharray="5 6" />
      <circle cx="20" cy="54" r="5" fill="currentColor" />
      <circle cx="100" cy="48" r="5" fill="currentColor" opacity="0.6" />
    </Frame>
  );
}

const BY_TYPE: Record<string, (props: SceneProps) => React.ReactElement> = {
  beach: Beach,
  mountain: Mountain,
  cultural: Cultural,
  city: City,
  adventure: Adventure,
  nature: Nature,
  foodie: Foodie,
  shopping: Shopping,
};

export function TravelTypeScene({ type, className }: { type: string; className?: string }) {
  const Drawing = BY_TYPE[type] ?? GenericType;
  return <Drawing className={className} />;
}

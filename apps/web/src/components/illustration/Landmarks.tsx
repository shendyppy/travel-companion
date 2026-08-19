/**
 * One drawn landmark per destination.
 *
 * The brief bans stock photography, and that rule survives here rather than
 * being traded away for recognisability. A photograph of Borobudur would need a
 * licence, ship a few hundred kilobytes over an Indonesian mobile connection,
 * need a second treatment for dark mode, and look like every other travel site.
 * A drawn silhouette costs none of that and is the more distinctive answer, which
 * is the whole reason the illustration language exists in this project.
 *
 * Every shape uses `currentColor`. That is what lets a card tint its landmark
 * with the destination's own travel-type hue, so Lombok arrives in the beach
 * colour and Yogyakarta in the cultural one without a second set of assets.
 *
 * Deliberately simple — four to eight paths each. These render around 96px wide
 * on a card, and detail below that size turns to mud; a silhouette that reads
 * instantly beats an accurate drawing nobody can make out.
 */

interface LandmarkProps {
  className?: string;
}

/** Shared frame: wide, short, with the subject sitting on an implied ground line. */
function Frame({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <svg viewBox="0 0 96 64" fill="none" className={className} aria-hidden role="presentation">
      {children}
    </svg>
  );
}

/** Yogyakarta — Borobudur: stepped terraces under a crown of stupas. */
function Borobudur({ className }: LandmarkProps) {
  return (
    <Frame className={className}>
      <path d="M14 54h68M20 46h56M27 38h42" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" opacity="0.45" />
      <path d="M38 30h20" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" opacity="0.7" />
      <path d="M48 12c5 0 8 4 8 9H40c0-5 3-9 8-9z" fill="currentColor" />
      <circle cx="35" cy="25" r="3" fill="currentColor" opacity="0.6" />
      <circle cx="61" cy="25" r="3" fill="currentColor" opacity="0.6" />
    </Frame>
  );
}

/** Lombok — Rinjani: the caldera rim, notched, with the crater lake below. */
function Rinjani({ className }: LandmarkProps) {
  return (
    <Frame className={className}>
      <path d="M6 54L34 18l12 15 9-11 29 32H6z" fill="currentColor" opacity="0.25" />
      <path d="M6 54L34 18l12 15 9-11 29 32" stroke="currentColor" strokeWidth="2.5" strokeLinejoin="round" />
      <path d="M28 44c6-4 14-4 20 0" stroke="currentColor" strokeWidth="2" strokeLinecap="round" opacity="0.7" />
    </Frame>
  );
}

/** Belitung — the granite boulders, stacked over a waterline. */
function Belitung({ className }: LandmarkProps) {
  return (
    <Frame className={className}>
      <path d="M4 52h88" stroke="currentColor" strokeWidth="2" strokeLinecap="round" opacity="0.4" />
      <ellipse cx="36" cy="42" rx="20" ry="12" fill="currentColor" opacity="0.28" />
      <ellipse cx="34" cy="26" rx="12" ry="9" fill="currentColor" opacity="0.55" />
      <ellipse cx="66" cy="45" rx="14" ry="9" fill="currentColor" opacity="0.35" />
      <path d="M10 58c6-3 12-3 18 0s12 3 18 0 12-3 18 0 12 3 18 0" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" opacity="0.5" />
    </Frame>
  );
}

/** Bandung — tea terraces banding a hillside, a cone behind. */
function Bandung({ className }: LandmarkProps) {
  return (
    <Frame className={className}>
      <path d="M52 22L74 48H30z" fill="currentColor" opacity="0.28" />
      <path d="M4 40c14-8 30-8 44 0s30 8 44 0" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
      <path d="M4 48c14-8 30-8 44 0s30 8 44 0" stroke="currentColor" strokeWidth="2" strokeLinecap="round" opacity="0.6" />
      <path d="M4 56c14-8 30-8 44 0s30 8 44 0" stroke="currentColor" strokeWidth="2" strokeLinecap="round" opacity="0.35" />
    </Frame>
  );
}

/** Malang — Bromo: the caldera floor, the smoking cone, the rim beyond. */
function Bromo({ className }: LandmarkProps) {
  return (
    <Frame className={className}>
      <path d="M4 54h88" stroke="currentColor" strokeWidth="2" strokeLinecap="round" opacity="0.35" />
      <path d="M30 54l16-24 16 24z" fill="currentColor" opacity="0.35" />
      <path d="M30 54l16-24 16 24" stroke="currentColor" strokeWidth="2.5" strokeLinejoin="round" />
      <path d="M40 30h12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <path d="M46 24c0-4 5-4 5-9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" opacity="0.55" />
      <path d="M66 54l12-16 10 16z" fill="currentColor" opacity="0.2" />
    </Frame>
  );
}

/** Kuala Lumpur — the twin towers and their skybridge. */
function Petronas({ className }: LandmarkProps) {
  return (
    <Frame className={className}>
      <path d="M4 56h88" stroke="currentColor" strokeWidth="2" strokeLinecap="round" opacity="0.35" />
      <path d="M32 56V22l6-10 6 10v34z" fill="currentColor" opacity="0.35" />
      <path d="M52 56V22l6-10 6 10v34z" fill="currentColor" opacity="0.35" />
      <path d="M32 56V22l6-10 6 10v34M52 56V22l6-10 6 10v34" stroke="currentColor" strokeWidth="2" strokeLinejoin="round" />
      <path d="M44 34h8" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
      <path d="M38 12V6M58 12V6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" opacity="0.7" />
    </Frame>
  );
}

/** Ho Chi Minh City — the tapered tower with its heliport disc. */
function Bitexco({ className }: LandmarkProps) {
  return (
    <Frame className={className}>
      <path d="M4 56h88" stroke="currentColor" strokeWidth="2" strokeLinecap="round" opacity="0.35" />
      <path d="M38 56V16c0-4 3-6 6-6s6 2 6 6v40z" fill="currentColor" opacity="0.35" />
      <path d="M38 56V16c0-4 3-6 6-6s6 2 6 6v40" stroke="currentColor" strokeWidth="2" strokeLinejoin="round" />
      <ellipse cx="56" cy="28" rx="12" ry="3.5" fill="currentColor" opacity="0.7" />
      <path d="M60 56V40M68 56V46" stroke="currentColor" strokeWidth="2" strokeLinecap="round" opacity="0.4" />
      <path d="M24 56V38" stroke="currentColor" strokeWidth="2" strokeLinecap="round" opacity="0.4" />
    </Frame>
  );
}

/** Chiang Mai — a Lanna temple: tiered roofs narrowing to a spire. */
function LannaTemple({ className }: LandmarkProps) {
  return (
    <Frame className={className}>
      <path d="M8 56h80" stroke="currentColor" strokeWidth="2" strokeLinecap="round" opacity="0.35" />
      <path d="M48 8v6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <path d="M48 14l14 10H34zM48 24l18 12H30zM48 36l22 14H26z" fill="currentColor" opacity="0.32" />
      <path d="M48 14l14 10H34zM48 24l18 12H30zM48 36l22 14H26z" stroke="currentColor" strokeWidth="2" strokeLinejoin="round" />
    </Frame>
  );
}

/** Siem Reap — Angkor Wat: five lotus towers over a causeway. */
function AngkorWat({ className }: LandmarkProps) {
  return (
    <Frame className={className}>
      <path d="M6 54h84" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
      <path d="M48 14c4 6 6 12 6 18v12H42V32c0-6 2-12 6-18z" fill="currentColor" opacity="0.45" />
      <path d="M28 26c3 5 5 10 5 14v6H23v-6c0-4 2-9 5-14zM68 26c3 5 5 10 5 14v6H63v-6c0-4 2-9 5-14z" fill="currentColor" opacity="0.32" />
      <path d="M14 34c2 4 4 8 4 11v3h-8v-3c0-3 2-7 4-11zM82 34c2 4 4 8 4 11v3h-8v-3c0-3 2-7 4-11z" fill="currentColor" opacity="0.22" />
      <path d="M10 48h76" stroke="currentColor" strokeWidth="2" strokeLinecap="round" opacity="0.6" />
    </Frame>
  );
}

/** Penang — the clan jetties: stilt houses standing in the water. */
function ClanJetty({ className }: LandmarkProps) {
  return (
    <Frame className={className}>
      <path d="M18 34l10-8 10 8v14H18zM48 30l12-9 12 9v18H48z" fill="currentColor" opacity="0.32" />
      <path d="M18 34l10-8 10 8v14H18zM48 30l12-9 12 9v18H48z" stroke="currentColor" strokeWidth="2" strokeLinejoin="round" />
      <path d="M22 48v8M34 48v8M52 48v8M68 48v8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" opacity="0.55" />
      <path d="M6 58c6-3 12-3 18 0s12 3 18 0 12-3 18 0 12 3 18 0" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" opacity="0.5" />
    </Frame>
  );
}

/** Vientiane — Pha That Luang: the tapered stupa on its tiered base. */
function PhaThatLuang({ className }: LandmarkProps) {
  return (
    <Frame className={className}>
      <path d="M12 56h72" stroke="currentColor" strokeWidth="2" strokeLinecap="round" opacity="0.4" />
      <path d="M32 56V44h32v12z" fill="currentColor" opacity="0.28" />
      <path d="M38 44V34h20v10z" fill="currentColor" opacity="0.4" />
      <path d="M48 6l7 16c0 6-3 12-7 12s-7-6-7-12z" fill="currentColor" />
      <path d="M32 56V44h32v12M38 44V34h20v10" stroke="currentColor" strokeWidth="2" strokeLinejoin="round" />
    </Frame>
  );
}

/** Tokyo — the lattice tower. */
function TokyoTower({ className }: LandmarkProps) {
  return (
    <Frame className={className}>
      <path d="M8 56h80" stroke="currentColor" strokeWidth="2" strokeLinecap="round" opacity="0.35" />
      <path d="M48 6v8M40 56L48 14l8 42" stroke="currentColor" strokeWidth="2.5" strokeLinejoin="round" />
      <path d="M42 40h12M38 50h20" stroke="currentColor" strokeWidth="2" strokeLinecap="round" opacity="0.7" />
      <path d="M44 26h8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" opacity="0.55" />
      <path d="M22 56V44M74 56V44" stroke="currentColor" strokeWidth="2" strokeLinecap="round" opacity="0.3" />
    </Frame>
  );
}

/** Osaka — the castle keep: stacked roofs with upturned eaves. */
function OsakaCastle({ className }: LandmarkProps) {
  return (
    <Frame className={className}>
      <path d="M10 56h76" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
      <path d="M48 10l12 8H36zM48 20l16 9H32zM48 31l20 10H28z" fill="currentColor" opacity="0.35" />
      <path d="M48 10l12 8H36zM48 20l16 9H32zM48 31l20 10H28z" stroke="currentColor" strokeWidth="2" strokeLinejoin="round" />
      <path d="M34 41h28v9H34z" fill="currentColor" opacity="0.25" stroke="currentColor" strokeWidth="2" />
    </Frame>
  );
}

/** Kyoto — a torii gate, standing clear. */
function Torii({ className }: LandmarkProps) {
  return (
    <Frame className={className}>
      <path d="M8 56h80" stroke="currentColor" strokeWidth="2" strokeLinecap="round" opacity="0.35" />
      <path d="M18 18h60" stroke="currentColor" strokeWidth="4" strokeLinecap="round" />
      <path d="M24 28h48" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
      <path d="M32 18v38M64 18v38" stroke="currentColor" strokeWidth="3.5" strokeLinecap="round" />
      <path d="M46 28v6h4v-6" stroke="currentColor" strokeWidth="2" opacity="0.6" />
    </Frame>
  );
}

/** Fukuoka — the triangular tower on the bay. */
function FukuokaTower({ className }: LandmarkProps) {
  return (
    <Frame className={className}>
      <path d="M8 56h80" stroke="currentColor" strokeWidth="2" strokeLinecap="round" opacity="0.35" />
      <path d="M48 8l10 48H38z" fill="currentColor" opacity="0.32" />
      <path d="M48 8l10 48H38z" stroke="currentColor" strokeWidth="2" strokeLinejoin="round" />
      <path d="M43 32h10M41 44h14" stroke="currentColor" strokeWidth="2" strokeLinecap="round" opacity="0.65" />
      <path d="M12 58c6-3 12-3 18 0M66 58c6-3 12-3 18 0" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" opacity="0.45" />
    </Frame>
  );
}

/** Anywhere without a drawing yet: a horizon and a route, the product's own shape. */
function GenericPlace({ className }: LandmarkProps) {
  return (
    <Frame className={className}>
      <path d="M6 50h84" stroke="currentColor" strokeWidth="2" strokeLinecap="round" opacity="0.4" />
      <path d="M16 44C30 20 66 20 80 40" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeDasharray="4 5" opacity="0.7" />
      <circle cx="16" cy="44" r="4" fill="currentColor" />
      <circle cx="80" cy="40" r="4" fill="currentColor" opacity="0.6" />
    </Frame>
  );
}

/**
 * Keyed by catalogue `name` rather than IATA: two destinations in the set
 * (Belitung, Kyoto) have no airport code of their own, and a landmark should not
 * disappear because the nearest airport is in another city.
 */
const BY_NAME: Record<string, (props: LandmarkProps) => React.ReactElement> = {
  Yogyakarta: Borobudur,
  Lombok: Rinjani,
  Belitung: Belitung,
  Bandung: Bandung,
  Malang: Bromo,
  "Kuala Lumpur": Petronas,
  "Ho Chi Minh City": Bitexco,
  "Chiang Mai": LannaTemple,
  "Siem Reap": AngkorWat,
  Penang: ClanJetty,
  Vientiane: PhaThatLuang,
  Tokyo: TokyoTower,
  Osaka: OsakaCastle,
  Kyoto: Torii,
  Fukuoka: FukuokaTower,
};

export function Landmark({ name, className }: { name: string; className?: string }) {
  const Drawing = BY_NAME[name] ?? GenericPlace;
  return <Drawing className={className} />;
}

export function hasLandmark(name: string): boolean {
  return name in BY_NAME;
}

import { cn } from "@/lib/utils";

/**
 * The tile that identifies a carrier in a list of twenty fares.
 *
 * **Not a logo.** Airline logos are third-party trademarks; using them would
 * mean either hotlinking a logo CDN — an external request on a page that
 * currently makes none, plus a dependency that breaks silently when it moves —
 * or shipping marks this project has no licence to redistribute. Neither is
 * worth it for a tile 32 pixels wide.
 *
 * What people actually scan a fare list for is "is this the same airline as the
 * row above". A carrier's own colour answers that instantly and carries no
 * trademark: the code stays the identifier, the hue makes it separable.
 *
 * The hues follow the same discipline as the travel-type palette — identical
 * lightness and chroma, only hue moves. Real brand colours vary wildly in
 * saturation, and dropping them in raw would make a results list where Lion Air
 * shouts and Garuda whispers, which is a ranking nobody chose. These are the
 * recognisable hue at a disciplined weight.
 */

/** Carrier → hue angle. Chosen to echo the airline's own colour, not to match it. */
const HUE: Record<string, number> = {
  // Indonesia
  GA: 200, // Garuda Indonesia — teal blue
  JT: 25, // Lion Air — red
  QG: 150, // Citilink — green
  ID: 250, // Batik Air — blue
  IU: 55, // Super Air Jet — orange
  SJ: 35, // Sriwijaya Air — red orange
  IW: 190, // Wings Air
  // Regional
  AK: 20, // AirAsia
  D7: 20, // AirAsia X
  MH: 230, // Malaysia Airlines
  OD: 130, // Batik Air Malaysia
  SQ: 245, // Singapore Airlines
  TR: 85, // Scoot
  TG: 310, // Thai Airways — purple
  FD: 20, // Thai AirAsia
  VN: 235, // Vietnam Airlines
  VJ: 350, // VietJet
  // North Asia
  NH: 255, // ANA
  JL: 28, // JAL
  CX: 180, // Cathay Pacific
  CI: 15, // China Airlines
  KE: 215, // Korean Air
  OZ: 340, // Asiana
};

export function AirlineMark({
  code,
  name,
  className,
}: {
  code: string;
  /** Shown on hover; the tile itself only has room for the code. */
  name?: string;
  className?: string;
}) {
  const hue = HUE[code?.toUpperCase()];

  // An unknown carrier gets the neutral treatment rather than a guessed hue. A
  // wrong colour is worse than no colour: it would imply a relationship between
  // two airlines that share nothing.
  const known = hue !== undefined;

  return (
    <span
      className={cn(
        "tabular grid size-8 shrink-0 place-items-center rounded-md font-mono text-2xs font-semibold",
        known ? "airline-tile" : "bg-surface-2 text-fg-muted",
        className,
      )}
      style={known ? ({ "--airline-hue": hue } as React.CSSProperties) : undefined}
      title={name}
      aria-hidden
    >
      {code}
    </span>
  );
}

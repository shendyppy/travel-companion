import { cn } from "@/lib/utils";

/**
 * The colour a travel type wears, and the small chip that wears it.
 *
 * All eight hues sit at identical lightness and chroma in `globals.css` — only
 * the hue moves. That is what stops eight colours reading as a pile of stickers:
 * nothing is louder than anything else, which is honest, because no travel type
 * outranks another. Colour here is a label, not a ranking.
 *
 * The map lived inside `InspirationGrid` and was the only place in the app using
 * the category palette at all — eight designed hues doing one job on one screen.
 * It is here so anything showing a destination can say what kind of trip it is.
 *
 * Class names are written out in full because Tailwind scans source text. A
 * template literal like `bg-cat-${value}-soft` compiles to no CSS whatsoever,
 * silently, which is a trap worth the repetition to avoid.
 */
export const CATEGORY_STYLE: Record<string, { tint: string; mark: string }> = {
  beach: { tint: "bg-cat-beach-soft", mark: "text-cat-beach" },
  mountain: { tint: "bg-cat-mountain-soft", mark: "text-cat-mountain" },
  cultural: { tint: "bg-cat-cultural-soft", mark: "text-cat-cultural" },
  city: { tint: "bg-cat-city-soft", mark: "text-cat-city" },
  adventure: { tint: "bg-cat-adventure-soft", mark: "text-cat-adventure" },
  nature: { tint: "bg-cat-nature-soft", mark: "text-cat-nature" },
  foodie: { tint: "bg-cat-foodie-soft", mark: "text-cat-foodie" },
  shopping: { tint: "bg-cat-shopping-soft", mark: "text-cat-shopping" },
};

export const NEUTRAL_STYLE = { tint: "bg-surface-2", mark: "text-fg-muted" };

export function categoryStyle(value: string | undefined) {
  return (value && CATEGORY_STYLE[value]) || NEUTRAL_STYLE;
}

/**
 * A destination's kind, as a tinted label.
 *
 * Takes the raw facet value for the colour and a display label separately,
 * because the value is an English enum (`cultural`) and the label is translated
 * (`Budaya`). Colouring by the label would break the moment someone switches
 * language.
 */
export function TravelTypeMark({
  value,
  label,
  className,
}: {
  value?: string;
  label: string;
  className?: string;
}) {
  const style = categoryStyle(value);

  return (
    <span
      className={cn(
        "inline-flex w-fit items-center gap-1.5 rounded-pill px-2 py-0.5 text-2xs font-medium",
        style.tint,
        style.mark,
        className,
      )}
    >
      <span className="size-1.5 rounded-full bg-current" aria-hidden />
      {label}
    </span>
  );
}

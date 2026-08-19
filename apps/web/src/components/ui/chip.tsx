"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

interface ChipProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  selected?: boolean;
}

/**
 * A selectable pill, used for facets and follow-up suggestions.
 *
 * `whitespace-normal` and `text-left` are deliberate. Chip content here is
 * user-facing Indonesian of unpredictable length — facet labels like
 * "Petualangan", agent-generated follow-ups like "Cariin yang berangkat pagi
 * dong" — and a chip that truncates its own label is worse than one that wraps
 * to two lines.
 */
export const Chip = React.forwardRef<HTMLButtonElement, ChipProps>(
  ({ className, selected, ...props }, ref) => (
    <button
      ref={ref}
      type="button"
      aria-pressed={selected}
      className={cn(
        "pressable inline-flex items-center gap-1.5 rounded-pill border px-3.5 py-1.5 text-sm text-left whitespace-normal",
        "transition-[background-color,border-color,color,transform] duration-[--duration-fast]",
        selected
          ? "border-accent bg-accent-soft text-accent font-medium"
          : "border-border bg-surface text-fg-muted hover:border-border-strong hover:text-fg",
        className,
      )}
      {...props}
    />
  ),
);
Chip.displayName = "Chip";

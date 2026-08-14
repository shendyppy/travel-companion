import * as React from "react";
import { cn } from "@/lib/utils";

/**
 * Flat by default. Elevation is reserved for things that genuinely float —
 * dialogs, the mobile sheet, a dropdown — so that when a shadow does appear it
 * means something. A page of cards all wearing drop shadows says nothing about
 * hierarchy.
 */
export const Card = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn("rounded-card border border-border bg-surface", className)}
      {...props}
    />
  ),
);
Card.displayName = "Card";

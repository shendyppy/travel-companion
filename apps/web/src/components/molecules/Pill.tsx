import { cn } from "@/lib/utils";

/**
 * The small accent-soft label that marks one option out of a list — "termurah",
 * "tercepat".
 *
 * Deliberately not `ui/badge`. That one is the general-purpose shadcn primitive
 * with six variants; this is the single treatment this product uses to say "of
 * everything here, look at this one", and it stays one thing so that meaning
 * does not drift into decoration.
 */
export function Pill({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <span
      className={cn(
        "shrink-0 rounded-pill bg-accent-soft px-2 py-0.5 text-2xs font-medium text-accent",
        className,
      )}
    >
      {children}
    </span>
  );
}

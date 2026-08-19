import { cn } from "@/lib/utils";
import { rupiah } from "@/lib/format";

/**
 * A price, everywhere.
 *
 * Money had the same three classes copied onto it in six places — `tabular`,
 * `font-mono`, `text-price` — plus, in two of them, its own copy of the "is this
 * rupiah?" branch. The classes are not styling preference: tabular figures are
 * what let a column of fares line up so the eye can run down it, and this is the
 * only thing on any page that gets the price colour.
 *
 * It takes either an amount to format or text that is already formatted, because
 * both genuinely occur. A fare from the API is a number; a budget band is the
 * range "< 1jt", which was written as a label and has no single amount to round.
 * Splitting these into two components would put the treatment in two places
 * again, which is the thing this exists to stop.
 *
 * Foreign currency is rounded. Fares arrive with decimals attached and a
 * fractional rupiah-equivalent is noise, not precision — one of the two flight
 * surfaces already rounded and the other did not, which is the kind of
 * disagreement that only ends when there is one code path.
 */
type PriceProps = {
  /** `sm` supports something else, `md` is the default, `lg` is the number on a card. */
  size?: "sm" | "md" | "lg";
  className?: string;
} & (
  | { amount: number; currency?: string; children?: never }
  | { children: React.ReactNode; amount?: never; currency?: never }
);

const SIZES = { sm: "text-sm", md: "text-base", lg: "text-lg" } as const;

export function Price({ amount, currency = "IDR", size = "md", className, children }: PriceProps) {
  return (
    <span className={cn("tabular font-mono font-semibold text-price", SIZES[size], className)}>
      {children ??
        (currency === "IDR" ? rupiah(amount!) : `${currency} ${Math.round(amount!)}`)}
    </span>
  );
}

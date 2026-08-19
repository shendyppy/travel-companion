"use client";

/**
 * Which city the fare rail departs from.
 *
 * Deliberately a picker rather than geolocation. Detection would be a guess, and
 * a guess about where you live is the kind that annoys people when it is wrong —
 * a Surabaya user shown Jakarta fares under a confident heading has been
 * mislabelled, not helped. The server already clamps unknown origins and reports
 * which one it actually served; this just makes the choice explicit and cheap to
 * change.
 *
 * The list is the set the server warms. Offering cities with no cached fares
 * would mean every pick lands on an empty rail.
 */

import { useRouter, useSearchParams } from "next/navigation";
import { MapPin } from "lucide-react";
import { useMessages } from "@/components/i18n/MessagesProvider";

export const ORIGINS = [
  { iata: "CGK", label: "Jakarta" },
  { iata: "SUB", label: "Surabaya" },
  { iata: "DPS", label: "Bali" },
  { iata: "KNO", label: "Medan" },
  { iata: "UPG", label: "Makassar" },
] as const;

export function originLabel(iata: string): string {
  return ORIGINS.find((o) => o.iata === iata)?.label ?? iata;
}

export function OriginPicker({ value }: { value: string }) {
  const router = useRouter();
  const params = useSearchParams();
  const { m, locale } = useMessages();

  const change = (iata: string) => {
    const next = new URLSearchParams(params.toString());
    next.set("origin", iata);
    // The rail is rendered on the server from a cached endpoint, so a navigation
    // is the refetch. `scroll: false` keeps the viewport where the user was.
    router.push(`/${locale}?${next.toString()}`, { scroll: false });
  };

  return (
    <label className="inline-flex items-center gap-2 rounded-lg border border-border bg-surface px-3 py-1.5 text-sm">
      <MapPin className="size-3.5 shrink-0 text-fg-subtle" aria-hidden />
      <span className="sr-only">{m.deals.originLabel}</span>
      <select
        value={value}
        onChange={(event) => change(event.target.value)}
        className="bg-transparent font-medium outline-none"
      >
        {ORIGINS.map((origin) => (
          <option key={origin.iata} value={origin.iata}>
            {origin.label}
          </option>
        ))}
      </select>
    </label>
  );
}

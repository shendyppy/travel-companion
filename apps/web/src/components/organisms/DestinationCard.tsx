"use client";

import { useMessages } from "@/components/i18n/MessagesProvider";
import { Price } from "@/components/molecules/Price";
import type { Destination } from "@/lib/types";

/**
 * One recommended destination.
 *
 * The daily cost is the load-bearing number, not the description. These figures
 * are curated in rupiah for Indonesian travellers specifically — they are the
 * thing the model would otherwise invent, so the card treats them as the point
 * rather than as a footnote.
 */
export function DestinationCard({
  destination,
  onAsk,
}: {
  destination: Destination;
  onAsk?: (city: string) => void;
}) {
  const { m, t } = useMessages();
  const daily = destination.estimated_daily_total_idr;

  return (
    <div className="rounded-card border border-border bg-surface p-3.5">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h4 className="truncate font-semibold">{destination.name}</h4>
          <p className="text-xs text-fg-muted">{destination.country}</p>
        </div>
        {daily ? (
          <div className="shrink-0 text-right">
            <Price amount={daily} size="sm" className="block" />
            <p className="text-2xs text-fg-muted">per hari</p>
          </div>
        ) : null}
      </div>

      <p className="mt-2 text-sm text-fg-muted">{destination.description}</p>

      {destination.highlights?.length > 0 && (
        <ul className="mt-2.5 flex flex-wrap gap-1.5">
          {destination.highlights.slice(0, 3).map((highlight) => (
            <li
              key={highlight}
              className="rounded-pill bg-surface-2 px-2 py-0.5 text-2xs text-fg-muted"
            >
              {highlight}
            </li>
          ))}
        </ul>
      )}

      {onAsk && (
        <button
          type="button"
          onClick={() => onAsk(destination.name)}
          className="mt-3 text-sm font-medium text-accent hover:underline"
        >
          {t(m.tool.askAbout, { city: destination.name })}
        </button>
      )}
    </div>
  );
}

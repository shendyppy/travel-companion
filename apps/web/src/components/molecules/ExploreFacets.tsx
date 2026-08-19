"use client";

/**
 * Inspiration search: describe the trip, not the route.
 *
 * Every filter is optional, because the tool behind it requires nothing. That is
 * worth designing for rather than papering over — a user who picks nothing and
 * hits search gets the full curated set, which is a perfectly good answer to
 * "surprise me". So the button stays enabled from the start and the empty state
 * is a feature.
 *
 * Budget leads. Indonesian travellers pick a number before they pick a place far
 * more often than the other way round, and no OTA lets them start there.
 */

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Sparkles } from "lucide-react";
import { Chip } from "@/components/ui/chip";
import { useMessages } from "@/components/i18n/MessagesProvider";
import type { Facets, ToolSeed } from "@/lib/types";
import type { Submission } from "@/components/organisms/FlightSearchForm";

export function ExploreFacets({
  facets,
  onSubmit,
  busy,
}: {
  facets: Facets;
  onSubmit: (submission: Submission) => void;
  busy?: boolean;
}) {
  const [budget, setBudget] = useState<string | null>(null);
  const [types, setTypes] = useState<string[]>([]);
  const [region, setRegion] = useState<string | null>(null);
  const [season, setSeason] = useState<string | null>(null);
  const { m, t } = useMessages();

  const toggleType = (value: string) =>
    setTypes((prev) => (prev.includes(value) ? prev.filter((t) => t !== value) : [...prev, value]));

  const submit = () => {
    if (busy) return;

    const args: Record<string, unknown> = {};
    if (budget) args.budget = budget;
    if (types.length) args.travel_types = types;
    if (region) args.region = region;
    if (season) args.season = season;

    const seed: ToolSeed = { tool: "recommend_destinations", arguments: args };

    // The message mirrors what the chips say, so the conversation reads as
    // though the user typed it. An empty selection still needs a sentence — the
    // seed is context, never a replacement for the message.
    const bits: string[] = [];
    if (budget) {
      const band = facets.budget_bands.find((b) => b.value === budget);
      if (band) bits.push(t(m.explore.bitBudget, { range: band.range_label }));
    }
    if (types.length) {
      const labels = types
        .map((value) => facets.travel_types.find((f) => f.value === value)?.label.toLowerCase())
        .filter(Boolean);
      if (labels.length) {
        bits.push(t(m.explore.bitVibe, { labels: labels.join(m.explore.and) }));
      }
    }
    if (region) {
      bits.push(facets.regions.find((r) => r.value === region)?.label.toLowerCase() ?? region);
    }
    if (season) {
      bits.push(facets.seasons.find((s) => s.value === season)?.label.toLowerCase() ?? season);
    }

    const message = bits.length
      ? t(m.explore.messageWith, { bits: bits.join(", ") })
      : m.explore.messageAny;

    onSubmit({ message, seed });
  };

  return (
    <div className="grid gap-4">
      <Group label={m.explore.budget}>
        {facets.budget_bands.map((band) => (
          <Chip
            key={band.value}
            selected={budget === band.value}
            onClick={() => setBudget(budget === band.value ? null : band.value)}
          >
            <span className="font-medium">{band.label}</span>
            <span className="tabular text-xs opacity-70">{band.range_label}</span>
          </Chip>
        ))}
      </Group>

      <Group label={m.explore.vibe}>
        {facets.travel_types.map((type) => (
          <Chip
            key={type.value}
            selected={types.includes(type.value)}
            onClick={() => toggleType(type.value)}
          >
            {type.label}
          </Chip>
        ))}
      </Group>

      <div className="grid gap-4 sm:grid-cols-2">
        <Group label={m.explore.where}>
          {facets.regions.map((r) => (
            <Chip
              key={r.value}
              selected={region === r.value}
              onClick={() => setRegion(region === r.value ? null : r.value)}
            >
              {r.label}
            </Chip>
          ))}
        </Group>

        <Group label={m.explore.season}>
          {facets.seasons.slice(0, 4).map((s) => (
            <Chip
              key={s.value}
              selected={season === s.value}
              onClick={() => setSeason(season === s.value ? null : s.value)}
            >
              {s.label}
            </Chip>
          ))}
        </Group>
      </div>

      <Button type="button" onClick={submit} disabled={busy} className="self-start">
        <Sparkles className="size-4" aria-hidden />
        {m.explore.submit}
      </Button>
    </div>
  );
}

function Group({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <fieldset className="min-w-0">
      <legend className="mb-2 text-2xs font-medium uppercase tracking-wide text-fg-subtle">
        {label}
      </legend>
      <div className="flex flex-wrap gap-2">{children}</div>
    </fieldset>
  );
}

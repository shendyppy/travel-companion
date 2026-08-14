"use client";

/**
 * The structured flight search.
 *
 * The densest thing on the landing page, and it can carry that density because
 * it is also the most familiar — anyone who has booked a flight in Indonesia has
 * filled in this exact form.
 *
 * Origin and destination stay free text rather than becoming an autocomplete
 * over an airport list. `lookup_place` resolves city names, nicknames and IATA
 * codes server-side against 6,000 airports, so "Jogja", "YIA" and "Yogyakarta"
 * all work. Putting a picker in front of that would replace something forgiving
 * with something that can be wrong.
 */

import { useState } from "react";
import { ArrowRight, Users } from "lucide-react";
import { cn } from "@/lib/utils";
import { isoDateIn, shortDate } from "@/lib/format";
import type { ToolSeed } from "@/lib/types";

export interface Submission {
  message: string;
  seed: ToolSeed;
}

function Field({
  label,
  children,
  className,
}: {
  label: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <label className={cn("flex min-w-0 flex-col gap-1", className)}>
      <span className="text-2xs font-medium uppercase tracking-wide text-fg-subtle">{label}</span>
      {children}
    </label>
  );
}

const inputClass =
  "h-10 w-full min-w-0 rounded-lg border border-border bg-surface px-3 text-base outline-none " +
  "placeholder:text-fg-subtle focus:border-border-strong";

export function FlightSearchForm({
  onSubmit,
  busy,
}: {
  onSubmit: (submission: Submission) => void;
  busy?: boolean;
}) {
  const [origin, setOrigin] = useState("Jakarta");
  const [destination, setDestination] = useState("");
  const [departure, setDeparture] = useState(isoDateIn(30));
  const [rangeEnd, setRangeEnd] = useState(isoDateIn(37));
  const [flexible, setFlexible] = useState(false);
  const [adults, setAdults] = useState(1);

  const ready = origin.trim() && destination.trim();

  const submit = () => {
    if (!ready || busy) return;

    // Flexible dates are a different tool, not a different argument: probing a
    // range costs one provider call per date, so the model must not reach for it
    // unless the user actually asked for it.
    const seed: ToolSeed = flexible
      ? {
          tool: "search_flights_flexible",
          arguments: {
            origin: origin.trim(),
            destination: destination.trim(),
            start_date: departure,
            end_date: rangeEnd,
            adults,
          },
        }
      : {
          tool: "search_flights",
          arguments: {
            origin: origin.trim(),
            destination: destination.trim(),
            departure_date: departure,
            adults,
          },
        };

    const who = adults > 1 ? `, ${adults} orang` : "";
    const message = flexible
      ? `Cari penerbangan termurah ${origin} ke ${destination} antara ${shortDate(departure)} sampai ${shortDate(rangeEnd)}${who}`
      : `Cari penerbangan ${origin} ke ${destination} tanggal ${shortDate(departure)}${who}`;

    onSubmit({ message, seed });
  };

  return (
    <div className="grid gap-3">
      <div className="grid gap-3 sm:grid-cols-2">
        <Field label="Dari">
          <input
            className={inputClass}
            value={origin}
            onChange={(e) => setOrigin(e.target.value)}
            placeholder="Jakarta"
            autoComplete="off"
          />
        </Field>
        <Field label="Ke">
          <input
            className={inputClass}
            value={destination}
            onChange={(e) => setDestination(e.target.value)}
            placeholder="Bali, Tokyo, Bangkok…"
            autoComplete="off"
          />
        </Field>
      </div>

      <div className="grid gap-3 sm:grid-cols-[1fr_1fr_auto]">
        <Field label={flexible ? "Dari tanggal" : "Tanggal berangkat"}>
          <input
            type="date"
            className={cn(inputClass, "tabular")}
            value={departure}
            min={isoDateIn(0)}
            onChange={(e) => setDeparture(e.target.value)}
          />
        </Field>

        {flexible ? (
          <Field label="Sampai tanggal">
            <input
              type="date"
              className={cn(inputClass, "tabular")}
              value={rangeEnd}
              min={departure}
              onChange={(e) => setRangeEnd(e.target.value)}
            />
          </Field>
        ) : (
          <Field label="Penumpang">
            <div className="flex h-10 items-center gap-2 rounded-lg border border-border bg-surface px-3">
              <Users className="size-4 shrink-0 text-fg-subtle" aria-hidden />
              <select
                className="w-full bg-transparent text-base outline-none"
                value={adults}
                onChange={(e) => setAdults(Number(e.target.value))}
                aria-label="Jumlah penumpang dewasa"
              >
                {Array.from({ length: 9 }, (_, i) => i + 1).map((n) => (
                  <option key={n} value={n}>
                    {n} dewasa
                  </option>
                ))}
              </select>
            </div>
          </Field>
        )}

        <div className="flex items-end">
          <button
            type="button"
            onClick={submit}
            disabled={!ready || busy}
            className={cn(
              "inline-flex h-10 w-full items-center justify-center gap-2 rounded-lg px-6 text-sm font-medium sm:w-auto",
              "bg-accent text-accent-fg transition-opacity disabled:opacity-40",
            )}
          >
            Cari penerbangan
            <ArrowRight className="size-4" aria-hidden />
          </button>
        </div>
      </div>

      <label className="flex w-fit cursor-pointer items-center gap-2 text-sm text-fg-muted">
        <input
          type="checkbox"
          checked={flexible}
          onChange={(e) => setFlexible(e.target.checked)}
          className="size-4 accent-[var(--color-accent)]"
        />
        Tanggal saya fleksibel — cariin yang paling murah
      </label>
    </div>
  );
}

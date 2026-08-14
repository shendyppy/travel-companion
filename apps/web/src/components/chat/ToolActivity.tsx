"use client";

/**
 * What the agent is doing, in plain language.
 *
 * The tension this component exists to solve: it should feel like transparency,
 * not like a debug console. Someone who does not care about the mechanics should
 * find it reassuring; someone who does should be able to see exactly what
 * happened. So the default is one calm sentence in Indonesian — "Mencari
 * penerbangan CGK → DPS" — and the raw arguments and result are one click away
 * behind a disclosure, not on screen by default.
 *
 * Failure gets the same treatment as success rather than a red alert. Tools fail
 * routinely: a route with no flights, a place with no curated data. The agent is
 * built to say so honestly instead of inventing a number, and a UI that screams
 * every time would make normal operation feel broken.
 */

import { useState } from "react";
import { Check, ChevronDown, Loader2, MinusCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { shortDate } from "@/lib/format";
import type { ToolActivity as Activity } from "@/lib/types";

function arg(args: Record<string, unknown>, key: string): string | undefined {
  const value = args[key];
  return typeof value === "string" && value ? value : undefined;
}

/**
 * Turn a tool call into a sentence.
 *
 * Deliberately describes the *intent*, not the function. "Mencari penerbangan"
 * rather than "search_flights(origin=CGK, destination=DPS)". A user who wanted
 * the function signature can open the disclosure.
 */
function describe(activity: Activity): string {
  const { tool, arguments: args } = activity;
  const route = [arg(args, "origin"), arg(args, "destination")].filter(Boolean).join(" → ");

  switch (tool) {
    case "search_flights": {
      const date = arg(args, "departure_date");
      return `Mencari penerbangan ${route}${date ? `, ${shortDate(date)}` : ""}`;
    }
    case "search_flights_flexible":
      return `Mencari tanggal termurah ${route}`;
    case "recommend_destinations":
      return "Menyusun rekomendasi destinasi";
    case "get_destination_info":
      return `Membaca data ${arg(args, "city") ?? "destinasi"}`;
    case "lookup_place":
      return `Mencari kode bandara ${arg(args, "query") ?? ""}`.trim();
    case "resolve_dates":
      return "Menentukan tanggalnya";
    case "search_knowledge":
      return "Membaca panduan perjalanan";
    default:
      return `Menjalankan ${tool}`;
  }
}

/**
 * What came back, in one clause.
 *
 * Counting results is worth the branching: "3 penerbangan" tells a user
 * something "Selesai" does not, and it is the difference between a status line
 * that reassures and one that is merely present.
 */
function summarise(activity: Activity): string {
  const result = activity.result;
  if (!result) return "";
  if (!result.ok) return result.error ? "tidak ketemu" : "gagal";

  const data = result.data as Record<string, unknown> | undefined;
  if (!data) return "selesai";

  const flights = data.flights as unknown[] | undefined;
  if (Array.isArray(flights)) {
    return flights.length ? `${flights.length} penerbangan` : "tidak ada penerbangan";
  }
  const destinations = data.destinations as unknown[] | undefined;
  if (Array.isArray(destinations)) {
    return destinations.length ? `${destinations.length} destinasi` : "tidak ada yang cocok";
  }
  const passages = data.passages as unknown[] | undefined;
  if (Array.isArray(passages)) return `${passages.length} kutipan`;

  return "selesai";
}

export function ToolActivity({ activity }: { activity: Activity }) {
  const [open, setOpen] = useState(false);
  const running = !activity.result;
  const failed = Boolean(activity.result && !activity.result.ok);

  return (
    <div
      className={cn(
        "animate-rise rounded-lg border text-sm",
        failed ? "border-border bg-warning-soft/40" : "border-border bg-surface-2",
      )}
    >
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="flex w-full items-center gap-2.5 px-3 py-2 text-left"
      >
        <span className="shrink-0" aria-hidden>
          {running ? (
            <Loader2 className="size-3.5 animate-spin text-accent" />
          ) : failed ? (
            <MinusCircle className="size-3.5 text-warning" />
          ) : (
            <Check className="size-3.5 text-success" />
          )}
        </span>

        <span className={cn("min-w-0 flex-1 truncate", running ? "text-fg-muted" : "text-fg")}>
          {describe(activity)}
        </span>

        {!running && (
          <span className="shrink-0 text-xs text-fg-muted">{summarise(activity)}</span>
        )}

        <ChevronDown
          className={cn(
            "size-3.5 shrink-0 text-fg-subtle transition-transform duration-[--duration-fast]",
            open && "rotate-180",
          )}
          aria-hidden
        />
      </button>

      {open && (
        <div className="animate-fade border-t border-border px-3 py-2">
          <p className="mb-1 text-2xs uppercase tracking-wide text-fg-subtle">
            {activity.tool}
          </p>
          <pre className="overflow-x-auto text-2xs leading-relaxed text-fg-muted">
            {JSON.stringify(activity.arguments, null, 2)}
          </pre>
          {failed && activity.result?.error && (
            <p className="mt-2 text-xs text-fg-muted">{activity.result.error}</p>
          )}
        </div>
      )}
    </div>
  );
}

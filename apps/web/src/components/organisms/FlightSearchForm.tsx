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
import { Button } from "@/components/ui/button";
import { isoDateIn, shortDate } from "@/lib/format";
import { useMessages } from "@/components/i18n/MessagesProvider";
import type { FlightQuery, ToolSeed } from "@/lib/types";

export interface Submission {
  message: string;
  seed: ToolSeed;
  /**
   * Set only by this form, and only for a fixed date.
   *
   * Its presence is how a caller knows the submission has a results page behind
   * it: a single date resolves to a list of flights that can be filtered and
   * sorted, so it navigates to `/flights`. A flexible range does not — it is a
   * probe across up to seven dates that answers "when is it cheapest", which is
   * a sentence, not a table. That one stays in the conversation.
   */
  flightQuery?: FlightQuery;
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
  initial,
  submitLabel,
  allowFlexible = true,
}: {
  onSubmit: (submission: Submission) => void;
  busy?: boolean;
  /** Prefill, so the results page can reopen the form on the search it ran. */
  initial?: Partial<FlightQuery>;
  submitLabel?: string;
  /**
   * Off where a flexible search has nowhere to go. A date range produces one
   * cheapest date, not a list, so it has no results page — and offering a toggle
   * whose submit would do nothing is worse than not offering it.
   */
  allowFlexible?: boolean;
}) {
  const [origin, setOrigin] = useState(initial?.origin ?? "Jakarta");
  const [destination, setDestination] = useState(initial?.destination ?? "");
  const [departure, setDeparture] = useState(initial?.departure_date ?? isoDateIn(30));
  const [returnDate, setReturnDate] = useState(initial?.return_date ?? isoDateIn(37));
  const [roundTrip, setRoundTrip] = useState(Boolean(initial?.return_date));
  const [rangeEnd, setRangeEnd] = useState(isoDateIn(37));
  const [flexible, setFlexible] = useState(false);
  const [adults, setAdults] = useState(initial?.adults ?? 1);
  const { m, t, locale } = useMessages();

  const ready = origin.trim() && destination.trim();

  // A return leg and a flexible departure window are different searches, not two
  // options on one. Flexible probes a range of *departure* dates for the cheapest
  // single day; asking that question about a round trip means pricing a grid, not
  // a list, which is not what the tool behind this does. Picking one clears
  // the other rather than letting an impossible combination sit on screen.
  const chooseRoundTrip = (next: boolean) => {
    setRoundTrip(next);
    if (next) setFlexible(false);
  };

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
            // Only sent when asked for. The tool prices a one-way search unless
            // it sees this, and passing it always would silently double what
            // every fare on the results page means.
            ...(roundTrip ? { return_date: returnDate } : {}),
            adults,
          },
        };

    // The message is translated as well as the labels, and that is load-bearing
    // rather than tidy: the agent replies in whatever language it is written to,
    // so an English visitor filling in this form must send English or they get an
    // Indonesian answer to a form they read in English.
    const who = adults > 1 ? t(m.flightForm.messageWho, { n: adults }) : "";
    const message = flexible
      ? t(m.flightForm.messageFlexible, {
          origin,
          destination,
          start: shortDate(departure, locale),
          end: shortDate(rangeEnd, locale),
          who,
        })
      : roundTrip
        ? t(m.flightForm.messageReturn, {
            origin,
            destination,
            date: shortDate(departure, locale),
            returnDate: shortDate(returnDate, locale),
            who,
          })
        : t(m.flightForm.messageFixed, {
            origin,
            destination,
            date: shortDate(departure, locale),
            who,
          });

    onSubmit({
      message,
      seed,
      flightQuery: flexible
        ? undefined
        : {
            origin: origin.trim(),
            destination: destination.trim(),
            departure_date: departure,
            return_date: roundTrip ? returnDate : null,
            adults,
          },
    });
  };

  return (
    <div className="grid gap-3">
      {/* Trip type leads, because it changes what the rest of the form asks for.
          Two segments rather than a checkbox: "pulang-pergi" is a choice between
          two kinds of trip, and a lone unticked box reads as an optional extra
          on a one-way search that was never actually the default anyone chose. */}
      <div
        className="inline-flex w-fit rounded-lg border border-border bg-surface-2 p-0.5"
        role="group"
        aria-label={m.flightForm.tripType}
      >
        {[
          { on: false, label: m.flightForm.oneWay },
          { on: true, label: m.flightForm.roundTrip },
        ].map((option) => (
          <button
            key={option.label}
            type="button"
            onClick={() => chooseRoundTrip(option.on)}
            aria-pressed={roundTrip === option.on}
            className={cn(
              "rounded-md px-3.5 py-1.5 text-sm font-medium transition-colors duration-[--duration-fast]",
              roundTrip === option.on
                ? "bg-surface text-fg shadow-card"
                : "text-fg-muted hover:text-fg",
            )}
          >
            {option.label}
          </button>
        ))}
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <Field label={m.flightForm.from}>
          <input
            className={inputClass}
            value={origin}
            onChange={(e) => setOrigin(e.target.value)}
            placeholder={m.flightForm.fromPlaceholder}
            autoComplete="off"
          />
        </Field>
        <Field label={m.flightForm.to}>
          <input
            className={inputClass}
            value={destination}
            onChange={(e) => setDestination(e.target.value)}
            placeholder={m.flightForm.toPlaceholder}
            autoComplete="off"
          />
        </Field>
      </div>

      <div
        className={cn(
          "grid gap-3",
          roundTrip ? "sm:grid-cols-[1fr_1fr_1fr_auto]" : "sm:grid-cols-[1fr_1fr_auto]",
        )}
      >
        <Field label={flexible ? m.flightForm.fromDate : m.flightForm.departureDate}>
          <input
            type="date"
            className={cn(inputClass, "tabular")}
            value={departure}
            min={isoDateIn(0)}
            onChange={(e) => {
              setDeparture(e.target.value);
              // A return before the departure is not a trip. Dragging the
              // outbound past the inbound pushes the inbound along rather than
              // waiting for the browser to reject it on submit.
              if (roundTrip && returnDate < e.target.value) setReturnDate(e.target.value);
            }}
          />
        </Field>

        {roundTrip && (
          <Field label={m.flightForm.returnDate}>
            <input
              type="date"
              className={cn(inputClass, "tabular")}
              value={returnDate}
              min={departure}
              onChange={(e) => setReturnDate(e.target.value)}
            />
          </Field>
        )}

        {flexible ? (
          <Field label={m.flightForm.toDate}>
            <input
              type="date"
              className={cn(inputClass, "tabular")}
              value={rangeEnd}
              min={departure}
              onChange={(e) => setRangeEnd(e.target.value)}
            />
          </Field>
        ) : (
          <Field label={m.flightForm.passengers}>
            <div className="flex h-10 items-center gap-2 rounded-lg border border-border bg-surface px-3">
              <Users className="size-4 shrink-0 text-fg-subtle" aria-hidden />
              <select
                className="w-full bg-transparent text-base outline-none"
                value={adults}
                onChange={(e) => setAdults(Number(e.target.value))}
                aria-label={m.flightForm.passengersLabel}
              >
                {Array.from({ length: 9 }, (_, i) => i + 1).map((n) => (
                  <option key={n} value={n}>
                    {t(m.flightForm.passengersCount, { n })}
                  </option>
                ))}
              </select>
            </div>
          </Field>
        )}

        <div className="flex items-end">
          <Button
            type="button"
            onClick={submit}
            disabled={!ready || busy}
            className="w-full sm:w-auto"
          >
            {submitLabel ?? m.flightForm.submit}
            <ArrowRight className="size-4" aria-hidden />
          </Button>
        </div>
      </div>

      {/* Hidden on a round trip rather than disabled: a control that cannot be
          used is noise, and there is nothing here to explain that would help. */}
      {allowFlexible && !roundTrip && (
        <label className="flex w-fit cursor-pointer items-center gap-2 text-sm text-fg-muted">
          <input
            type="checkbox"
            checked={flexible}
            onChange={(e) => setFlexible(e.target.checked)}
            className="size-4 accent-[var(--color-accent)]"
          />
          {m.flightForm.flexible}
        </label>
      )}
    </div>
  );
}

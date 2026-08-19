"use client";

/**
 * Owns the landing page's single conversation.
 *
 * Every interactive surface on the page — the command bar, the fare rail, the
 * inspiration tiles, the budget bands, the follow-up chips — calls `run`. One
 * turn, one session, one place it can be. That is what makes the claim in the
 * brief literally true rather than aspirational: there is no second path into
 * the agent, so the rails cannot quietly become links to a different experience.
 *
 * One submission does leave: a flight search on a fixed date goes to `/flights`
 * instead of streaming in place. It is the only shape of answer this product
 * produces that is genuinely a table — twenty rows to filter by airline, sort by
 * time, and compare — and morphing the hero into a table would be a worse
 * version of a page that already exists. Everything else, flexible dates
 * included, still answers here.
 *
 * The catalogue and deals arrive as props from the server component, so the
 * first paint has real destinations and real prices in it without a client
 * fetch.
 */

import { useCallback, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useAgentStream } from "@/hooks/useAgentStream";
import { stashHandoff } from "@/lib/handoff";
import { flightsHref } from "@/lib/flightsHref";
import { useMessages } from "@/components/i18n/MessagesProvider";
import { Hero } from "./Hero";
import { DealRail } from "./DealRail";
import { DemoSection } from "./DemoSection";
import { InspirationGrid } from "./InspirationGrid";
import { OnboardingTour } from "./OnboardingTour";
import { originLabel } from "./OriginPicker";
import type { Submission } from "./FlightSearchForm";
import type { CatalogueResponse, DealsResponse } from "@/lib/types";

export function LandingClient({
  catalogue,
  deals,
}: {
  catalogue: CatalogueResponse | null;
  deals: DealsResponse | null;
}) {
  const router = useRouter();
  const agent = useAgentStream();
  const { locale } = useMessages();
  const [summary, setSummary] = useState("");
  const [expanded, setExpanded] = useState(false);
  const answerRef = useRef<HTMLDivElement>(null);

  const run = useCallback(
    ({ message, seed, flightQuery }: Submission) => {
      // A fixed-date flight search has a results page behind it. Navigating is
      // not a bypass of the agent — the same tool with the same arguments runs
      // there, and the companion dock reads the route straight back out of the
      // URL.
      if (flightQuery) {
        router.push(flightsHref(flightQuery, locale));
        return;
      }

      setSummary(message);
      setExpanded(false);
      void agent.send(message, seed ? { seed } : undefined);
      // A tile halfway down the page has to bring the answer with it, or the
      // click looks like it did nothing.
      requestAnimationFrame(() =>
        answerRef.current?.scrollIntoView({ behavior: "smooth", block: "center" }),
      );
    },
    [agent, router, locale],
  );

  const handOff = () => {
    stashHandoff({ sessionId: agent.sessionId, messages: agent.messages });
    router.push(`/${locale}/chat`);
  };

  const origin = deals?.origin ?? "CGK";

  /*
   * Section order is the question a visitor is actually asking at that point:
   *
   *   hero        "mau ke mana?"
   *   inspirasi   "belum kepikiran, ada saran?"      <- was below the rail
   *   deals       "oke, dari sini ke sana berapa?"
   *   demo        "terus jadinya apa?"
   *
   * Inspiration moved above the fare rail because someone without a destination
   * cannot use a fare rail. Showing prices to Bali before asking whether they
   * want a beach at all was the page answering a question nobody had reached yet.
   */
  return (
    <>
      <div id="penerbangan">
        <Hero
          facets={catalogue?.facets ?? null}
          agent={agent}
          run={run}
          summary={summary}
          expanded={expanded}
          onExpand={() => setExpanded(true)}
          onHandOff={handOff}
          answerRef={answerRef}
        />
      </div>

      {catalogue && (
        <InspirationGrid
          travelTypes={catalogue.facets.travel_types}
          budgetBands={catalogue.facets.budget_bands}
          onRun={run}
        />
      )}

      {deals && <DealRail deals={deals} originLabel={originLabel(origin)} onRun={run} />}

      <DemoSection />

      <OnboardingTour />
    </>
  );
}

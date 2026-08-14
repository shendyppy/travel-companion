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
 * The catalogue and deals arrive as props from the server component, so the
 * first paint has real destinations and real prices in it without a client
 * fetch.
 */

import { useCallback, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useAgentStream } from "@/hooks/useAgentStream";
import { stashHandoff } from "@/lib/handoff";
import { Hero } from "./Hero";
import { DealRail } from "./DealRail";
import { InspirationGrid } from "./InspirationGrid";
import { OriginPicker, originLabel } from "./OriginPicker";
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
  const [summary, setSummary] = useState("");
  const [expanded, setExpanded] = useState(false);
  const answerRef = useRef<HTMLDivElement>(null);

  const run = useCallback(
    ({ message, seed }: Submission) => {
      setSummary(message);
      setExpanded(false);
      void agent.send(message, seed ? { seed } : undefined);
      // A tile halfway down the page has to bring the answer with it, or the
      // click looks like it did nothing.
      requestAnimationFrame(() =>
        answerRef.current?.scrollIntoView({ behavior: "smooth", block: "center" }),
      );
    },
    [agent],
  );

  const handOff = () => {
    stashHandoff({ sessionId: agent.sessionId, messages: agent.messages });
    router.push("/chat");
  };

  const origin = deals?.origin ?? "CGK";

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

      {deals && (
        <>
          <div className="mx-auto -mb-6 max-w-6xl px-5">
            <OriginPicker value={origin} />
          </div>
          <DealRail deals={deals} originLabel={originLabel(origin)} onRun={run} />
        </>
      )}

      {catalogue && (
        <div id="inspirasi">
          <InspirationGrid
            travelTypes={catalogue.facets.travel_types}
            budgetBands={catalogue.facets.budget_bands}
            onRun={run}
          />
        </div>
      )}
    </>
  );
}

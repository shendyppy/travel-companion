/**
 * Domain types.
 *
 * These are hand-written on purpose, and they are *not* the API contract.
 * `packages/types` holds the generated mirror of the FastAPI schema; that is the
 * source of truth for anything crossing the wire. What lives here is the shape
 * the UI thinks in — a message with interleaved tool activity, for instance, is
 * a thing the frontend assembles out of a stream of events and that no endpoint
 * ever returns.
 *
 * Where the two overlap (FlightInfo, Deal) these are kept structurally
 * compatible so a generated type can be swapped in without a rewrite.
 */

export type SeedableTool =
  | "search_flights"
  | "search_flights_flexible"
  | "recommend_destinations"
  | "get_destination_info";

/** A tool call the client decided on, sent alongside the message. */
export interface ToolSeed {
  tool: SeedableTool;
  arguments: Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// Catalogue
// ---------------------------------------------------------------------------

export interface FacetOption {
  value: string;
  label: string;
}

export interface BudgetBand extends FacetOption {
  range_label: string;
  min_idr: number | null;
  max_idr: number | null;
}

export interface Facets {
  travel_types: FacetOption[];
  budget_bands: BudgetBand[];
  seasons: FacetOption[];
  regions: FacetOption[];
}

export interface Destination {
  name: string;
  country: string;
  region: string;
  description: string;
  budget_category: string;
  travel_types: string[];
  best_season: string;
  estimated_daily_cost_idr: Record<string, number>;
  estimated_daily_total_idr: number | null;
  highlights: string[];
  why_budget_friendly: string;
  iata: string | null;
}

export interface CatalogueResponse {
  destinations: Destination[];
  facets: Facets;
}

// ---------------------------------------------------------------------------
// Deals
// ---------------------------------------------------------------------------

export interface Deal {
  city: string;
  country: string;
  iata: string;
  region: string;
  price_idr: number;
  airline: string | null;
  stops: number;
  daily_cost_idr: number | null;
  travel_types: string[];
}

export interface DealsResponse {
  origin: string;
  requested_origin: string | null;
  /** null means the rail is cold — render "cek harga", never a number. */
  updated_at: string | null;
  departure_date: string | null;
  deals: Deal[];
}

// ---------------------------------------------------------------------------
// Flights
// ---------------------------------------------------------------------------

export interface FlightInfo {
  airline: string;
  airline_code: string;
  departure_time: string;
  arrival_time: string;
  origin: string;
  destination: string;
  price: number;
  currency: string;
  duration: string;
  stops: number;
}

// ---------------------------------------------------------------------------
// Agent stream
// ---------------------------------------------------------------------------

/**
 * One tool call as the UI sees it. `result` is undefined while the tool is
 * still running — that gap is the whole reason ToolActivity exists, so it is
 * modelled explicitly rather than as a boolean flag beside a nullable field.
 */
export interface ToolActivity {
  id: string;
  tool: string;
  arguments: Record<string, unknown>;
  result?: { ok: boolean; data?: unknown; error?: string };
}

/**
 * A turn from the agent.
 *
 * `parts` is ordered: the agent may write a sentence, call a tool, then keep
 * writing, so a message is not a single block of text with tools bolted on the
 * side. Rendering walks this array in order.
 */
export type MessagePart =
  | { kind: "text"; text: string }
  | { kind: "tool"; activity: ToolActivity };

export interface Message {
  id: string;
  role: "user" | "agent";
  parts: MessagePart[];
  /** Still streaming — drives the caret and suppresses the timestamp. */
  pending?: boolean;
  error?: string;
  at: number;
}

/** Raw SSE payloads, exactly as `api.py` emits them. */
export type StreamEvent =
  | { type: "session"; session_id: string }
  | { type: "quota"; remaining: number }
  | { type: "quota_exceeded"; error: string; remaining: number }
  | { type: "seed_rejected"; tool: string; reason: string }
  | { type: "text_delta"; content: string }
  | { type: "tool_start"; tool: string; arguments: Record<string, unknown> }
  | { type: "tool_result"; tool: string; result: { ok: boolean; data?: unknown; error?: string } }
  | { type: "suggestions"; suggestions: string[] }
  | { type: "error"; error: string };

"""
Travel Companion API.

Notable changes from the previous version:

- **Real streaming.** /api/chat/stream used to call a synchronous agent to
  completion and then emit the whole reply in one event. That was not just fake
  streaming: the blocking call also stalled the event loop, so other users
  queued behind it. It is async end to end now.

- **Sessions no longer hold agent objects in memory.** There used to be an
  `_agents` cache of TravelAgent instances, because they could not be serialised
  to Redis. Conversations therefore broke as soon as Cloud Run ran more than one
  instance, or after a cold start. Only the message history is stored now --
  plain JSON any instance can read.

- **Tool events.** Clients receive tool_start and tool_result, so the UI can show
  what the agent is doing instead of an anonymous spinner.
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime
from typing import Any, AsyncIterator, Optional

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from src import access, catalogue, deals as deals_cache, flight_results, tools
from src.agent import AgentEvent, Turn, parse_seed, run as run_agent
from src.config import LOG_FORMAT, LOG_LEVEL
from src.providers import knowledge
from src.llm import active_provider, is_configured, resolve_model
from src.models import ChatRequest, ChatResponse, HealthResponse
from src.session_store import close_session_store, get_session_store
from src.suggestion_engine import ConversationState, get_suggestion_engine

logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

# How many recent messages travel with each turn. Unbounded history means token
# cost that only ever grows; 24 messages is roughly 12 exchanges, enough for a
# realistic planning conversation.
MAX_HISTORY_MESSAGES = 24

app = FastAPI(
    title="Travel Companion API",
    description="AI travel companion: destination recommendations, flight search, itinerary planning",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# allow_origins=["*"] together with allow_credentials=True is rejected by
# browsers, and becomes less defensible once BYOK lands. Origins are configurable.
_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins or ["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Accept", access.API_KEY_HEADER, access.PROVIDER_HEADER],
)

suggestions = get_suggestion_engine()


# ==============================================================================
# Sessions
# ==============================================================================


async def _load_session(session_id: Optional[str]) -> tuple[str, dict[str, Any]]:
    store = get_session_store()

    if session_id:
        data = await store.get(session_id)
        if data:
            data.setdefault("history", [])
            return session_id, data

    new_id = session_id or str(uuid.uuid4())
    data = {
        "created_at": datetime.now().isoformat(),
        "state": ConversationState.NEW.value,
        "destination": None,
        "message_count": 0,
        "history": [],
    }
    await store.set(new_id, data)
    logger.info("New session: %s", new_id[:8])
    return new_id, data


async def _save_session(session_id: str, data: dict[str, Any], turn: Turn) -> None:
    history = [*data.get("history", []), *turn.messages]
    data["history"] = history[-MAX_HISTORY_MESSAGES:]
    data["message_count"] = data.get("message_count", 0) + 1
    await get_session_store().set(session_id, data)


def _next_suggestions(data: dict[str, Any], user_message: str, reply: str, used_tools: list[str]) -> list[str]:
    state, destination = suggestions.detect_state_from_response(
        user_message=user_message,
        ai_response=reply,
        has_flights="search_flights" in used_tools,
        current_destination=data.get("destination"),
    )
    data["state"] = state.value
    if destination:
        data["destination"] = destination
    return suggestions.generate_suggestions(
        state=state,
        destination=destination or data.get("destination"),
        has_flights="search_flights" in used_tools,
        response_text=reply,
        count=4,
    )


# ==============================================================================
# Chat
# ==============================================================================


def _sse(payload: dict[str, Any]) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False, default=str)}\n\n"


@app.post("/api/chat/stream", tags=["Chat"])
async def chat_stream(request: ChatRequest, http: Request):
    """
    Streaming chat over Server-Sent Events.

    Event sequence:
        session       -> session id, sent first
        quota         -> demo messages left today (absent when the user brought a key)
        seed_rejected -> a supplied seed failed validation and was dropped; the
                         turn still runs on `message` alone. Not an error the
                         user should see -- it means the client sent something
                         wrong, so surface it in dev tooling, not in the UI.
        text_delta    -> text fragments, forwarded as the model produces them
        tool_start    -> the agent began calling a tool (drives UI status)
        tool_result   -> tool output (render as cards)
        suggestions   -> follow-up chips
        error         -> something failed; the stream still closes cleanly
        [DONE]        -> terminator
    """

    grant = await access.check(http)

    async def events() -> AsyncIterator[str]:
        session_id, data = await _load_session(request.session_id)
        yield _sse({"type": "session", "session_id": session_id})

        if not grant.allowed:
            # Quota is a normal outcome, not a server fault, so it arrives as an
            # event on an open stream rather than an HTTP error the client has to
            # special-case mid-conversation.
            yield _sse({"type": "quota_exceeded", "error": grant.reason, "remaining": 0})
            yield "data: [DONE]\n\n"
            return

        if not grant.using_own_key:
            yield _sse({"type": "quota", "remaining": grant.remaining})

        # Validated at the boundary, so the loop only ever receives a seed that
        # has already passed the allowlist and its schema. A rejected seed is
        # reported and dropped -- never fatal, because `message` on its own still
        # produces a perfectly good answer and this runs in a hero.
        agent_seed = None
        if request.seed is not None:
            agent_seed, seed_error = parse_seed(request.seed.tool, request.seed.arguments)
            if seed_error:
                yield _sse({"type": "seed_rejected", "tool": request.seed.tool, "reason": seed_error})

        reply_parts: list[str] = []
        used_tools: list[str] = []
        turn: Optional[Turn] = None
        failed = False

        try:
            async for item in run_agent(
                data.get("history", []),
                request.message,
                api_key=grant.api_key,
                provider=grant.provider,
                seed=agent_seed,
            ):
                if isinstance(item, Turn):
                    turn = item
                    continue

                event: AgentEvent = item
                if event.type == "text_delta":
                    reply_parts.append(event.text or "")
                    yield _sse({"type": "text_delta", "content": event.text})
                elif event.type == "tool_start":
                    used_tools.append(event.tool or "")
                    yield _sse({"type": "tool_start", "tool": event.tool, "arguments": event.arguments})
                elif event.type == "tool_result":
                    yield _sse({"type": "tool_result", "tool": event.tool, "result": event.result})
                elif event.type == "error":
                    failed = True
                    yield _sse({"type": "error", "error": event.error})
                elif event.type == "done":
                    pass
        except Exception:
            # Never leak internals to the client
            logger.error("Chat stream blew up", exc_info=True)
            yield _sse({"type": "error", "error": "Something went wrong on our side. Please try again."})
            failed = True

        if turn is not None and not failed:
            reply = turn.text or "".join(reply_parts)
            chips = _next_suggestions(data, request.message, reply, used_tools)
            await _save_session(session_id, data, turn)
            yield _sse({"type": "suggestions", "suggestions": chips})

        yield "data: [DONE]\n\n"

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # stop proxies from buffering
        },
    )


@app.post("/api/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(request: ChatRequest, http: Request):
    """
    Non-streaming chat. Same path, events just collected first.

    For UI, prefer /api/chat/stream -- the wait feels far shorter.
    """
    grant = await access.check(http)
    if not grant.allowed:
        return JSONResponse(status_code=429, content={"error": grant.reason, "remaining": 0})

    session_id, data = await _load_session(request.session_id)

    agent_seed = None
    if request.seed is not None:
        # No stream to report a rejection on here, so it stays in the log.
        agent_seed, _ = parse_seed(request.seed.tool, request.seed.arguments)

    parts: list[str] = []
    used_tools: list[str] = []
    turn: Optional[Turn] = None
    error: Optional[str] = None

    async for item in run_agent(
        data.get("history", []),
        request.message,
        api_key=grant.api_key,
        provider=grant.provider,
        seed=agent_seed,
    ):
        if isinstance(item, Turn):
            turn = item
        elif item.type == "text_delta":
            parts.append(item.text or "")
        elif item.type == "tool_start":
            used_tools.append(item.tool or "")
        elif item.type == "error":
            error = item.error

    reply = (turn.text if turn else "".join(parts)) or (error or "Sorry, something is off right now.")
    chips: list[str] = []
    if turn and not error:
        chips = _next_suggestions(data, request.message, reply, used_tools)
        await _save_session(session_id, data, turn)

    return ChatResponse(
        response=reply,
        flights=None,  # flights now arrive via tool_result events
        session_id=session_id,
        suggestions=chips,
    )


# ==============================================================================
# Catalogue
# ==============================================================================


class FacetOption(BaseModel):
    value: str = Field(..., description="Value to pass back in a tool seed")
    label: str = Field(..., description="Indonesian display label")


class BudgetBand(FacetOption):
    range_label: str = Field(..., description="Short range, e.g. '500rb–1jt'")
    min_idr: Optional[int] = Field(None, description="Lower bound of daily spend, IDR")
    max_idr: Optional[int] = Field(None, description="Upper bound of daily spend, IDR")


class Facets(BaseModel):
    travel_types: list[FacetOption]
    budget_bands: list[BudgetBand]
    seasons: list[FacetOption]
    regions: list[FacetOption]


class DestinationsResponse(BaseModel):
    destinations: list[dict[str, Any]] = Field(..., description="The curated destination set")
    facets: Facets = Field(..., description="Vocabularies behind the inspiration and budget surfaces")


@app.get("/api/destinations", response_model=DestinationsResponse, tags=["Catalogue"])
async def destinations():
    """
    The curated destination set plus the facet vocabularies behind it.

    Static for the lifetime of a deploy -- it is a Python literal, not a query.
    Cache it hard at the edge.
    """
    return DestinationsResponse(
        destinations=catalogue.destinations(),
        facets=Facets(**catalogue.facets()),
    )


# ==============================================================================
# Deals
# ==============================================================================


class Deal(BaseModel):
    city: str
    country: str
    iata: str
    region: str
    price_idr: int = Field(..., description="Cheapest fare found for departure_date")
    airline: Optional[str] = None
    stops: int = 0
    daily_cost_idr: Optional[float] = Field(None, description="Estimated daily spend on the ground")
    travel_types: list[str] = []


class DealsResponse(BaseModel):
    origin: str = Field(..., description="Origin actually served, which may differ from the one requested")
    requested_origin: Optional[str] = Field(None, description="What the caller asked for, if anything")
    updated_at: Optional[str] = Field(None, description="When these fares were fetched. None means the rail is cold.")
    departure_date: Optional[str] = Field(None, description="The date these fares are for")
    deals: list[Deal] = Field(default_factory=list)


@app.get("/api/deals", response_model=DealsResponse, tags=["Deals"])
async def deals(origin: Optional[str] = None):
    """
    Starting fares from one origin, served from cache.

    This endpoint never calls a flight provider. A cold or unwarmed origin
    returns an empty list with `updated_at: null`, and the client is expected to
    render that as "cek harga" rather than as a price.

    `origin` is clamped to the warmed set; `requested_origin` reports what was
    asked for so the UI can say "kami tampilkan dari Jakarta" instead of
    mislabelling the rail.
    """
    payload = await deals_cache.get(origin)
    return DealsResponse(**payload, requested_origin=origin)


# ==============================================================================
# Flight results
# ==============================================================================


class FlightOption(BaseModel):
    airline: str
    airline_code: str
    departure_time: str
    arrival_time: str
    origin: str
    destination: str
    price: float
    currency: str
    duration: str
    duration_minutes: Optional[int] = Field(None, description="Total minutes, for sorting")
    departure_bucket: Optional[str] = Field(
        None, description="pagi | siang | sore | malam — matches the departure_buckets facet"
    )
    stops: int


class AirlineFacet(BaseModel):
    code: str
    name: str
    count: int
    min_price: Optional[int] = None


class StopsFacet(BaseModel):
    value: int
    count: int


class RangeFacet(BaseModel):
    min: int
    max: int


class DurationFacet(BaseModel):
    min_minutes: int
    max_minutes: int


class DepartureBucketFacet(BaseModel):
    value: str = Field(..., description="pagi | siang | sore | malam")
    label: str
    count: int


class FlightFacets(BaseModel):
    """
    Filter vocabulary for one result set.

    Only values present in `flights` appear here, so a control built from this
    can never filter to nothing.
    """

    airlines: list[AirlineFacet] = []
    stops: list[StopsFacet] = []
    price: Optional[RangeFacet] = None
    duration: Optional[DurationFacet] = None
    departure_buckets: list[DepartureBucketFacet] = []


class FlightSearchResponse(BaseModel):
    origin: str = Field(..., description="Resolved IATA code, which may differ from what was typed")
    destination: str
    departure_date: str
    return_date: Optional[str] = None
    adults: int
    dates_returned: list[str] = Field(
        default_factory=list,
        description=(
            "Departure dates the provider actually returned, when they differ from "
            "the one requested. Empty in the normal case. Non-empty means the fares "
            "below are for another day and the UI must say so rather than relabel them."
        ),
    )
    currency: str = "IDR"
    total_found: int
    flights: list[FlightOption] = []
    facets: FlightFacets = FlightFacets()
    booking_links: dict[str, str] = Field(
        default_factory=dict, description="Handoff to whoever actually sells the seat"
    )
    cached_at: str
    cached: bool = Field(..., description="True when served without touching a provider")


@app.get("/api/flights/search", response_model=FlightSearchResponse, tags=["Flights"])
async def flight_search(
    http: Request,
    origin: str,
    destination: str,
    departure_date: str,
    return_date: Optional[str] = None,
    adults: int = 1,
):
    """
    Every flight a provider returned for one route and date, plus filter facets.

    Unlike `search_flights` (the agent tool), this is not truncated -- the tool's
    eight-result cap is a token budget, and a results page has no tokens to
    budget. See `MAX_RESULTS` in `tools/flights.py`.

    Unlike `/api/deals`, this *may* reach a provider on the request path, because
    a person typed this route and is waiting. What keeps that from being an open
    tap is a per-IP hourly limit on provider calls plus a 15-minute cache; a
    cached answer costs nothing and spends no allowance.

    `origin` and `destination` are forgiving -- city name, nickname, or IATA.
    They are resolved server-side, and the response reports what they resolved to.
    """
    if not (1 <= adults <= 9):
        return JSONResponse(status_code=422, content={"error": "adults must be between 1 and 9."})

    grant = await access.check_provider_call(http)
    if not grant.allowed:
        return JSONResponse(status_code=429, content={"error": grant.reason})

    result = await flight_results.search(
        origin=origin,
        destination=destination,
        departure_date=departure_date,
        return_date=return_date,
        adults=adults,
    )

    if not result.get("cached"):
        await access.consume_provider_call(http)

    if not result.get("ok"):
        # A route with no flights, a date in the past, a provider that timed out:
        # all normal outcomes the page renders as an explanation. 502 rather than
        # 500 because the fault is upstream, and never a 500, which would read as
        # a bug in this service.
        return JSONResponse(status_code=502, content={"error": result.get("error")})

    return FlightSearchResponse(**{k: v for k, v in result.items() if k != "ok"})


# ==============================================================================
# Suggestions
# ==============================================================================


class InitialSuggestionsResponse(BaseModel):
    suggestions: list[str] = Field(..., description="Opening prompts")


@app.get("/api/suggestions/initial", response_model=InitialSuggestionsResponse, tags=["Suggestions"])
async def initial_suggestions():
    return InitialSuggestionsResponse(suggestions=suggestions.get_initial_suggestions())


# ==============================================================================
# System
# ==============================================================================


@app.get("/api/health", response_model=HealthResponse, tags=["System"])
async def health():
    from src.config import AMADEUS_CONFIGURED

    store_health = await get_session_store().health_check()
    return HealthResponse(
        status="healthy" if is_configured() else "degraded",
        version="2.0.0",
        llm_provider=active_provider(),
        amadeus_configured=AMADEUS_CONFIGURED,
        model=resolve_model(),
        tools=tools.names(),
        session_store=store_health.get("type", "unknown"),
        knowledge_base=knowledge.stats(),
        access=access.quota_info(),
    )


@app.on_event("startup")
async def on_startup():
    logger.info("=" * 60)
    logger.info("Travel Companion API")
    logger.info("  LLM provider : %s (%s)", active_provider(), resolve_model())
    logger.info("  Key present  : %s", is_configured())
    logger.info("  Tools        : %s", ", ".join(tools.names()))
    health_info = await get_session_store().health_check()
    logger.info("  Session store: %s", health_info.get("type"))
    logger.info("=" * 60)


@app.on_event("shutdown")
async def on_shutdown():
    await close_session_store()
    logger.info("Travel Companion API stopped")

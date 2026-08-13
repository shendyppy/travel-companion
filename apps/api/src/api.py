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

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from src import tools
from src.agent import AgentEvent, Turn, run as run_agent
from src.config import LOG_FORMAT, LOG_LEVEL
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
    allow_headers=["Content-Type", "Accept"],
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
async def chat_stream(request: ChatRequest):
    """
    Streaming chat over Server-Sent Events.

    Event sequence:
        session      -> session id, sent first
        text_delta   -> text fragments, forwarded as the model produces them
        tool_start   -> the agent began calling a tool (drives UI status)
        tool_result  -> tool output (render as cards)
        suggestions  -> follow-up chips
        error        -> something failed; the stream still closes cleanly
        [DONE]       -> terminator
    """

    async def events() -> AsyncIterator[str]:
        session_id, data = await _load_session(request.session_id)
        yield _sse({"type": "session", "session_id": session_id})

        reply_parts: list[str] = []
        used_tools: list[str] = []
        turn: Optional[Turn] = None
        failed = False

        try:
            async for item in run_agent(data.get("history", []), request.message):
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
async def chat(request: ChatRequest):
    """
    Non-streaming chat. Same path, events just collected first.

    For UI, prefer /api/chat/stream -- the wait feels far shorter.
    """
    session_id, data = await _load_session(request.session_id)

    parts: list[str] = []
    used_tools: list[str] = []
    turn: Optional[Turn] = None
    error: Optional[str] = None

    async for item in run_agent(data.get("history", []), request.message):
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

"""
Agent loop.

This replaces the old `TravelAgent.send_message()` (~310 lines of nested if
branches). It is a standard tool-calling loop:

    send the conversation -> model either answers, or asks for tools
                          -> if tools: run them, append results, repeat
                          -> if it answers: done

Every "what does the user want" decision moved to the model, expressed as which
tool it calls. There is no regex picking through prose anymore.

The loop yields events rather than returning a string. Callers decide how to
present them: SSE to a browser, collected into one blob for the non-streaming
endpoint, or recorded for evaluation.
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Literal, Optional

from src import tools
from src.agent.persona import system_prompt
from src.llm import client

logger = logging.getLogger(__name__)

# How many times the model may ask for tools before it is forced to answer. Six
# covers the longest sensible chain (resolve_dates -> lookup_place x2 ->
# search_flights -> one correction) while still capping cost if the model gets
# stuck calling the same tool over and over.
MAX_ITERATIONS = 6

EventType = Literal["text_delta", "tool_start", "tool_result", "done", "error"]


@dataclass
class AgentEvent:
    type: EventType
    text: Optional[str] = None
    tool: Optional[str] = None
    arguments: Optional[dict[str, Any]] = None
    result: Optional[dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class Turn:
    """Outcome of one turn. `messages` is what needs persisting."""

    messages: list[dict[str, Any]] = field(default_factory=list)
    text: str = ""
    tools_used: list[str] = field(default_factory=list)


def build_messages(history: list[dict[str, Any]], user_message: str) -> list[dict[str, Any]]:
    """
    Assemble the full conversation to send to the model.

    The system prompt is rebuilt every turn because it carries today's date. If
    it were frozen into the stored history, a conversation running past midnight
    would resolve "tomorrow" from the wrong day.
    """
    return [
        {"role": "system", "content": system_prompt()},
        *history,
        {"role": "user", "content": user_message},
    ]


async def _run_tools(calls: list[client.ToolCall]) -> list[tuple[client.ToolCall, dict[str, Any]]]:
    """Run requested tools concurrently -- they are usually independent."""
    results = await asyncio.gather(*(tools.dispatch(c.name, c.arguments) for c in calls))
    return list(zip(calls, results))


async def run(
    history: list[dict[str, Any]],
    user_message: str,
    *,
    api_key: Optional[str] = None,
    provider: Optional[str] = None,
    max_iterations: int = MAX_ITERATIONS,
) -> AsyncIterator[AgentEvent | Turn]:
    """
    Run one conversational turn.

    Yields AgentEvent as things happen, then a single Turn at the end holding the
    messages to persist. Callers tell them apart with isinstance.

    Args:
        history: previous turns in OpenAI message format
        user_message: the new message from the user
        api_key: the user's own key (BYOK). None means use the server key.
        provider: the provider that key belongs to. None means the server default.
    """
    messages = build_messages(history, user_message)
    turn = Turn()
    tools_used: list[str] = []

    for iteration in range(max_iterations):
        collected_text: list[str] = []
        pending_calls: list[client.ToolCall] = []

        try:
            async for chunk in client.stream_completion(
                messages, tools=tools.schemas(), api_key=api_key, provider=provider
            ):
                if chunk.text:
                    collected_text.append(chunk.text)
                    yield AgentEvent(type="text_delta", text=chunk.text)
                if chunk.tool_calls:
                    pending_calls = chunk.tool_calls
        except client.LLMError as exc:
            # LLMError messages are already sanitised in the client, so they are
            # safe to surface
            logger.warning("Agent turn failed: %s", exc)
            yield AgentEvent(type="error", error=str(exc))
            return

        text = "".join(collected_text)

        if not pending_calls:
            turn.messages = [
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": text},
            ]
            turn.text = text
            turn.tools_used = tools_used
            yield AgentEvent(type="done", text=text)
            yield turn
            return

        # The model asked for tools. Record the request exactly as it came out --
        # providers reject tool messages that have no preceding tool_calls to
        # attach to.
        messages.append(
            {
                "role": "assistant",
                "content": text or None,
                "tool_calls": [
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {"name": call.name, "arguments": call.arguments},
                    }
                    for call in pending_calls
                ],
            }
        )

        for call in pending_calls:
            try:
                preview = json.loads(call.arguments or "{}")
            except json.JSONDecodeError:
                preview = {}
            tools_used.append(call.name)
            yield AgentEvent(type="tool_start", tool=call.name, arguments=preview)

        for call, result in await _run_tools(pending_calls):
            yield AgentEvent(type="tool_result", tool=call.name, result=result)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "name": call.name,
                    "content": json.dumps(result, ensure_ascii=False, default=str),
                }
            )

        logger.debug("Iteration %d done, %d tools called", iteration + 1, len(pending_calls))

    # Out of iterations. This is not a normal outcome, so it should not be dressed
    # up as a plausible answer -- the user deserves to know the agent gave up.
    logger.warning("Agent turn hit the %d iteration cap", max_iterations)
    yield AgentEvent(
        type="error",
        error="This needed too many steps. Try breaking it into smaller questions.",
    )

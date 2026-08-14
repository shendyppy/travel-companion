"""
Seeded tool calls.

A seed is a tool call chosen by the *client* rather than by the model. The
landing page's flight form already knows it wants `search_flights` with five
specific arguments; making it compose "cari penerbangan Jakarta ke Bali tanggal
20 September" and hoping the model reconstructs those arguments is a lossy
round-trip through natural language for information that was already structured.

So the form sends both: a human-readable `message`, and the structured call. The
loop runs the tool first and writes the call into the transcript in the shape the
model would have produced itself. From the model's point of view it asked for the
tool and got an answer; from the frontend's point of view the SSE events are
identical to any other tool call. Neither side needs a special case, and turn two
onwards has no idea a seed happened.

**This module is a trust boundary.** It is the only place where something outside
the process picks which internal function runs. Two gates, both mandatory:

1. An allowlist. Not every registered tool is seedable, and a tool becoming
   seedable should be a deliberate edit here rather than an automatic consequence
   of existing.
2. Schema validation via `tools.validate`, which rejects unknown properties as
   well as malformed ones.

Validation happens at the API boundary (`parse`), execution happens in the loop
(`execute`). Keeping those apart means the loop only ever receives a seed that
has already been checked, so there is no path where a caller reaches `execute`
with something unvalidated.
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass
from typing import Any, Optional

from src import tools

logger = logging.getLogger(__name__)

# Tools a client may seed. Deliberately narrow: these are the four the landing
# page's structured surfaces map onto, and they are all read-only lookups.
#
# `lookup_place`, `resolve_dates` and `search_knowledge` are omitted on purpose.
# They are plumbing the model uses to get to the tools above -- a client that
# wants them wants a different endpoint, not a seed.
SEEDABLE: frozenset[str] = frozenset(
    {
        "search_flights",
        "search_flights_flexible",
        "recommend_destinations",
        "get_destination_info",
    }
)


@dataclass(frozen=True)
class Seed:
    """A validated, ready-to-run tool call. Only `parse` may construct one."""

    tool: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class Prepared:
    """A seed that has run: its result, plus the messages to splice in."""

    tool: str
    arguments: dict[str, Any]
    result: dict[str, Any]
    messages: list[dict[str, Any]]


def parse(tool: Any, arguments: Any) -> tuple[Optional[Seed], Optional[str]]:
    """
    Validate a client-supplied seed. Returns `(seed, None)` or `(None, reason)`.

    Never raises. A bad seed is not an error condition worth failing a request
    over -- the message alone still produces a perfectly good answer, so the
    caller drops the seed and carries on.
    """
    if not isinstance(tool, str) or not tool:
        return None, "Seed tool must be a non-empty string."

    if tool not in SEEDABLE:
        # Distinguish "not seedable" from "does not exist" in the log, but not in
        # the response: the set of tools that exist is not a client's business.
        if tools.exists(tool):
            logger.warning("Rejected seed for non-seedable tool: %s", tool)
        else:
            logger.warning("Rejected seed for unknown tool: %s", tool)
        return None, f"Tool '{tool}' cannot be seeded."

    if arguments is None:
        arguments = {}
    if not isinstance(arguments, dict):
        return None, "Seed arguments must be an object."

    error = tools.validate(tool, arguments)
    if error:
        logger.warning("Rejected seed for %s: %s", tool, error)
        return None, error

    return Seed(tool=tool, arguments=dict(arguments)), None


async def execute(seed: Seed) -> Prepared:
    """
    Run a validated seed and build the transcript entries for it.

    `tools.dispatch` never raises, so a provider failure comes back as
    `{"ok": False, ...}` and gets written into the transcript like any other tool
    result. The model then explains the failure in its own words, which is
    exactly what it does when it picks a tool itself and the tool fails. A seed
    that could not find flights is not a broken request.
    """
    call_id = f"seed_{uuid.uuid4().hex[:12]}"
    result = await tools.dispatch(seed.tool, seed.arguments)

    messages = [
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": call_id,
                    "type": "function",
                    "function": {
                        "name": seed.tool,
                        "arguments": json.dumps(seed.arguments, ensure_ascii=False, default=str),
                    },
                }
            ],
        },
        {
            "role": "tool",
            "tool_call_id": call_id,
            "name": seed.tool,
            "content": json.dumps(result, ensure_ascii=False, default=str),
        },
    ]

    return Prepared(tool=seed.tool, arguments=seed.arguments, result=result, messages=messages)

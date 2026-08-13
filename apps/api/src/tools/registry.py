"""
Tool registry.

One place to collect tool schemas and run them. Adding a capability now means
adding one decorated function, not another branch in the middle of the
conversation pipeline.

Two properties are enforced here:

1. **Dispatch never raises into the agent loop.** Tool failures come back as
   structured results so the model can read them, explain them to the user, and
   try another route. A tool that explodes and kills the conversation is a far
   worse experience than one that reports "nothing found".

2. **Synchronous functions run off the event loop.** The provider modules use
   blocking `requests`. Calling those directly from the async path would stall
   the event loop and make other users queue behind them -- exactly the problem
   the previous implementation had.
"""

from __future__ import annotations

import asyncio
import inspect
import json
import logging
from dataclasses import dataclass
from typing import Any, Callable

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    parameters: dict[str, Any]
    fn: Callable[..., Any]


_REGISTRY: dict[str, Tool] = {}


def tool(*, name: str, description: str, parameters: dict[str, Any]):
    """
    Register a function as a tool.

    `parameters` is JSON Schema, written by hand rather than derived from type
    hints: the per-field descriptions are what the model reads to decide how to
    fill them in. That is where the quality lives, so it is worth stating
    explicitly.
    """

    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        if name in _REGISTRY:
            raise ValueError(f"Tool '{name}' registered twice")
        _REGISTRY[name] = Tool(name=name, description=description, parameters=parameters, fn=fn)
        return fn

    return decorator


def schemas() -> list[dict[str, Any]]:
    """Tool schemas in OpenAI format. LiteLLM translates these per provider."""
    return [
        {
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters,
            },
        }
        for t in _REGISTRY.values()
    ]


def names() -> list[str]:
    return list(_REGISTRY)


def _error(message: str, **extra: Any) -> dict[str, Any]:
    return {"ok": False, "error": message, **extra}


async def dispatch(name: str, arguments: str | dict[str, Any]) -> dict[str, Any]:
    """
    Run a tool. Always returns a dict, never raises.

    Args:
        name: tool the model asked for
        arguments: JSON string from the stream, or an already-parsed dict
    """
    entry = _REGISTRY.get(name)
    if entry is None:
        logger.warning("Model asked for unknown tool: %s", name)
        return _error(f"Tool '{name}' does not exist.", available=names())

    if isinstance(arguments, str):
        raw = arguments.strip() or "{}"
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            # Happens when the model emits truncated JSON. Report it plainly so
            # it can rebuild the arguments.
            logger.warning("Tool %s got invalid JSON arguments: %s", name, exc)
            return _error(f"Arguments for '{name}' were not valid JSON: {exc}")
    else:
        parsed = arguments

    if not isinstance(parsed, dict):
        return _error(f"Arguments for '{name}' must be a JSON object, got {type(parsed).__name__}.")

    try:
        if inspect.iscoroutinefunction(entry.fn):
            result = await entry.fn(**parsed)
        else:
            # Providers are blocking -- hand off to a thread so the event loop
            # stays free
            result = await asyncio.to_thread(lambda: entry.fn(**parsed))
    except TypeError as exc:
        # Usually arguments that don't match the signature
        logger.warning("Tool %s called with bad arguments: %s", name, exc)
        return _error(f"Arguments for '{name}' did not match: {exc}")
    except Exception as exc:
        logger.error("Tool %s failed: %s: %s", name, type(exc).__name__, exc, exc_info=True)
        return _error(f"Tool '{name}' failed to run: {type(exc).__name__}")

    if isinstance(result, dict) and "ok" in result:
        return result
    return {"ok": True, "data": result}

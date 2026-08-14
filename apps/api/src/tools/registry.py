"""
Tool registry.

One place to collect tool schemas and run them. Adding a capability now means
adding one decorated function, not another branch in the middle of the
conversation pipeline.

Three properties are enforced here:

1. **Dispatch never raises into the agent loop.** Tool failures come back as
   structured results so the model can read them, explain them to the user, and
   try another route. A tool that explodes and kills the conversation is a far
   worse experience than one that reports "nothing found".

2. **Synchronous functions run off the event loop.** The provider modules use
   blocking `requests`. Calling those directly from the async path would stall
   the event loop and make other users queue behind them -- exactly the problem
   the previous implementation had.

3. **Arguments can be validated before dispatch.** `dispatch` is deliberately
   forgiving -- a model that fills a tool in badly should get a readable error
   back and another go, not a rejection. But `seed` (see `agent/seed.py`) lets a
   *client* choose the tool and the arguments, and that is a different trust
   level entirely. `validate` is the strict gate for that path. Both paths share
   one schema, so the contract cannot drift between them.
"""

from __future__ import annotations

import asyncio
import inspect
import json
import logging
from dataclasses import dataclass
from typing import Any, Callable, Optional

import jsonschema

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


def exists(name: str) -> bool:
    return name in _REGISTRY


def validate(name: str, arguments: dict[str, Any]) -> Optional[str]:
    """
    Check arguments against a tool's registered schema. Returns an error string,
    or None when they are valid.

    Strict on purpose, and strict in a way `dispatch` is not: unknown properties
    are rejected as well as bad ones. The caller here is a client, not the model,
    so there is no reason to be generous -- an argument we do not recognise is
    either a bug in the frontend or someone probing, and both deserve the same
    flat refusal.

    Uses `jsonschema` rather than hand-rolled checks. The schemas already exist
    and this sits on a trust boundary; writing a second, weaker interpretation of
    them by hand is how holes get made.
    """
    entry = _REGISTRY.get(name)
    if entry is None:
        return f"Tool '{name}' does not exist."

    if not isinstance(arguments, dict):
        return f"Arguments for '{name}' must be an object, got {type(arguments).__name__}."

    schema = {**entry.parameters, "additionalProperties": False}
    try:
        jsonschema.validate(instance=arguments, schema=schema)
    except jsonschema.ValidationError as exc:
        location = ".".join(str(p) for p in exc.absolute_path)
        return f"{location}: {exc.message}" if location else exc.message
    except jsonschema.SchemaError as exc:
        # A broken schema is our bug, not the caller's. Fail closed.
        logger.error("Tool %s has an invalid schema: %s", name, exc)
        return f"Tool '{name}' has an invalid schema."

    return None


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

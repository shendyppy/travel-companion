"""
Access control: bring-your-own-key and demo quota.

Two modes, decided per request:

    no key supplied  -> server's key, tight per-IP quota
    key supplied     -> the user's key, no quota, cost sits with them

The hybrid exists because a portfolio piece has to be tryable. A visitor who
hits "enter your API key" before seeing anything work will simply leave. But an
open endpoint spending the owner's money is not viable either, so the free path
is deliberately small and there is a hard daily ceiling behind it.

## Rules for handling a user's key

These are the part most likely to go wrong quietly, so they are stated plainly:

1. **Never persisted.** Not in Redis, not in the session, not on disk. It lives
   for the duration of one request.
2. **Never logged.** litellm.turn_off_message_logging is set in llm/client.py,
   and provider errors are scrubbed before they reach the logger.
3. **Never echoed back**, including inside error messages. Provider errors often
   quote the request that produced them.
4. **Header only.** Query strings end up in access logs, proxy logs, and browser
   history.
5. **Never forwarded anywhere** except the LLM provider the user chose.
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from datetime import date
from typing import Optional

from fastapi import Request

from src.llm import client

logger = logging.getLogger(__name__)

API_KEY_HEADER = "X-LLM-Api-Key"
PROVIDER_HEADER = "X-LLM-Provider"

# Free messages per IP per day. Small enough that a shared link cannot run up a
# bill, large enough to actually try the thing.
DEMO_DAILY_LIMIT = int(os.getenv("DEMO_DAILY_LIMIT", "10"))

# Ceiling across all demo users combined. The per-IP limit alone does not bound
# spend -- IPs are cheap. This is the number the owner's wallet actually cares
# about, so failure here is a hard stop rather than a slowdown.
DEMO_GLOBAL_DAILY_LIMIT = int(os.getenv("DEMO_GLOBAL_DAILY_LIMIT", "500"))

# Shortest thing that could plausibly be a key. Catches empty headers and
# obvious junk before spending a network round trip to find out.
MIN_KEY_LENGTH = 16


@dataclass
class Access:
    """Decision for one request."""

    allowed: bool
    api_key: Optional[str]        # None means fall back to the server key
    provider: Optional[str]
    using_own_key: bool
    remaining: Optional[int]      # demo messages left today; None when BYOK
    reason: Optional[str] = None  # why it was refused


def _client_ip(request: Request) -> str:
    """
    Best-effort client IP.

    Cloud Run and Vercel both sit behind proxies, so the socket address is the
    proxy. X-Forwarded-For's first entry is the original client. It is spoofable
    -- which is exactly why the global ceiling above exists and does not depend
    on getting this right.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def extract_key(request: Request) -> tuple[Optional[str], Optional[str]]:
    """
    Pull the user's key and chosen provider out of the headers.

    Returns (key, provider). Both None when the user brought nothing.
    """
    raw = (request.headers.get(API_KEY_HEADER) or "").strip()
    if not raw or len(raw) < MIN_KEY_LENGTH:
        return None, None

    provider = (request.headers.get(PROVIDER_HEADER) or "").strip().lower() or None
    if provider and provider not in client._PROVIDERS:
        # Unknown provider name: ignore it rather than failing, and let the
        # default handle the key. Never echo the value back.
        logger.warning("Unknown provider requested in %s header", PROVIDER_HEADER)
        provider = None

    return raw, provider


# ==============================================================================
# Quota
# ==============================================================================


class _MemoryCounter:
    """Fallback when Redis is not configured. Per-process, so dev only."""

    def __init__(self) -> None:
        self._counts: dict[str, tuple[int, float]] = {}

    def incr(self, key: str, ttl: int) -> int:
        now = time.time()
        count, expires = self._counts.get(key, (0, now + ttl))
        if now > expires:
            count, expires = 0, now + ttl
        count += 1
        self._counts[key] = (count, expires)
        return count


_memory = _MemoryCounter()


async def _incr(key: str, ttl: int) -> int:
    """Increment a counter, returning the new value."""
    from src.session_store import get_session_store

    store = get_session_store()
    redis = getattr(store, "_redis", None) or getattr(store, "redis", None)

    if redis is None:
        return _memory.incr(key, ttl)

    try:
        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, ttl)
        return int(count)
    except Exception as exc:
        # A broken counter must not take the API down with it. Falling back to
        # the in-memory one degrades the limit rather than the service.
        logger.warning("Rate limit counter unavailable, using in-memory: %s", exc)
        return _memory.incr(key, ttl)


async def check(request: Request) -> Access:
    """
    Decide whether this request may proceed, and with whose key.

    Call once per chat request. Increments the demo counter as a side effect
    when the user did not bring a key.
    """
    key, provider = extract_key(request)

    if key:
        # The user pays. No quota, and nothing about the key is recorded.
        return Access(
            allowed=True,
            api_key=key,
            provider=provider,
            using_own_key=True,
            remaining=None,
        )

    if not client.is_configured():
        return Access(
            allowed=False, api_key=None, provider=None, using_own_key=False,
            remaining=0,
            reason="No demo key is configured on this server. Supply your own API key to continue.",
        )

    today = date.today().isoformat()
    ttl = 60 * 60 * 26  # a bit over a day, so the window rolls cleanly

    global_count = await _incr(f"quota:global:{today}", ttl)
    if global_count > DEMO_GLOBAL_DAILY_LIMIT:
        logger.warning("Global demo quota exhausted (%d)", global_count)
        return Access(
            allowed=False, api_key=None, provider=None, using_own_key=False,
            remaining=0,
            reason=(
                "The shared demo quota for today is used up. Supply your own API key "
                "to keep going -- it is never stored."
            ),
        )

    ip_count = await _incr(f"quota:ip:{_client_ip(request)}:{today}", ttl)
    remaining = max(0, DEMO_DAILY_LIMIT - ip_count)

    if ip_count > DEMO_DAILY_LIMIT:
        return Access(
            allowed=False, api_key=None, provider=None, using_own_key=False,
            remaining=0,
            reason=(
                f"You have used today's {DEMO_DAILY_LIMIT} free messages. Supply your own "
                f"API key to continue without limits -- it is never stored."
            ),
        )

    return Access(
        allowed=True,
        api_key=None,           # loop falls back to the server key
        provider=None,
        using_own_key=False,
        remaining=remaining,
    )


def quota_info() -> dict[str, object]:
    """Public description of the demo allowance, for the health endpoint."""
    return {
        "demo_daily_limit_per_ip": DEMO_DAILY_LIMIT,
        "demo_global_daily_limit": DEMO_GLOBAL_DAILY_LIMIT,
        "byok_header": API_KEY_HEADER,
        "byok_provider_header": PROVIDER_HEADER,
        "key_storage": "never stored; used for the duration of one request",
    }

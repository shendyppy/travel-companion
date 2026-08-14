"""
Cached fare rail for the landing page.

The rail shows a starting price to each curated destination from wherever the
visitor is. Doing that live would be 15 destinations x one provider call *per
page view*, which is not a rate-limit problem, it is a bill. So the rail is
served from a cache that a scheduled job warms, and the card says how old the
number is.

Three rules, and they are the whole module:

1. **A cold miss returns an empty list.** Never a placeholder, never an estimate,
   never last month's number relabelled. The frontend renders "cek harga" cards
   instead, which is a worse card and an honest one. The agent is built never to
   invent a price when a lookup fails; the landing page does not get an exemption.

2. **A public GET never triggers a provider call.** If it did, the endpoint would
   be a 15x amplifier for anyone with curl. Refreshes come from the warm script
   or from a background revalidation that can only fire when a cached entry
   already exists.

3. **Stale is served happily.** Fares move slowly enough that a six-hour-old
   number is useful, and `updated_at` travels with it so the card can say so.

The cache rides on the session store rather than opening a second Redis client:
it already handles Redis-or-in-memory, TTLs, and connection lifecycle. The cost
is that `clear_all()` would drop deals along with sessions, which is acceptable
for a cache that a scheduled job rebuilds.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from src import catalogue, tools
from src.session_store import get_session_store

logger = logging.getLogger(__name__)

# ==============================================================================
# Cost knobs. Changing any of these changes a bill -- they are together, and
# spelled out, so that is hard to do by accident.
#
#   one refresh  = len(ORIGINS) x ~len(destinations) provider calls
#                = 5 x 15 = 75 calls
#   per day      = 75 x (24 / (SOFT_TTL in hours)) = 75 x 4 = 300 calls
#
# Adding an origin adds 15 calls per refresh. Halving SOFT_TTL_SECONDS doubles
# everything. Neither is a small edit.
# ==============================================================================

ORIGINS: tuple[str, ...] = ("CGK", "SUB", "DPS", "KNO", "UPG")
DEFAULT_ORIGIN = "CGK"

# How far out to price. Far enough to be a plausible trip and to dodge the
# last-minute premium; close enough that the fare means something.
LOOKAHEAD_DAYS = 30

HARD_TTL_SECONDS = 12 * 60 * 60   # entry disappears; rail falls back to empty
SOFT_TTL_SECONDS = 6 * 60 * 60    # entry is served but revalidated behind the request

# Providers are shared with live chat traffic. A warm run must not starve it.
CONCURRENCY = 4

_CACHE_PREFIX = "deals:"

# Origins with a refresh in flight. Without this, four simultaneous stale reads
# would each kick off their own 15-call refresh.
_refreshing: set[str] = set()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _cache_key(origin: str) -> str:
    return f"{_CACHE_PREFIX}{origin.upper()}"


def normalise_origin(origin: Optional[str]) -> str:
    """
    Clamp a requested origin to one we actually warm.

    Serving an un-warmed origin would mean either a cold miss on every request or
    a provider call on every request. Falling back to Jakarta is the honest third
    option, and the response says which origin it is really for so the frontend
    can tell the user rather than quietly mislabel the rail.
    """
    if not origin:
        return DEFAULT_ORIGIN
    code = origin.strip().upper()
    return code if code in ORIGINS else DEFAULT_ORIGIN


def _empty(origin: str) -> dict[str, Any]:
    return {"origin": origin, "updated_at": None, "departure_date": None, "deals": []}


async def _price_one(
    origin: str,
    destination: dict[str, Any],
    departure_date: str,
    limiter: asyncio.Semaphore,
) -> Optional[dict[str, Any]]:
    """One destination's starting fare, or None if there isn't one to report."""
    iata = destination.get("iata")
    if not iata or iata == origin:
        return None

    async with limiter:
        result = await tools.dispatch(
            "search_flights",
            {"origin": origin, "destination": iata, "departure_date": departure_date, "adults": 1},
        )

    if not result.get("ok"):
        logger.info("No fare for %s->%s: %s", origin, iata, result.get("error"))
        return None

    cheapest = (result.get("data") or {}).get("cheapest")
    if not cheapest or not cheapest.get("price"):
        return None

    return {
        "city": destination["name"],
        "country": destination["country"],
        "iata": iata,
        "region": destination["region"],
        "price_idr": round(float(cheapest["price"])),
        "airline": cheapest.get("airline"),
        "stops": cheapest.get("stops", 0),
        "daily_cost_idr": destination.get("estimated_daily_total_idr"),
        "travel_types": destination.get("travel_types", []),
    }


async def refresh(origin: str) -> dict[str, Any]:
    """
    Price every curated destination from one origin and cache the result.

    Expensive by construction -- roughly one provider call per destination. Call
    it from the warm script or from background revalidation, never from a
    request path.
    """
    origin = normalise_origin(origin)
    departure_date = (_now() + timedelta(days=LOOKAHEAD_DAYS)).strftime("%Y-%m-%d")
    limiter = asyncio.Semaphore(CONCURRENCY)

    destinations = catalogue.destinations()
    priced = await asyncio.gather(
        *(_price_one(origin, d, departure_date, limiter) for d in destinations)
    )
    deals = sorted((d for d in priced if d), key=lambda d: d["price_idr"])

    payload = {
        "origin": origin,
        "updated_at": _now().isoformat(),
        "departure_date": departure_date,
        "deals": deals,
    }

    if deals:
        await get_session_store().set(_cache_key(origin), payload, ttl=HARD_TTL_SECONDS)
        logger.info("Warmed deals for %s: %d of %d destinations priced", origin, len(deals), len(destinations))
    else:
        # Caching an empty rail would pin the fallback in place for twelve hours
        # over what is usually a transient provider outage.
        logger.warning("Deals refresh for %s priced nothing; leaving cache untouched", origin)

    return payload


def _age_seconds(payload: dict[str, Any]) -> Optional[float]:
    stamp = payload.get("updated_at")
    if not stamp:
        return None
    try:
        return (_now() - datetime.fromisoformat(stamp)).total_seconds()
    except ValueError:
        return None


async def _revalidate(origin: str) -> None:
    try:
        await refresh(origin)
    except Exception:
        logger.error("Background deals refresh for %s failed", origin, exc_info=True)
    finally:
        _refreshing.discard(origin)


async def get(origin: Optional[str] = None) -> dict[str, Any]:
    """
    Read the rail for an origin. Never calls a provider on the request path.

    A stale-but-present entry is returned as-is and revalidated in the
    background; the caller gets its answer immediately either way.
    """
    origin = normalise_origin(origin)
    cached = await get_session_store().get(_cache_key(origin))

    if not cached or not cached.get("deals"):
        return _empty(origin)

    age = _age_seconds(cached)
    if age is not None and age > SOFT_TTL_SECONDS and origin not in _refreshing:
        _refreshing.add(origin)
        asyncio.create_task(_revalidate(origin))

    return cached

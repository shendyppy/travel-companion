"""
Flight results for the /flights page.

This is the second consumer of `tools.flights.search_and_normalize`, and it
differs from the first in exactly two ways, both deliberate:

1. **It does not truncate.** The tool caps at eight because its results are
   billed as model context. A results page has no such constraint, so it renders
   everything the provider returned.

2. **It may call a provider on the request path.** `deals.py` never does -- that
   endpoint is a public GET whose result nobody asked for specifically, so a live
   call there would make it a 15x amplifier for anyone with curl. Here a human
   typed a route and a date and is waiting for the answer, so refusing to look it
   up would defeat the endpoint. The protection is therefore a rate limit
   (`access.check_provider_call`) plus this cache, not a blanket refusal.

Facets are computed here rather than in the browser. The filter rail needs to
know which airlines are present and what the price floor is, and deriving that
client-side would put a second copy of the pricing logic somewhere it could
quietly disagree with the first.
"""

from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime, timezone
from typing import Any, Optional

from src.providers import booking_links
from src.session_store import get_session_store
from src.tools.flights import search_and_normalize

logger = logging.getLogger(__name__)

# Fares move slowly; a quarter of an hour is long enough to absorb a user
# refreshing, sorting, and filtering without re-billing the provider, and short
# enough that the number on screen is still one they could book.
CACHE_TTL_SECONDS = 15 * 60

_CACHE_PREFIX = "flights:"

# Indonesian time-of-day bands, which are not even quarters -- "pagi" runs long
# and "malam" wraps midnight, because that is how people describe flights.
_BUCKET_LABELS = {
    "pagi": "Pagi (05:00–10:59)",
    "siang": "Siang (11:00–14:59)",
    "sore": "Sore (15:00–18:59)",
    "malam": "Malam (19:00–04:59)",
}
_BUCKET_ORDER = ("pagi", "siang", "sore", "malam")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _cache_key(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: Optional[str],
    adults: int,
) -> str:
    # The resolved IATA codes are not known until after the search, so the key is
    # built from what the caller typed. "Jakarta" and "CGK" therefore occupy two
    # entries for the same route -- a duplicate lookup, not a wrong answer, and
    # cheaper than resolving the route twice on every cache read.
    return (
        f"{_CACHE_PREFIX}{origin.strip().upper()}:{destination.strip().upper()}"
        f":{departure_date}:{return_date or '-'}:{adults}"
    )


def _hour_of(value: str) -> Optional[int]:
    """
    Departure hour from a timestamp, whichever provider produced it.

    Amadeus gives a full ISO datetime, Google Flights sometimes a bare clock
    time. Both end in `HH:MM`, which is all this needs.
    """
    if not value:
        return None

    time_part = value.split("T", 1)[1] if "T" in value else value
    match = re.match(r"\s*(\d{1,2}):(\d{2})", time_part)
    if not match:
        return None

    hour = int(match.group(1))
    return hour if 0 <= hour < 24 else None


def _bucket(hour: int) -> str:
    if 5 <= hour < 11:
        return "pagi"
    if 11 <= hour < 15:
        return "siang"
    if 15 <= hour < 19:
        return "sore"
    return "malam"


def build_facets(flights: list[dict[str, Any]]) -> dict[str, Any]:
    """
    The filter vocabulary for one result set.

    Only values actually present get a facet. An airline checkbox that filters to
    nothing is a control that does not work, and the page has a rule against
    those.
    """
    airlines: dict[str, dict[str, Any]] = {}
    stops: dict[int, int] = {}
    buckets: dict[str, int] = {}
    prices: list[float] = []
    durations: list[int] = []

    for flight in flights:
        code = flight.get("airline_code") or "XX"
        entry = airlines.setdefault(
            code,
            {"code": code, "name": flight.get("airline") or code, "count": 0, "min_price": None},
        )
        entry["count"] += 1

        price = flight.get("price")
        if price:
            prices.append(float(price))
            if entry["min_price"] is None or price < entry["min_price"]:
                entry["min_price"] = round(float(price))

        stop_count = int(flight.get("stops") or 0)
        stops[stop_count] = stops.get(stop_count, 0) + 1

        minutes = flight.get("duration_minutes")
        if minutes:
            durations.append(int(minutes))

        hour = _hour_of(flight.get("departure_time") or "")
        if hour is not None:
            band = _bucket(hour)
            buckets[band] = buckets.get(band, 0) + 1

    return {
        # Most-served airline first: the rail is scanned top-down and the airline
        # with twelve options is more use at the top than one with a single seat.
        "airlines": sorted(airlines.values(), key=lambda a: (-a["count"], a["name"])),
        "stops": [{"value": value, "count": stops[value]} for value in sorted(stops)],
        "price": (
            {"min": round(min(prices)), "max": round(max(prices))} if prices else None
        ),
        "duration": (
            {"min_minutes": min(durations), "max_minutes": max(durations)} if durations else None
        ),
        "departure_buckets": [
            {"value": band, "label": _BUCKET_LABELS[band], "count": buckets[band]}
            for band in _BUCKET_ORDER
            if band in buckets
        ],
    }


def _with_bucket(flight: dict[str, Any]) -> dict[str, Any]:
    """
    Tag a flight with the time-of-day band it belongs to.

    Sent rather than recomputed in the browser on purpose: the filter checkbox and
    the flight it hides have to agree about where "sore" ends, and a second
    implementation of these boundaries in TypeScript is a drift waiting to
    happen. The tool's copy of a flight does not carry this -- a model does not
    need a precomputed bucket to reason about 17:40.
    """
    hour = _hour_of(flight.get("departure_time") or "")
    return {**flight, "departure_bucket": _bucket(hour) if hour is not None else None}


def _dates_returned(flights: list[dict[str, Any]], asked_for: str) -> list[str]:
    """
    Departure dates the provider actually sent back, when they are not the one
    we asked for.

    This exists because a provider can and does answer the wrong question. The
    RapidAPI Google Flights upstream has been observed returning today's
    schedule for a request three weeks out -- the `outboundDate` parameter goes
    out correctly and comes back ignored.

    Rendering those fares under the requested date would put a number on screen
    that is real, current, and about a different day. The project's rule is that
    a price is never invented; a price silently relabelled is the same failure
    wearing better clothes. So the mismatch travels with the payload and the page
    says it out loud.
    """
    seen = {
        (flight.get("departure_time") or "").split("T", 1)[0]
        for flight in flights
        if flight.get("departure_time")
    }
    return sorted(date for date in seen if date and date != asked_for)


def _payload(
    found_origin: str,
    found_destination: str,
    departure_date: str,
    return_date: Optional[str],
    adults: int,
    flights: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "origin": found_origin,
        "destination": found_destination,
        "departure_date": departure_date,
        "return_date": return_date,
        "adults": adults,
        "dates_returned": _dates_returned(flights, departure_date),
        "currency": (flights[0].get("currency") if flights else None) or "IDR",
        "total_found": len(flights),
        "flights": [_with_bucket(f) for f in flights],
        "facets": build_facets(flights),
        # The product does not sell seats, so this is the handoff -- and it is
        # generated whether or not any fares came back, because "we found nothing,
        # try Traveloka" is still a useful answer.
        "booking_links": booking_links.get_booking_links_dict(
            origin=found_origin,
            destination=found_destination,
            departure_date=departure_date,
            passengers=adults,
            return_date=return_date,
        ),
        "cached_at": _now().isoformat(),
    }


async def search(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: Optional[str] = None,
    adults: int = 1,
) -> dict[str, Any]:
    """
    Full result set for one route and date, from cache when possible.

    Raises nothing. A provider failure comes back as `{"ok": False, "error": ...}`
    so the page can render the reason instead of a blank list -- failure states
    are a normal outcome here, not an exception.
    """
    key = _cache_key(origin, destination, departure_date, return_date, adults)
    store = get_session_store()

    cached = await store.get(key)
    if cached:
        return {"ok": True, "cached": True, **cached}

    # `search_and_normalize` goes through blocking `requests`. Calling it inline
    # would stall the event loop and queue every other user behind this one --
    # the exact bug the streaming rewrite fixed, and easy to reintroduce here.
    found = await asyncio.to_thread(
        search_and_normalize, origin, destination, departure_date, return_date, adults
    )

    if not found.ok:
        # Deliberately not cached. Pinning a provider timeout in place for fifteen
        # minutes turns a blip into an outage, and the retry costs one call.
        logger.info("Flight search %s->%s failed: %s", origin, destination, found.error)
        return {"ok": False, "cached": False, "error": found.error}

    payload = _payload(
        found.origin or origin.upper(),
        found.destination or destination.upper(),
        departure_date,
        return_date,
        adults,
        found.flights,
    )

    # An empty-but-successful search *is* cached, unlike in `deals.py`. There an
    # empty rail meant fifteen destinations failed at once, which is an outage;
    # here it means the provider answered clearly that nobody flies this route on
    # this date, and asking again in a minute will not change that.
    await store.set(key, payload, ttl=CACHE_TTL_SECONDS)

    return {"ok": True, "cached": False, **payload}

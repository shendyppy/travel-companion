"""
Flight tools.

Besides calling the providers, this module unifies the shape of what comes back.
`search_flights` in flight_api.py returns raw payloads whose structure differs
between Google Flights and Amadeus depending on which one answered -- something
the caller neither knows nor should care about. That normalisation used to sit
in api.py; it lives here now so the tool has a single contract.

`search_and_normalize` is the shared half, and it exists because there are now
two consumers with genuinely different needs: the tool below, whose results are
fed to a language model, and `src/flight_results.py`, which serves the /flights
results page. Same provider call, same normalisation, different ceilings -- see
MAX_RESULTS.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Optional

from src.providers import flight_api, places
from src.tools.registry import tool

logger = logging.getLogger(__name__)

# How many flights the *tool* returns. This is a token budget, not a UI decision:
# every result here is serialised into the model's context and paid for on both
# the prompt and the reasoning side, so eight is roughly where more options stop
# improving the answer and start costing money.
#
# The results page has no such constraint and deliberately does not use this --
# it calls `search_and_normalize` directly and renders everything the provider
# returned. If you ever find yourself raising this to make the page show more
# flights, the page is calling the wrong function.
MAX_RESULTS = 8


def _normalize(raw: dict[str, Any], origin: str, destination: str) -> Optional[dict[str, Any]]:
    """
    Flatten one flight record into a single shape.

    Amadeus returns a nested structure (`itineraries` -> `segments`); Google
    Flights returns a flat one. The presence of `itineraries` tells them apart.
    """
    try:
        if "itineraries" in raw:
            return _normalize_amadeus(raw, origin, destination)
        return _normalize_flat(raw, origin, destination)
    except Exception as exc:
        logger.warning("Could not normalise flight record: %s", exc)
        return None


_DURATION_UNITS = {"d": 24 * 60, "h": 60, "m": 1}


def _duration_minutes(value: str) -> Optional[int]:
    """
    Total minutes from either duration format we produce.

    Amadeus hands over ISO 8601 ("PT1H50M") and Google Flights a human string
    ("1h 50m"), and `format_duration` turns the former into the latter -- so both
    reduce to the same digit-then-unit scan once the ISO prefix is dropped.
    Returns None when there is nothing parseable, because a missing duration must
    sort and filter differently from a zero-minute one.
    """
    if not value:
        return None

    text = value.strip().lower()
    if text.startswith("p"):
        # ISO 8601 splits at the T, and it has to be split rather than scanned
        # whole: "m" means months before the T and minutes after it, so P1DT2H30M
        # is a day plus two and a half hours, not thirty months.
        date_part, _, time_part = text[1:].partition("t")
    else:
        date_part, time_part = "", text

    total = sum(int(amount) * _DURATION_UNITS["d"] for amount in re.findall(r"(\d+)\s*d", date_part))
    total += sum(
        int(amount) * _DURATION_UNITS[unit]
        for amount, unit in re.findall(r"(\d+)\s*([dhm])", time_part)
    )
    return total or None


def _normalize_flat(raw: dict[str, Any], origin: str, destination: str) -> dict[str, Any]:
    duration = raw.get("duration") or ""
    return {
        "airline": raw.get("airline") or "Unknown",
        "airline_code": raw.get("airline_code") or "XX",
        "departure_time": raw.get("departure_time") or "",
        "arrival_time": raw.get("arrival_time") or "",
        "origin": raw.get("origin") or origin,
        "destination": raw.get("destination") or destination,
        "price": float(raw.get("price") or 0),
        "currency": raw.get("currency") or "IDR",
        "duration": duration,
        "duration_minutes": _duration_minutes(duration),
        "stops": int(raw.get("stops") or 0),
    }


def _normalize_amadeus(raw: dict[str, Any], origin: str, destination: str) -> Optional[dict[str, Any]]:
    itineraries = raw.get("itineraries") or []
    if not itineraries:
        return None
    segments = itineraries[0].get("segments") or []
    if not segments:
        return None

    price_info = raw.get("price") or {}
    price = float(price_info.get("grandTotal") or 0)
    currency = price_info.get("currency") or "EUR"
    if currency != "IDR":
        rate = flight_api.get_exchange_rate(currency, "IDR")
        if rate:
            price, currency = price * rate, "IDR"

    first, last = segments[0], segments[-1]
    airline_code = (first.get("operating") or {}).get("carrierCode") or first.get("carrierCode") or "XX"
    departure = first.get("departure") or {}
    arrival = last.get("arrival") or {}
    raw_duration = itineraries[0].get("duration") or ""

    return {
        "airline": flight_api.get_airline_name_safe(airline_code, origin, destination),
        "airline_code": airline_code,
        "departure_time": departure.get("at") or "",
        "arrival_time": arrival.get("at") or "",
        "origin": departure.get("iataCode") or origin,
        "destination": arrival.get("iataCode") or destination,
        "price": round(price),
        "currency": currency,
        "duration": flight_api.format_duration(raw_duration),
        "duration_minutes": _duration_minutes(raw_duration),
        "stops": len(segments) - 1,
    }


def _to_iata(value: str, label: str) -> tuple[Optional[str], Optional[str]]:
    """Turn whatever the model passed into an IATA code. Returns (code, error)."""
    code = places.primary_iata(value)
    if code:
        return code, None
    return None, f"No airport found for {label} '{value}'. Try lookup_place first."


@dataclass
class FlightSearch:
    """
    One provider round trip: resolved, normalised, sorted cheapest-first, uncapped.

    Uncapped is the point. Whoever asked decides how many of these they can
    afford to carry -- the tool below truncates to MAX_RESULTS because its
    results are billed as model context; the results page keeps all of them.
    """

    ok: bool
    flights: list[dict[str, Any]] = field(default_factory=list)
    origin: Optional[str] = None
    destination: Optional[str] = None
    error: Optional[str] = None


def search_and_normalize(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: Optional[str] = None,
    adults: int = 1,
) -> FlightSearch:
    """
    Resolve the route, call the provider, and flatten what comes back.

    The single path to flight data. Anything that needs flights calls this rather
    than `flight_api` directly, so IATA resolution, the Amadeus/Google shape
    difference, and cheapest-first ordering are decided in exactly one place.
    """
    origin_code, err = _to_iata(origin, "origin")
    if err:
        return FlightSearch(ok=False, error=err)

    dest_code, err = _to_iata(destination, "destination")
    if err:
        return FlightSearch(ok=False, error=err)

    if origin_code == dest_code:
        return FlightSearch(ok=False, error="Origin and destination resolve to the same airport.")

    result = flight_api.search_flights(
        origin=origin_code,
        destination=dest_code,
        departure_date=departure_date,
        adults=adults,
        return_date=return_date,
        trip_type="return" if return_date else "oneway",
    )

    if not result.get("success"):
        return FlightSearch(
            ok=False,
            origin=origin_code,
            destination=dest_code,
            error=result.get("error") or "Flight search failed.",
        )

    raw_items = result.get("data") or []
    flights = [f for f in (_normalize(r, origin_code, dest_code) for r in raw_items) if f]
    flights.sort(key=lambda f: f["price"] or float("inf"))

    return FlightSearch(ok=True, flights=flights, origin=origin_code, destination=dest_code)


@tool(
    name="search_flights",
    description=(
        "Search real flights for one specific departure date. Use this once the user "
        "has given a concrete date. If the date is still relative ('next week', 'long "
        "weekend'), call resolve_dates first. Returns flights with prices, cheapest first."
    ),
    parameters={
        "type": "object",
        "properties": {
            "origin": {
                "type": "string",
                "description": "Origin city or airport. City name ('Jakarta') or IATA code ('CGK').",
            },
            "destination": {
                "type": "string",
                "description": "Destination city or airport. City name ('Bali') or IATA code ('DPS').",
            },
            "departure_date": {
                "type": "string",
                "description": "Departure date in YYYY-MM-DD format.",
            },
            "return_date": {
                "type": "string",
                "description": "Return date in YYYY-MM-DD format. Omit for one-way.",
            },
            "adults": {
                "type": "integer",
                "description": "Number of adult passengers. Defaults to 1.",
                "minimum": 1,
                "maximum": 9,
            },
        },
        "required": ["origin", "destination", "departure_date"],
    },
)
def search_flights(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: Optional[str] = None,
    adults: int = 1,
) -> dict[str, Any]:
    found = search_and_normalize(origin, destination, departure_date, return_date, adults)

    if not found.ok:
        return {"ok": False, "error": found.error}

    if not found.flights:
        return {
            "ok": True,
            "data": {
                "flights": [],
                "note": "No flights found for that route and date.",
            },
        }

    return {
        "ok": True,
        "data": {
            "origin": found.origin,
            "destination": found.destination,
            "departure_date": departure_date,
            "return_date": return_date,
            "adults": adults,
            # `total_found` counts everything the provider returned, while
            # `flights` is truncated -- the model needs to know it is looking at
            # a sample so it can say "ada 23 pilihan" instead of "ada 8".
            "total_found": len(found.flights),
            "cheapest": found.flights[0],
            "flights": found.flights[:MAX_RESULTS],
        },
    }


@tool(
    name="search_flights_flexible",
    description=(
        "Find the cheapest flight across a date range. Use this when the user is "
        "flexible about dates ('whenever is cheapest next month'). Slower than "
        "search_flights because it probes several dates, so keep the range under "
        "two weeks."
    ),
    parameters={
        "type": "object",
        "properties": {
            "origin": {"type": "string", "description": "Origin city or airport."},
            "destination": {"type": "string", "description": "Destination city or airport."},
            "start_date": {"type": "string", "description": "Start of range, YYYY-MM-DD."},
            "end_date": {"type": "string", "description": "End of range, YYYY-MM-DD."},
            "adults": {
                "type": "integer",
                "description": "Number of adult passengers. Defaults to 1.",
                "minimum": 1,
                "maximum": 9,
            },
        },
        "required": ["origin", "destination", "start_date", "end_date"],
    },
)
def search_flights_flexible(
    origin: str,
    destination: str,
    start_date: str,
    end_date: str,
    adults: int = 1,
) -> dict[str, Any]:
    origin_code, err = _to_iata(origin, "origin")
    if err:
        return {"ok": False, "error": err}
    dest_code, err = _to_iata(destination, "destination")
    if err:
        return {"ok": False, "error": err}

    result = flight_api.search_flights_in_date_range(
        origin=origin_code,
        destination=dest_code,
        start_date=start_date,
        end_date=end_date,
        adults=adults,
        max_searches=7,  # capped: each date costs one API call
    )

    if not result.get("success"):
        return {"ok": False, "error": result.get("error") or "Date range search failed."}

    return {"ok": True, "data": result}

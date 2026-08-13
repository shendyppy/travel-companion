"""
Flight tools.

Besides calling the providers, this module unifies the shape of what comes back.
`search_flights` in flight_api.py returns raw payloads whose structure differs
between Google Flights and Amadeus depending on which one answered -- something
the caller neither knows nor should care about. That normalisation used to sit
in api.py; it lives here now so the tool has a single contract.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from src.providers import flight_api, places
from src.tools.registry import tool

logger = logging.getLogger(__name__)

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


def _normalize_flat(raw: dict[str, Any], origin: str, destination: str) -> dict[str, Any]:
    return {
        "airline": raw.get("airline") or "Unknown",
        "airline_code": raw.get("airline_code") or "XX",
        "departure_time": raw.get("departure_time") or "",
        "arrival_time": raw.get("arrival_time") or "",
        "origin": raw.get("origin") or origin,
        "destination": raw.get("destination") or destination,
        "price": float(raw.get("price") or 0),
        "currency": raw.get("currency") or "IDR",
        "duration": raw.get("duration") or "",
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

    return {
        "airline": flight_api.get_airline_name_safe(airline_code, origin, destination),
        "airline_code": airline_code,
        "departure_time": departure.get("at") or "",
        "arrival_time": arrival.get("at") or "",
        "origin": departure.get("iataCode") or origin,
        "destination": arrival.get("iataCode") or destination,
        "price": round(price),
        "currency": currency,
        "duration": flight_api.format_duration(itineraries[0].get("duration") or ""),
        "stops": len(segments) - 1,
    }


def _to_iata(value: str, label: str) -> tuple[Optional[str], Optional[str]]:
    """Turn whatever the model passed into an IATA code. Returns (code, error)."""
    code = places.primary_iata(value)
    if code:
        return code, None
    return None, f"No airport found for {label} '{value}'. Try lookup_place first."


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
    origin_code, err = _to_iata(origin, "origin")
    if err:
        return {"ok": False, "error": err}
    dest_code, err = _to_iata(destination, "destination")
    if err:
        return {"ok": False, "error": err}

    if origin_code == dest_code:
        return {"ok": False, "error": "Origin and destination resolve to the same airport."}

    result = flight_api.search_flights(
        origin=origin_code,
        destination=dest_code,
        departure_date=departure_date,
        adults=adults,
        return_date=return_date,
        trip_type="return" if return_date else "oneway",
    )

    if not result.get("success"):
        return {"ok": False, "error": result.get("error") or "Flight search failed."}

    raw_items = result.get("data") or []
    flights = [f for f in (_normalize(r, origin_code, dest_code) for r in raw_items) if f]
    flights.sort(key=lambda f: f["price"] or float("inf"))

    if not flights:
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
            "origin": origin_code,
            "destination": dest_code,
            "departure_date": departure_date,
            "return_date": return_date,
            "adults": adults,
            "total_found": len(flights),
            "cheapest": flights[0],
            "flights": flights[:MAX_RESULTS],
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

"""
Destination tools.

Wraps the curated destination data (`destination_data.py`) and seasonal knowledge
(`season_intelligence.py`) as tools.

Why this is still worth having when the model already "knows" about Bali: the
data here carries realistic daily costs in rupiah for Indonesian travellers, and
the reasoning for why a place makes sense on a given budget. Those are exactly
the things a model invents when left to itself.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from src.providers import destination_data, season_intelligence
from src.providers.destination_data import BudgetCategory, Season, TravelType
from src.providers.places import primary_iata
from src.tools.registry import tool

logger = logging.getLogger(__name__)


def _serialize(dest: destination_data.Destination) -> dict[str, Any]:
    daily = dest.estimated_daily_cost or {}
    return {
        "name": dest.name,
        "country": dest.country,
        "region": dest.region,
        "description": dest.description,
        "budget_category": dest.budget_category.value,
        "travel_types": [t.value for t in dest.travel_types],
        "best_season": dest.best_season.value,
        "estimated_daily_cost_idr": daily,
        "estimated_daily_total_idr": sum(daily.values()) if daily else None,
        "highlights": dest.highlights,
        "why_budget_friendly": dest.why_budget_friendly,
    }


def _coerce(enum_cls, value: str | None, field: str) -> tuple[Any, Optional[str]]:
    if value is None:
        return None, None
    try:
        return enum_cls(value.strip().lower()), None
    except ValueError:
        allowed = ", ".join(m.value for m in enum_cls)
        return None, f"'{value}' is not a valid {field}. Allowed values: {allowed}."


@tool(
    name="recommend_destinations",
    description=(
        "Recommend destinations by budget, trip style, and season. Use this when the "
        "user has not settled on a destination and is looking for ideas. Every filter "
        "is optional -- the more you supply, the sharper the match."
    ),
    parameters={
        "type": "object",
        "properties": {
            "budget": {
                "type": "string",
                "enum": [m.value for m in BudgetCategory],
                "description": (
                    "Daily budget band: budget (under 500k IDR), affordable (500k-1M), "
                    "moderate (1M-2M), splurge (over 2M)."
                ),
            },
            "travel_types": {
                "type": "array",
                "items": {"type": "string", "enum": [m.value for m in TravelType]},
                "description": "Trip styles the user is after, e.g. ['beach', 'cultural'].",
            },
            "region": {
                "type": "string",
                "enum": ["domestic", "international"],
                "description": "Domestic (within Indonesia) or international.",
            },
            "season": {
                "type": "string",
                "enum": [m.value for m in Season],
                "description": "Preferred season, if the user mentioned one.",
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum recommendations. Defaults to 5.",
                "minimum": 1,
                "maximum": 10,
            },
        },
        "required": [],
    },
)
def recommend_destinations(
    budget: Optional[str] = None,
    travel_types: Optional[list[str]] = None,
    region: Optional[str] = None,
    season: Optional[str] = None,
    max_results: int = 5,
) -> dict[str, Any]:
    budget_enum, err = _coerce(BudgetCategory, budget, "budget")
    if err:
        return {"ok": False, "error": err}
    season_enum, err = _coerce(Season, season, "season")
    if err:
        return {"ok": False, "error": err}

    type_enums: list[TravelType] = []
    for raw in travel_types or []:
        parsed, err = _coerce(TravelType, raw, "travel type")
        if err:
            return {"ok": False, "error": err}
        if parsed:
            type_enums.append(parsed)

    matches = destination_data.recommend_destinations(
        budget=budget_enum,
        travel_types=type_enums or None,
        region=region,
        season=season_enum,
        max_results=max_results,
    )

    if not matches:
        return {
            "ok": True,
            "data": {
                "destinations": [],
                "note": "Nothing matches that combination of filters. Try relaxing one of them.",
            },
        }

    return {
        "ok": True,
        "data": {
            "filters": {
                "budget": budget,
                "travel_types": travel_types,
                "region": region,
                "season": season,
            },
            "destinations": [_serialize(d) for d in matches],
        },
    }


@tool(
    name="get_destination_info",
    description=(
        "Get details for one destination: daily cost breakdown, highlights, and "
        "seasonal information (when it is busy, when it is cheap, what the weather "
        "does). Use this when the user asks about a specific place."
    ),
    parameters={
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "City or country name, e.g. 'Bali', 'Tokyo', 'Vietnam'.",
            },
            "month": {
                "type": "integer",
                "description": "Month (1-12) for seasonal detail. Omit if unspecified.",
                "minimum": 1,
                "maximum": 12,
            },
        },
        "required": ["city"],
    },
)
def get_destination_info(city: str, month: Optional[int] = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"city": city}

    match = next(
        (
            d
            for d in destination_data.get_all_destinations()
            if city.strip().lower() in (d.name.lower(), d.country.lower())
        ),
        None,
    )
    if match:
        payload["destination"] = _serialize(match)

    iata = primary_iata(city)
    if iata:
        payload["primary_airport"] = iata
        season = season_intelligence.get_season_info(iata, month)
        if season:
            payload["season"] = {
                "name": getattr(season, "season_name", None),
                "months": getattr(season, "months", None),
                "weather": getattr(season, "weather", None),
                "crowd_level": getattr(season, "crowd_level", None),
                "price_level": getattr(season, "price_level", None),
                "notes": getattr(season, "description", None),
            }
        cheapest = season_intelligence.get_cheapest_months(iata)
        if cheapest:
            payload["cheapest_months"] = cheapest

    # Resolving an airport code alone is not destination information. If there is
    # nothing substantive, say so -- do not return ok:true with an empty payload,
    # because the model will assume it has data and stop looking.
    substantive = {"destination", "season", "cheapest_months"}
    if not substantive & payload.keys():
        return {
            "ok": False,
            "error": (
                f"No curated data for '{city}'. Answer from your general knowledge, "
                f"but say that the figures are estimates."
            ),
        }

    return {"ok": True, "data": payload}

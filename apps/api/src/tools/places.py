"""
Place and date tools.

Two things the model must not guess on its own:

- **Airport codes.** "Jakarta" is CGK, HLP, or PCB. A wrong code means wrong
  search results, and the user has no way to tell.
- **Holiday dates.** The model knows today's date (injected into the system
  prompt), so it can work out "tomorrow" by itself. What it cannot know are
  Indonesian public holidays and seasonal pricing patterns.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from src.providers import places
from src.providers.intelligent_date_generator import IntelligentDateGenerator
from src.tools.registry import tool

logger = logging.getLogger(__name__)

_date_generator = IntelligentDateGenerator()


@tool(
    name="lookup_place",
    description=(
        "Resolve a city name, country, or colloquial nickname into IATA airport codes. "
        "Call this before searching flights whenever you are not certain of the code. "
        "Handles local nicknames such as 'Bali' or 'Jogja'. When several results come "
        "back for the same city, the first one is the primary airport."
    ),
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The place name exactly as the user wrote it, e.g. 'Bali', 'Jogja', 'Kuala Lumpur'.",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum results. Defaults to 5.",
                "minimum": 1,
                "maximum": 10,
            },
        },
        "required": ["query"],
    },
)
def lookup_place(query: str, limit: int = 5) -> dict[str, Any]:
    found = places.resolve(query, limit=limit)
    if not found:
        return {
            "ok": False,
            "error": f"No airport found for '{query}'. Try a more common city name.",
        }
    return {"ok": True, "data": {"query": query, "places": [p.to_dict() for p in found]}}


@tool(
    name="resolve_dates",
    description=(
        "Turn a vague timing preference into concrete dates, with the reasoning behind "
        "each one. Use this when the user talks about timing without naming a date "
        "('next long weekend', 'cherry blossom season', 'whenever is cheapest'). "
        "Not needed when the user already gave a specific date."
    ),
    parameters={
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "The user's timing wording, verbatim, in their own language.",
            },
            "destination": {
                "type": "string",
                "description": "Destination city or country, if known. Sharpens the seasonal suggestions.",
            },
            "origin": {
                "type": "string",
                "description": "Origin city, if known.",
            },
        },
        "required": ["expression"],
    },
)
def resolve_dates(
    expression: str,
    destination: Optional[str] = None,
    origin: Optional[str] = None,
) -> dict[str, Any]:
    suggestions = _date_generator.generate_dates_from_keywords(
        text=expression,
        destination=destination,
        origin=origin,
    )

    if not suggestions:
        return {
            "ok": True,
            "data": {
                "suggestions": [],
                "note": (
                    "No special date suggestions for that. Work it out from today's date, "
                    "or ask the user directly."
                ),
            },
        }

    return {
        "ok": True,
        "data": {
            "expression": expression,
            "suggestions": [
                {
                    "departure_date": s.departure_date,
                    "return_date": s.return_date,
                    "duration_days": s.duration_days,
                    "reason": s.reason,
                    "price_category": s.price_category,
                    "confidence": s.confidence,
                    "alternatives": s.alternative_dates,
                }
                for s in suggestions[:5]
            ],
        },
    }

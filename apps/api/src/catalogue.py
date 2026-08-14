"""
The curated catalogue, served to the frontend.

The landing page's inspiration grid and budget picker need the destination set
and the vocabularies behind it -- travel types, budget bands, seasons, regions.
All of that already exists in `providers/destination_data.py`; this module just
puts a stable shape on it.

The alternative was hardcoding the enums in TypeScript, which would drift the
first time a destination or a travel type was added. The monorepo generates
`packages/types` from this schema for exactly this reason.

Labels are Indonesian because the audience is. That is a product decision, not a
translation gap: the frontend is not expected to hold a second copy of these
strings, and a facet vocabulary is small and stable enough that server-side
labels are simpler than a client-side i18n table. If a second language ever
lands, it belongs here as another field, not as a fork of the list.
"""

from __future__ import annotations

from typing import Any, Optional

from src.providers import destination_data
from src.providers.destination_data import BudgetCategory, Season, TravelType
from src.providers.places import primary_iata
from src.tools.destinations import serialize

# Indonesian labels for the facet vocabularies. Deliberately short -- these
# render as chips and tiles, and Indonesian already runs long.
TRAVEL_TYPE_LABELS: dict[TravelType, str] = {
    TravelType.BEACH: "Pantai",
    TravelType.MOUNTAIN: "Gunung",
    TravelType.CULTURAL: "Budaya",
    TravelType.CITY: "Kota",
    TravelType.ADVENTURE: "Petualangan",
    TravelType.NATURE: "Alam",
    TravelType.FOODIE: "Kuliner",
    TravelType.SHOPPING: "Belanja",
}

BUDGET_LABELS: dict[BudgetCategory, str] = {
    BudgetCategory.BUDGET: "Hemat",
    BudgetCategory.AFFORDABLE: "Terjangkau",
    BudgetCategory.MODERATE: "Menengah",
    BudgetCategory.SPLURGE: "Bebas",
}

SEASON_LABELS: dict[Season, str] = {
    Season.ALL_YEAR: "Sepanjang tahun",
    Season.SUMMER: "Musim panas",
    Season.WINTER: "Musim dingin",
    Season.DRY_SEASON: "Musim kemarau",
    Season.RAINY_SEASON: "Musim hujan",
    Season.SPRING: "Musim semi",
    Season.AUTUMN: "Musim gugur",
}

REGION_LABELS: dict[str, str] = {
    "domestic": "Dalam negeri",
    "international": "Luar negeri",
}


def _rupiah_short(amount: Optional[int]) -> Optional[str]:
    """1_000_000 -> '1jt', 500_000 -> '500rb'. For chip labels, not for prices."""
    if amount is None:
        return None
    if amount >= 1_000_000:
        value = amount / 1_000_000
        return f"{value:g}jt"
    return f"{amount // 1000}rb"


def _budget_label(band: BudgetCategory) -> str:
    bounds = destination_data.BUDGET_BANDS[band]
    low, high = _rupiah_short(bounds["min_idr"]), _rupiah_short(bounds["max_idr"])
    if low is None:
        return f"< {high}"
    if high is None:
        return f"> {low}"
    return f"{low}–{high}"


def destinations() -> list[dict[str, Any]]:
    """
    The curated set, each entry carrying its primary airport.

    The IATA code is resolved here rather than stored on the destination because
    `places.py` is the single source of truth for airport codes -- a second copy
    on the destination record is a second thing to keep right. It can be None:
    not every curated place resolves, and the deals rail has to cope with that
    rather than assume it away.
    """
    out: list[dict[str, Any]] = []
    for dest in destination_data.get_all_destinations():
        entry = serialize(dest)
        entry["iata"] = primary_iata(dest.name)
        out.append(entry)
    return out


def facets() -> dict[str, Any]:
    """Vocabularies for the inspiration grid, budget picker, and explore chips."""
    return {
        "travel_types": [
            {"value": t.value, "label": TRAVEL_TYPE_LABELS[t]} for t in TravelType
        ],
        "budget_bands": [
            {
                "value": b.value,
                "label": BUDGET_LABELS[b],
                "range_label": _budget_label(b),
                **destination_data.BUDGET_BANDS[b],
            }
            for b in BudgetCategory
        ],
        "seasons": [{"value": s.value, "label": SEASON_LABELS[s]} for s in Season],
        "regions": [
            {"value": r, "label": REGION_LABELS[r]} for r in destination_data.REGIONS
        ],
    }

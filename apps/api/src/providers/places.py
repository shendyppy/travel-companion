"""
Place lookup — one entry point.

The question "which airport serves this city" used to be answered in four places:

    flight_api._load_airports_database / get_airport_from_city_code
    destination_lookup.DestinationDatabase
    geolocation.DestinationMatcher
    smart_detection.LocationDetector

Each had different coverage and returned different answers, so the result
depended on which path happened to be called. This module replaces all of them
with a single index built from airports.dat (the OpenFlights dataset, 6,000+
airports with IATA codes).

The only hand-written part is the primary-airport preference for multi-airport
cities (Tokyo -> NRT, not HND). That is an editorial judgement, not data -- the
dataset has no concept of a "main" airport.
"""

from __future__ import annotations

import csv
import logging
import re
import unicodedata
from dataclasses import dataclass, asdict
from typing import Any, Optional

from src.config import DATA_DIR

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Place:
    iata: str
    airport: str
    city: str
    country: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# Cities with more than one airport: which one is meant when the user names only
# the city. Keys are normalised city names and IATA city codes.
_PRIMARY_AIRPORT: dict[str, str] = {
    "jakarta": "CGK", "jkt": "CGK",
    "tokyo": "NRT", "tyo": "NRT",
    "osaka": "KIX", "osa": "KIX",
    "seoul": "ICN", "sel": "ICN",
    "london": "LHR", "lon": "LHR",
    "paris": "CDG", "par": "CDG",
    "new york": "JFK", "nyc": "JFK",
    "milan": "MXP", "mil": "MXP",
    "rome": "FCO", "rom": "FCO",
    "beijing": "PEK", "bjs": "PEK",
    "shanghai": "PVG", "sha": "PVG",
    "bangkok": "BKK",
    "moscow": "SVO", "mow": "SVO",
    "washington": "IAD", "was": "IAD",
    "chicago": "ORD", "chi": "ORD",
    "sao paulo": "GRU", "sao": "GRU",
    "buenos aires": "EZE", "bue": "EZE",
    "toronto": "YYZ", "yto": "YYZ",
    "berlin": "BER", "ber": "BER",
    "stockholm": "ARN", "sto": "ARN",
    "kuala lumpur": "KUL",
    "singapore": "SIN", "singapura": "SIN",
    "surabaya": "SUB",
    "denpasar": "DPS", "bali": "DPS",
    "yogyakarta": "YIA", "jogja": "YIA", "jogjakarta": "YIA",
    "medan": "KNO",
    "makassar": "UPG",
    "bandung": "BDO",
    "semarang": "SRG",
    "lombok": "LOP",
    "labuan bajo": "LBJ",
    "manado": "MDC",
    "balikpapan": "BPN",
    "padang": "PDG",
    "palembang": "PLM",
    "pekanbaru": "PKU",
    "banda aceh": "BTJ",
    "solo": "SOC",
    "malang": "MLG",
    "batam": "BTH",
}

# Airports that genuinely operate but are absent from airports.dat. The
# OpenFlights dataset stops around 2017, while these two opened in 2020 -- and
# flight APIs accept their codes. Without this, "Jogja" resolves to JOG
# (Adisutjipto), which no longer handles scheduled commercial traffic.
_SUPPLEMENT: list[tuple[str, str, str, str]] = [
    ("YIA", "Yogyakarta International Airport", "Yogyakarta", "Indonesia"),
    ("BER", "Berlin Brandenburg Airport", "Berlin", "Germany"),
]

# Nicknames people actually use that the dataset does not carry
_ALIASES: dict[str, str] = {
    "jogja": "yogyakarta",
    "jogjakarta": "yogyakarta",
    "yogya": "yogyakarta",
    "bali": "denpasar",
    "ho chi minh": "ho chi minh city",
    "saigon": "ho chi minh city",
    "makkah": "mecca",
    "madinah": "medina",
}

_by_iata: dict[str, Place] | None = None
_by_city: dict[str, list[Place]] | None = None


def _normalize(text: str) -> str:
    """Lowercase, strip accents and punctuation — so 'São Paulo' == 'sao paulo'."""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^\w\s]", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def _build_index() -> tuple[dict[str, Place], dict[str, list[Place]]]:
    global _by_iata, _by_city
    if _by_iata is not None and _by_city is not None:
        return _by_iata, _by_city

    by_iata: dict[str, Place] = {}
    by_city: dict[str, list[Place]] = {}

    path = DATA_DIR / "airports.dat"
    if not path.exists():
        logger.error("airports.dat not found at %s", path)
        _by_iata, _by_city = by_iata, by_city
        return by_iata, by_city

    with path.open("r", encoding="utf-8") as handle:
        for row in csv.reader(handle):
            # Format: ID, Name, City, Country, IATA, ICAO, lat, lon, ...
            if len(row) < 5:
                continue
            iata = row[4].strip().upper()
            if not iata or iata == "\\N" or len(iata) != 3:
                continue

            place = Place(
                iata=iata,
                airport=row[1].strip(),
                city=row[2].strip(),
                country=row[3].strip(),
            )
            by_iata[iata] = place

            city_key = _normalize(place.city)
            if city_key:
                by_city.setdefault(city_key, []).append(place)

    for iata, airport, city, country in _SUPPLEMENT:
        place = Place(iata=iata, airport=airport, city=city, country=country)
        by_iata[iata] = place
        # Placed first so it wins over the older airport in the same city
        by_city.setdefault(_normalize(city), []).insert(0, place)

    logger.info("Place index built: %d airports, %d city names", len(by_iata), len(by_city))
    _by_iata, _by_city = by_iata, by_city
    return by_iata, by_city


def _rank(places: list[Place], city_key: str) -> list[Place]:
    """Primary airport first when a city has several."""
    preferred = _PRIMARY_AIRPORT.get(city_key)
    if not preferred:
        return places
    return sorted(places, key=lambda p: 0 if p.iata == preferred else 1)


def resolve(query: str, limit: int = 5) -> list[Place]:
    """
    Turn whatever the user wrote into a list of airports, most relevant first.

    Accepts IATA codes ("DPS"), city names ("Denpasar"), city codes ("JKT"), and
    everyday nicknames ("Bali", "Jogja").
    """
    if not query or not query.strip():
        return []

    by_iata, by_city = _build_index()
    key = _normalize(query)
    key = _ALIASES.get(key, key)

    # 1. Exact IATA code
    upper = query.strip().upper()
    if len(upper) == 3 and upper in by_iata:
        return [by_iata[upper]]

    # 2. City code or nickname we map explicitly
    mapped = _PRIMARY_AIRPORT.get(key)
    if mapped and mapped in by_iata:
        primary = by_iata[mapped]
        others = [p for p in by_city.get(_normalize(primary.city), []) if p.iata != mapped]
        return [primary, *others][:limit]

    # 3. Exact city name
    if key in by_city:
        return _rank(by_city[key], key)[:limit]

    # 4. Partial match — cities starting with the query, then containing it
    starts = [c for c in by_city if c.startswith(key)]
    contains = [c for c in by_city if key in c and c not in starts]
    results: list[Place] = []
    for city_key in [*sorted(starts, key=len), *sorted(contains, key=len)]:
        results.extend(_rank(by_city[city_key], city_key))
        if len(results) >= limit:
            break
    return results[:limit]


def primary_iata(query: str) -> Optional[str]:
    """The most likely IATA code for a query, or None."""
    found = resolve(query, limit=1)
    return found[0].iata if found else None


def describe(iata: str) -> Optional[Place]:
    by_iata, _ = _build_index()
    return by_iata.get(iata.strip().upper())

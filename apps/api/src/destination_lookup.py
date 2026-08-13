"""
Dynamic destination lookup system

This module provides:
- Real-time destination detection from any country/city
- Airport code lookup
- Country information
- Travel suggestions based on detected location
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class DestinationInfo:
    """Destination information structure"""
    name: str
    country: str
    country_code: str
    region: str  # continent: Asia, Europe, Americas, Africa, Oceania
    airport_codes: List[str]
    popular_cities: List[str]
    currency: str
    best_seasons: List[str]
    description: str

class DestinationDatabase:
    """Comprehensive destination database with real airport codes"""

    # Mapping of countries to their information
    COUNTRIES = {
        # Asia
        "japan": {
            "country_code": "JP",
            "region": "Asia",
            "airport_codes": ["NRT", "HND", "KIX", "ITM", "FUK", "CTS", "OKA"],
            "popular_cities": ["Tokyo", "Osaka", "Kyoto", "Fukuoka", "Sapporo"],
            "currency": "JPY",
            "best_seasons": ["spring", "autumn"],
            "description": "Land of the rising sun with perfect blend of tradition and technology"
        },
        "south korea": {
            "country_code": "KR",
            "region": "Asia",
            "airport_codes": ["ICN", "GMP", "PUS", "CJU"],
            "popular_cities": ["Seoul", "Busan", "Jeju", "Incheon"],
            "currency": "KRW",
            "best_seasons": ["spring", "autumn"],
            "description": "Dynamic country with K-pop culture, ancient palaces, and beautiful landscapes"
        },
        "thailand": {
            "country_code": "TH",
            "region": "Asia",
            "airport_codes": ["BKK", "DMK", "CNX", "HKT", "HDY"],
            "popular_cities": ["Bangkok", "Chiang Mai", "Phuket", "Krabi", "Pattaya"],
            "currency": "THB",
            "best_seasons": ["winter", "dry_season"],
            "description": "Land of smiles with stunning beaches, temples, and amazing street food"
        },
        "singapore": {
            "country_code": "SG",
            "region": "Asia",
            "airport_codes": ["SIN", "XSP"],
            "popular_cities": ["Singapore"],
            "currency": "SGD",
            "best_seasons": ["all_year"],
            "description": "Modern city-state with multicultural neighborhoods and world-class attractions"
        },
        "malaysia": {
            "country_code": "MY",
            "region": "Asia",
            "airport_codes": ["KUL", "SZB", "PEN", "BKI"],
            "popular_cities": ["Kuala Lumpur", "Penang", "Johor Bahru", "Kota Kinabalu"],
            "currency": "MYR",
            "best_seasons": ["all_year"],
            "description": "Diverse country with modern cities, tropical rainforests, and pristine beaches"
        },
        "vietnam": {
            "country_code": "VN",
            "region": "Asia",
            "airport_codes": ["SGN", "HAN", "DAD", "CXR"],
            "popular_cities": ["Ho Chi Minh", "Hanoi", "Da Nang", "Nha Trang"],
            "currency": "VND",
            "best_seasons": ["winter", "dry_season"],
            "description": "Rich history, delicious pho, and stunning limestone karsts"
        },
        "philippines": {
            "country_code": "PH",
            "region": "Asia",
            "airport_codes": ["MNL", "CEB", "CRK", "DVO"],
            "popular_cities": ["Manila", "Cebu", "Boracay", "Palawan"],
            "currency": "PHP",
            "best_seasons": ["dry_season"],
            "description": "Archipelago with 7,000+ islands, world-class beaches, and warm hospitality"
        },
        "india": {
            "country_code": "IN",
            "region": "Asia",
            "airport_codes": ["DEL", "BOM", "CCU", "MAA", "BLR"],
            "popular_cities": ["New Delhi", "Mumbai", "Bangalore", "Chennai", "Kolkata"],
            "currency": "INR",
            "best_seasons": ["winter"],
            "description": "Incredible diversity with ancient monuments, spicy cuisine, and vibrant culture"
        },
        "china": {
            "country_code": "CN",
            "region": "Asia",
            "airport_codes": ["PVG", "PEK", "CAN", "SZX", "CTU"],
            "popular_cities": ["Shanghai", "Beijing", "Guangzhou", "Shenzhen", "Chengdu"],
            "currency": "CNY",
            "best_seasons": ["spring", "autumn"],
            "description": "Ancient civilization meets modern innovation with iconic landmarks"
        },

        # Europe
        "france": {
            "country_code": "FR",
            "region": "Europe",
            "airport_codes": ["CDG", "ORY", "NCE", "LYS"],
            "popular_cities": ["Paris", "Nice", "Lyon", "Marseille", "Bordeaux"],
            "currency": "EUR",
            "best_seasons": ["spring", "summer", "autumn"],
            "description": "Romantic country with art, wine, cuisine, and iconic landmarks"
        },
        "italy": {
            "country_code": "IT",
            "region": "Europe",
            "airport_codes": ["FCO", "MXP", "VCE", "NAP"],
            "popular_cities": ["Rome", "Milan", "Venice", "Florence", "Naples"],
            "currency": "EUR",
            "best_seasons": ["spring", "autumn"],
            "description": "Cradle of Roman Empire with Renaissance art and delicious cuisine"
        },
        "spain": {
            "country_code": "ES",
            "region": "Europe",
            "airport_codes": ["MAD", "BCN", "LPA", "PMI"],
            "popular_cities": ["Madrid", "Barcelona", "Seville", "Valencia", "Bilbao"],
            "currency": "EUR",
            "best_seasons": ["spring", "autumn"],
            "description": "Vibrant country with flamenco, tapas, beaches, and architectural wonders"
        },
        "united kingdom": {
            "country_code": "GB",
            "region": "Europe",
            "airport_codes": ["LHR", "LGW", "STN", "MAN"],
            "popular_cities": ["London", "Edinburgh", "Manchester", "Liverpool", "Bath"],
            "currency": "GBP",
            "best_seasons": ["summer"],
            "description": "Rich history, royal palaces, pub culture, and diverse landscapes"
        },
        "germany": {
            "country_code": "DE",
            "region": "Europe",
            "airport_codes": ["FRA", "MUC", "TXL", "HAM"],
            "popular_cities": ["Berlin", "Munich", "Frankfurt", "Hamburg", "Cologne"],
            "currency": "EUR",
            "best_seasons": ["summer"],
            "description": "Efficient country with castles, beer gardens, and Christmas markets"
        },
        "netherlands": {
            "country_code": "NL",
            "region": "Europe",
            "airport_codes": ["AMS", "RTM", "EIN"],
            "popular_cities": ["Amsterdam", "Rotterdam", "The Hague", "Utrecht"],
            "currency": "EUR",
            "best_seasons": ["spring", "summer"],
            "description": "Canals, tulips, windmills, and liberal culture"
        },
        "switzerland": {
            "country_code": "CH",
            "region": "Europe",
            "airport_codes": ["ZRH", "GVA", "BSL"],
            "popular_cities": ["Zurich", "Geneva", "Basel", "Interlaken", "Lucerne"],
            "currency": "CHF",
            "best_seasons": ["summer", "winter"],
            "description": "Alpine paradise with chocolate, watches, and stunning mountain scenery"
        },

        # Americas
        "united states": {
            "country_code": "US",
            "region": "Americas",
            "airport_codes": ["JFK", "LAX", "ORD", "DFW", "SFO"],
            "popular_cities": ["New York", "Los Angeles", "Chicago", "San Francisco", "Miami"],
            "currency": "USD",
            "best_seasons": ["summer", "autumn"],
            "description": "Diverse country with iconic cities, national parks, and cultural melting pot"
        },
        "canada": {
            "country_code": "CA",
            "region": "Americas",
            "airport_codes": ["YYZ", "YVR", "YUL", "YYC"],
            "popular_cities": ["Toronto", "Vancouver", "Montreal", "Calgary", "Ottawa"],
            "currency": "CAD",
            "best_seasons": ["summer"],
            "description": "Friendly country with pristine nature, multicultural cities, and maple syrup"
        },
        "brazil": {
            "country_code": "BR",
            "region": "Americas",
            "airport_codes": ["GRU", "GIG", "BSB", "CNF"],
            "popular_cities": ["São Paulo", "Rio de Janeiro", "Brasília", "Salvador"],
            "currency": "BRL",
            "best_seasons": ["autumn", "winter"],
            "description": "Vibrant country with Carnival, samba, beaches, and Amazon rainforest"
        },

        # Oceania
        "australia": {
            "country_code": "AU",
            "region": "Oceania",
            "airport_codes": ["SYD", "MEL", "BNE", "PER"],
            "popular_cities": ["Sydney", "Melbourne", "Brisbane", "Perth", "Gold Coast"],
            "currency": "AUD",
            "best_seasons": ["spring", "autumn"],
            "description": "Unique wildlife, stunning beaches, outdoor lifestyle, and laid-back culture"
        },
        "new zealand": {
            "country_code": "NZ",
            "region": "Oceania",
            "airport_codes": ["AKL", "CHC", "WLG", "ZQN"],
            "popular_cities": ["Auckland", "Christchurch", "Wellington", "Queenstown"],
            "currency": "NZD",
            "best_seasons": ["summer", "autumn"],
            "description": "Adventure paradise with mountains, fjords, and Middle-earth landscapes"
        }
    }

    # Indonesian country names mapping
    INDONESIAN_COUNTRY_MAPS = {
        "jepang": "japan",
        "korea": "south korea",
        "thailand": "thailand",
        "malaysia": "malaysia",
        "singapura": "singapore",
        "vietnam": "vietnam",
        "filipina": "philippines",
        "china": "china",
        "india": "india",
        "inggris": "united kingdom",
        "amerika": "united states",
        "perancis": "france",
        "italia": "italy",
        "spanyol": "spain",
        "jerman": "germany",
        "belanda": "netherlands",
        "swiss": "switzerland",
        "australia": "australia",
        "selandia baru": "new zealand",
        "brasilia": "brazil",
        "kanada": "canada"
    }

    # City to country mapping for quick lookup
    CITY_TO_COUNTRY = {}

    @classmethod
    def _build_city_mapping(cls):
        """Build reverse mapping from cities to countries"""
        for country, info in cls.COUNTRIES.items():
            for city in info["popular_cities"]:
                cls.CITY_TO_COUNTRY[city.lower()] = country
                # Add variations
                if city == "New Delhi":
                    cls.CITY_TO_COUNTRY["delhi"] = country

    @classmethod
    def detect_destination(cls, text: str) -> Optional[DestinationInfo]:
        """
        Detect destination from user text

        Args:
            text: User input text

        Returns:
            DestinationInfo if detected, None otherwise
        """
        # Build city mapping if not built
        if not cls.CITY_TO_COUNTRY:
            cls._build_city_mapping()

        text_lower = text.lower()

        # First check Indonesian names
        for indo_name, eng_name in cls.INDONESIAN_COUNTRY_MAPS.items():
            if indo_name in text_lower:
                country = eng_name
                info = cls.COUNTRIES[country]
                return DestinationInfo(
                    name=eng_name.title(),
                    country=country.title(),
                    country_code=info["country_code"],
                    region=info["region"],
                    airport_codes=info["airport_codes"],
                    popular_cities=info["popular_cities"],
                    currency=info["currency"],
                    best_seasons=info["best_seasons"],
                    description=info["description"]
                )

        # Direct country match (English)
        for country, info in cls.COUNTRIES.items():
            if country in text_lower:
                return DestinationInfo(
                    name=country.title(),
                    country=country.title(),
                    country_code=info["country_code"],
                    region=info["region"],
                    airport_codes=info["airport_codes"],
                    popular_cities=info["popular_cities"],
                    currency=info["currency"],
                    best_seasons=info["best_seasons"],
                    description=info["description"]
                )

        # City match
        for city, country in cls.CITY_TO_COUNTRY.items():
            if city in text_lower:
                info = cls.COUNTRIES[country]
                return DestinationInfo(
                    name=city.title(),
                    country=country.title(),
                    country_code=info["country_code"],
                    region=info["region"],
                    airport_codes=info["airport_codes"],
                    popular_cities=info["popular_cities"],
                    currency=info["currency"],
                    best_seasons=info["best_seasons"],
                    description=f"{city.title()}, {info['description']}"
                )

        return None

    @classmethod
    def get_airport_code(cls, city_or_country: str) -> Optional[str]:
        """
        Get primary airport code for destination

        Args:
            city_or_country: Name of city or country

        Returns:
            Airport code if found, None otherwise
        """
        dest = cls.detect_destination(city_or_country)
        if dest and dest.airport_codes:
            return dest.airport_codes[0]  # Return primary airport
        return None

    @classmethod
    def search_destination(cls, query: str, limit: int = 5) -> List[DestinationInfo]:
        """
        Search for destinations matching query

        Args:
            query: Search query
            limit: Maximum results to return

        Returns:
            List of matching destinations
        """
        query_lower = query.lower()
        results = []

        for country, info in cls.COUNTRIES.items():
            score = 0

            # Country name match
            if country in query_lower:
                score += 10

            # City matches
            for city in info["popular_cities"]:
                if city.lower() in query_lower:
                    score += 5

            if score > 0:
                results.append(DestinationInfo(
                    name=country.title(),
                    country=country.title(),
                    country_code=info["country_code"],
                    region=info["region"],
                    airport_codes=info["airport_codes"],
                    popular_cities=info["popular_cities"],
                    currency=info["currency"],
                    best_seasons=info["best_seasons"],
                    description=info["description"]
                ))

        # Sort by score and return top results
        results.sort(key=lambda x: query_lower.count(x.name.lower()), reverse=True)
        return results[:limit]
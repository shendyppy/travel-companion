"""
Geolocation module for dynamic location detection

This module detects user location based on:
- IP address (using free IP geolocation API)
- Manual location input
- Browser geolocation (when integrated with frontend)
"""

import requests
from typing import Dict, Optional
from dataclasses import dataclass

@dataclass
class LocationInfo:
    """Location information structure"""
    city: str
    country: str
    country_code: str
    latitude: float
    longitude: float
    timezone: str
    nearest_airport_code: str = None
    nearest_airport_name: str = None

class GeoDetector:
    """Handles geolocation detection using various methods"""

    # Free IP geolocation APIs (choose one)
    IP_APIS = [
        "https://ipapi.co/json/",
        "https://ip-api.com/json/",
        "https://ipinfo.io/json",
        "https://api.ipify.org?format=json"  # For IP only
    ]

    # Major cities and their nearest airports (global coverage)
    GLOBAL_AIRPORTS = {
        # Asia
        "jakarta": {"code": "CGK", "name": "Soekarno-Hatta International"},
        "singapore": {"code": "SIN", "name": "Changi Airport"},
        "kuala_lumpur": {"code": "KUL", "name": "KL International Airport"},
        "bangkok": {"code": "BKK", "name": "Suvarnabhumi Airport"},
        "manila": {"code": "MNL", "name": "Ninoy Aquino International"},
        "hanoi": {"code": "HAN", "name": "Noi Bai International"},
        "ho_chi_minh": {"code": "SGN", "name": "Tan Son Nhat International"},
        "tokyo": {"code": "NRT", "name": "Narita International"},
        "seoul": {"code": "ICN", "name": "Incheon International"},
        "hong_kong": {"code": "HKG", "name": "Hong Kong International"},
        "taipei": {"code": "TPE", "name": "Taoyuan International"},
        "shanghai": {"code": "PVG", "name": "Pudong International"},
        "beijing": {"code": "PEK", "name": "Beijing Capital International"},
        "mumbai": {"code": "BOM", "name": "Chhatrapati Shivaji International"},
        "delhi": {"code": "DEL", "name": "Indira Gandhi International"},
        "bangalore": {"code": "BLR", "name": "Kempegowda International"},
        # Europe
        "london": {"code": "LHR", "name": "Heathrow Airport"},
        "paris": {"code": "CDG", "name": "Charles de Gaulle Airport"},
        "amsterdam": {"code": "AMS", "name": "Schiphol Airport"},
        "frankfurt": {"code": "FRA", "name": "Frankfurt Airport"},
        "madrid": {"code": "MAD", "name": "Barajas Airport"},
        "rome": {"code": "FCO", "name": "Fiumicino Airport"},
        "barcelona": {"code": "BCN", "name": "Barcelona Airport"},
        # Middle East
        "dubai": {"code": "DXB", "name": "Dubai International"},
        "doha": {"code": "DOH", "name": "Hamad International"},
        "istanbul": {"code": "IST", "name": "Istanbul Airport"},
        # North America
        "new_york": {"code": "JFK", "name": "John F. Kennedy Airport"},
        "los_angeles": {"code": "LAX", "name": "Los Angeles International"},
        "san_francisco": {"code": "SFO", "name": "San Francisco International"},
        "toronto": {"code": "YYZ", "name": "Toronto Pearson International"},
        "vancouver": {"code": "YVR", "name": "Vancouver International"},
        # South America
        "sao_paulo": {"code": "GRU", "name": "Guarulhos Airport"},
        "buenos_aires": {"code": "EZE", "name": "Ezeiza Airport"},
        # Africa
        "cairo": {"code": "CAI", "name": "Cairo International"},
        "johannesburg": {"code": "JNB", "name": "OR Tambo Airport"},
        # Australia
        "sydney": {"code": "SYD", "name": "Kingsford Smith Airport"},
        "melbourne": {"code": "MEL", "name": "Tullamarine Airport"},
    }

    @classmethod
    def detect_from_ip(cls) -> Optional[LocationInfo]:
        """
        Detect location from IP address using free API

        Returns:
            LocationInfo or None if detection fails
        """
        for api_url in cls.IP_APIS[:3]:  # Try first 3 APIs
            try:
                response = requests.get(api_url, timeout=5)
                response.raise_for_status()
                data = response.json()

                # Parse different API responses
                if "ip" in data and "org" not in data:  # ipify - only gives IP
                    continue

                # Extract common fields
                city = data.get("city", "").lower()
                country = data.get("country_name", data.get("country", ""))
                country_code = data.get("country_code", data.get("cc", ""))
                latitude = float(data.get("latitude", 0))
                longitude = float(data.get("longitude", 0))
                timezone = data.get("timezone", "")

                # Find nearest airport
                airport_info = cls._find_nearest_airport(city, country_code)

                return LocationInfo(
                    city=data.get("city", ""),
                    country=country,
                    country_code=country_code,
                    latitude=latitude,
                    longitude=longitude,
                    timezone=timezone,
                    nearest_airport_code=airport_info["code"] if airport_info else None,
                    nearest_airport_name=airport_info["name"] if airport_info else None
                )

            except Exception as e:
                print(f"Failed to detect location from {api_url}: {e}")
                continue

        return None

    @classmethod
    def _find_nearest_airport(cls, city: str, country_code: str) -> Optional[Dict]:
        """
        Find nearest airport for a given city

        Args:
            city: City name
            country_code: Two-letter country code

        Returns:
            Airport info dict or None
        """
        # Normalize city name
        city_key = city.lower().replace(" ", "_")

        # Direct match
        if city_key in cls.GLOBAL_AIRPORTS:
            return cls.GLOBAL_AIRPORTS[city_key]

        # Common city name variations
        city_variations = {
            "ny": "new_york",
            "la": "los_angeles",
            "sf": "san_francisco",
            "dubai_city": "dubai",
            "kuala_lumpur_city": "kuala_lumpur",
            "hcmc": "ho_chi_minh",
            "hcm": "ho_chi_minh",
        }

        if city_key in city_variations:
            city_key = city_variations[city_key]
            if city_key in cls.GLOBAL_AIRPORTS:
                return cls.GLOBAL_AIRPORTS[city_key]

        # Country-specific defaults
        country_defaults = {
            "ID": "jakarta",
            "SG": "singapore",
            "MY": "kuala_lumpur",
            "TH": "bangkok",
            "PH": "manila",
            "VN": "ho_chi_minh",
            "US": "new_york",
            "GB": "london",
            "FR": "paris",
            "DE": "frankfurt",
            "AE": "dubai",
            "AU": "sydney",
        }

        if country_code in country_defaults:
            default_city = country_defaults[country_code]
            return cls.GLOBAL_AIRPORTS.get(default_city)

        return None

    @classmethod
    def parse_manual_input(cls, location_text: str) -> Optional[Dict]:
        """
        Parse manually entered location

        Args:
            location_text: User input like "I'm in Tokyo" or "Dari Surabaya"

        Returns:
            Airport info or None
        """
        # Clean and normalize
        text = location_text.lower()

        # Check if city exists in our database
        for city, airport in cls.GLOBAL_AIRPORTS.items():
            # Check for city name matches
            if city.replace("_", " ") in text or city in text:
                return {
                    "code": airport["code"],
                    "name": f"{city.replace('_', ' ').title()} ({airport['name']})",
                    "city": city.replace("_", " "),
                    "country": None  # Could be added if needed
                }

        return None

# Country-based destination suggestions
class DestinationMatcher:
    """Matches destinations based on user's location"""

    REGIONAL_DESTINATIONS = {
        # Southeast Asia (from Indonesia)
        "ID": {
            "domestic": ["bali", "lombok", "yogyakarta", "bandung", "medan"],
            "regional": ["singapore", "kuala_lumpur", "bangkok", "ho_chi_minh"],
            "international": ["tokyo", "seoul", "dubai", "hong_kong"]
        },
        # Southeast Asia (from Singapore)
        "SG": {
            "domestic": [],  # Singapore has no domestic flights
            "regional": ["jakarta", "bali", "kuala_lumpur", "bangkok", "ho_chi_minh"],
            "international": ["tokyo", "seoul", "sydney", "dubai"]
        },
        # Southeast Asia (from Malaysia)
        "MY": {
            "domestic": ["kota_kinabalu", "penang", "langkawi"],
            "regional": ["jakarta", "bali", "singapore", "bangkok", "ho_chi_minh"],
            "international": ["tokyo", "seoul", "sydney", "dubai"]
        },
        # Default for other countries
        "default": {
            "domestic": [],
            "regional": [],  # Will be populated based on distance
            "international": ["bali", "singapore", "bangkok", "tokyo", "dubai", "paris", "new_york"]
        }
    }

    @classmethod
    def get_suggested_destinations(cls, user_country_code: str) -> Dict[str, list]:
        """
        Get destination suggestions based on user's country

        Args:
            user_country_code: Two-letter country code

        Returns:
            Dictionary with domestic, regional, international suggestions
        """
        # Get regional mapping or use default
        if user_country_code in cls.REGIONAL_DESTINATIONS:
            return cls.REGIONAL_DESTINATIONS[user_country_code]
        else:
            # For other countries, suggest popular global destinations
            return cls.REGIONAL_DESTINATIONS["default"]
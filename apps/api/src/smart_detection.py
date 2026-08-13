"""
Smart detection module for auto-suggesting travel options

This module contains functions to:
- Auto-detect user location from context
- Suggest optimal travel dates (next 2 months)
- Generate complete travel package suggestions
"""

import re
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

try:
    from src.destination_lookup import DestinationDatabase
    from src.intelligent_date_generator import IntelligentDateGenerator
except ImportError:
    from destination_lookup import DestinationDatabase
    from intelligent_date_generator import IntelligentDateGenerator

@dataclass
class FlightSuggestion:
    """Complete flight suggestion with all details"""
    origin: str
    origin_code: str
    destination: str
    destination_code: str
    airline: str
    departure_date: str
    return_date: Optional[str]
    price_per_person: float
    currency: str = "IDR"

class LocationDetector:
    """Detects locations from user conversation and context"""

    # Major Indonesian cities with their airports
    INDONESIAN_CITIES = {
        "jakarta": {"code": "CGK", "name": "Jakarta", "full_name": "Jakarta (Soekarno-Hatta)"},
        "surabaya": {"code": "SUB", "name": "Surabaya", "full_name": "Surabaya (Juanda)"},
        "medan": {"code": "KNO", "name": "Medan", "full_name": "Medan (Kualanamu)"},
        "bali": {"code": "DPS", "name": "Denpasar", "full_name": "Denpasar/Bali (Ngurah Rai)"},
        "denpasar": {"code": "DPS", "name": "Denpasar", "full_name": "Denpasar/Bali (Ngurah Rai)"},
        "makassar": {"code": "UPG", "name": "Makassar", "full_name": "Makassar (Sultan Hasanuddin)"},
        "yogyakarta": {"code": "JOG", "name": "Yogyakarta", "full_name": "Yogyakarta (Adisucipto)"},
        "jogja": {"code": "JOG", "name": "Yogyakarta", "full_name": "Yogyakarta (Adisucipto)"},
        "bandung": {"code": "BDO", "name": "Bandung", "full_name": "Bandung (Husein)"},
        "batam": {"code": "BTH", "name": "Batam", "full_name": "Batam (Hang Nadim)"},
        "pekanbaru": {"code": "PKU", "name": "Pekanbaru", "full_name": "Pekanbaru (Sultan Syarif)"},
        "palembang": {"code": "PLM", "name": "Palembang", "full_name": "Palembang (Sultan Mahmud)"},
        "balikpapan": {"code": "BPN", "name": "Balikpapan", "full_name": "Balikpapan (Sepinggan)"},
        "semarang": {"code": "SRG", "name": "Semarang", "full_name": "Semarang (Ahmad Yani)"},
        "lombok": {"code": "LOP", "name": "Lombok", "full_name": "Lombok (Lombok International)"},
        "manado": {"code": "MDC", "name": "Manado", "full_name": "Manado (Sam Ratulangi)"},
        "pontianak": {"code": "PNK", "name": "Pontianak", "full_name": "Pontianak (Supadio)"},
    }

    # Popular international destinations from Indonesia
    INTERNATIONAL_DESTINATIONS = {
        "singapore": {"code": "SIN", "name": "Singapore", "full_name": "Singapore (Changi)", "country": "Singapore"},
        "kuala lumpur": {"code": "KUL", "name": "Kuala Lumpur", "full_name": "Kuala Lumpur (KLIA)", "country": "Malaysia"},
        "penang": {"code": "PEN", "name": "Penang", "full_name": "Penang (Penang International)", "country": "Malaysia"},
        "johor bahru": {"code": "JHB", "name": "Johor Bahru", "full_name": "Johor Bahru", "country": "Malaysia"},
        "bangkok": {"code": "BKK", "name": "Bangkok", "full_name": "Bangkok (Suvarnabhumi)", "country": "Thailand"},
        "chiang mai": {"code": "CNX", "name": "Chiang Mai", "full_name": "Chiang Mai", "country": "Thailand"},
        "phuket": {"code": "HKT", "name": "Phuket", "full_name": "Phuket", "country": "Thailand"},
        "ho chi minh": {"code": "SGN", "name": "Ho Chi Minh", "full_name": "Ho Chi Minh City", "country": "Vietnam"},
        "hanoi": {"code": "HAN", "name": "Hanoi", "full_name": "Hanoi", "country": "Vietnam"},
        "siem reap": {"code": "REP", "name": "Siem Reap", "full_name": "Siem Reap", "country": "Cambodia"},
        "vientiane": {"code": "VTE", "name": "Vientiane", "full_name": "Vientiane", "country": "Laos"},
        "manila": {"code": "MNL", "name": "Manila", "full_name": "Manila (Ninoy Aquino)", "country": "Philippines"},
        "cebu": {"code": "CEB", "name": "Cebu", "full_name": "Cebu", "country": "Philippines"},
    }

    # Common location indicators
    LOCATION_INDICATORS = [
        "dari", "from", "berangkat dari", "departure",
        "ke", "to", "tujuan", "destination",
        "di", "at", "located", "tinggal", "live"
    ]

    @classmethod
    def detect_origin(cls, text: str, conversation_history: List[str] = None) -> Optional[Dict]:
        """
        Detect user's origin location from text and conversation history

        Args:
            text: Current user message
            conversation_history: Previous messages for context

        Returns:
            Location dictionary or None if not found
        """
        # Combine all text to search
        all_text = text.lower()
        if conversation_history:
            all_text = " ".join(conversation_history[-3:]) + " " + all_text  # Last 3 messages for context

        # Check for explicit origin indicators
        for indicator in cls.LOCATION_INDICATORS[:4]:  # Origin indicators
            pattern = f"{indicator} ([a-z\\s]+)"
            match = re.search(pattern, all_text.lower())
            if match:
                location = match.group(1).strip()
                # Clean up and check if it's a known city
                location = location.split()[0]  # Take first word
                if location in cls.INDONESIAN_CITIES:
                    return cls.INDONESIAN_CITIES[location]
                if location in cls.INTERNATIONAL_DESTINATIONS:
                    return cls.INTERNATIONAL_DESTINATIONS[location]

        # Check for city mentions without indicators
        for city, info in cls.INDONESIAN_CITIES.items():
            if city in all_text:
                # Check if it's likely origin (e.g., "tinggal di", "dari Jakarta")
                if any(word in all_text for word in ["tinggal di", "dari " + city, "stay in", "live in"]):
                    return info

        # Default to Jakarta if no location found (most common origin)
        return cls.INDONESIAN_CITIES["jakarta"]

    @classmethod
    def suggest_destinations(cls, origin: str, travel_type: str = None, budget: str = None,
                            detected_destination: Optional[str] = None) -> List[Dict]:
        """
        Suggest destinations based on origin, preferences, and detected destination

        Args:
            origin: Origin city code
            travel_type: beach, cultural, city, etc.
            budget: budget, affordable, moderate
            detected_destination: Destination mentioned by user (e.g., "Japan", "Paris")

        Returns:
            List of suggested destinations
        """
        suggestions = []

        # If user mentioned a specific destination, use it
        if detected_destination:
            dest_info = DestinationDatabase.detect_destination(detected_destination)
            if dest_info:
                # Add all popular cities from the detected destination
                # For example, if user says "Japan", add Tokyo, Osaka, etc.
                for city in dest_info.popular_cities[:3]:  # Top 3 cities from same country
                    # Find airport code for this city
                    airport_code = None
                    if dest_info.airport_codes:
                        # Match city to airport code (simplified - take in order)
                        city_index = dest_info.popular_cities.index(city)
                        if city_index < len(dest_info.airport_codes):
                            airport_code = dest_info.airport_codes[city_index]
                        else:
                            airport_code = dest_info.airport_codes[0]  # Default to first
                    
                    suggestions.append({
                        "name": city,
                        "code": airport_code if airport_code else "UNKNOWN",
                        "full_name": f"{city} ({airport_code if airport_code else ''})",
                        "country": dest_info.country,
                        "region": dest_info.region
                    })
                
                # If less than 3 cities, we're good with what we have
                # Don't add "similar destinations" from other countries

        # If origin is Indonesia and no specific destination mentioned
        elif origin in [city["code"] for city in cls.INDONESIAN_CITIES.values()]:
            # Domestic suggestions based on travel type
            domestic_suggestions = {
                "beach": ["bali", "lombok", "belitung"],
                "cultural": ["yogyakarta", "bandung", "malang"],
                "city": ["bandung", "surabaya", "medan"],
                "nature": ["lombok", "malang", "bandung"],
                "foodie": ["bandung", "yogyakarta", "surabaya"]
            }

            # Add domestic
            if travel_type and travel_type in domestic_suggestions:
                for city in domestic_suggestions[travel_type][:3]:
                    if city in cls.INDONESIAN_CITIES:
                        suggestions.append(cls.INDONESIAN_CITIES[city])
            else:
                # Default popular domestic destinations
                for city in ["bali", "lombok", "yogyakarta"]:
                    suggestions.append(cls.INDONESIAN_CITIES[city])

            # Add nearby international destinations
            for city in ["singapore", "kuala lumpur", "penang"]:
                suggestions.append(cls.INTERNATIONAL_DESTINATIONS[city])

        return suggestions[:5]  # Return top 5 suggestions

    @classmethod
    def _get_similar_destinations(cls, region: str, current_destination: str) -> List[Dict]:
        """
        Get similar destinations in the same region

        Args:
            region: Continent/region (Asia, Europe, Americas, etc.)
            current_destination: Current destination to exclude

        Returns:
            List of similar destination dicts
        """
        similar_destinations = []

        # Popular destinations by region, grouped by country for better filtering
        regional_suggestions = {
            "Asia": {
                "Japan": [
                    {"name": "Tokyo", "code": "NRT", "full_name": "Tokyo (Narita)", "country": "Japan"},
                    {"name": "Osaka", "code": "KIX", "full_name": "Osaka (Kansai)", "country": "Japan"},
                ],
                "South Korea": [
                    {"name": "Seoul", "code": "ICN", "full_name": "Seoul (Incheon)", "country": "South Korea"},
                    {"name": "Busan", "code": "PUS", "full_name": "Busan", "country": "South Korea"},
                ],
                "Thailand": [
                    {"name": "Bangkok", "code": "BKK", "full_name": "Bangkok (Suvarnabhumi)", "country": "Thailand"},
                    {"name": "Phuket", "code": "HKT", "full_name": "Phuket", "country": "Thailand"},
                ],
                "Others": [
                    {"name": "Singapore", "code": "SIN", "full_name": "Singapore (Changi)", "country": "Singapore"},
                ]
            },
            "Europe": [
                {"name": "Paris", "code": "CDG", "full_name": "Paris (Charles de Gaulle)", "country": "France"},
                {"name": "London", "code": "LHR", "full_name": "London (Heathrow)", "country": "United Kingdom"},
                {"name": "Rome", "code": "FCO", "full_name": "Rome (Fiumicino)", "country": "Italy"},
                {"name": "Barcelona", "code": "BCN", "full_name": "Barcelona", "country": "Spain"},
            ],
            "Americas": [
                {"name": "New York", "code": "JFK", "full_name": "New York (JFK)", "country": "United States"},
                {"name": "Los Angeles", "code": "LAX", "full_name": "Los Angeles (LAX)", "country": "United States"},
                {"name": "Toronto", "code": "YYZ", "full_name": "Toronto Pearson", "country": "Canada"},
            ],
            "Oceania": [
                {"name": "Sydney", "code": "SYD", "full_name": "Sydney (Kingsford Smith)", "country": "Australia"},
                {"name": "Auckland", "code": "AKL", "full_name": "Auckland", "country": "New Zealand"},
            ]
        }

        # Get destinations for the region
        if region in regional_suggestions:
            if region == "Asia":
                # Special handling for Asia to avoid mixing countries
                current_country = None
                for country, cities in regional_suggestions[region].items():
                    for city in cities:
                        if city["name"].lower() == current_destination.lower() or \
                           current_destination.lower() in ["japan", "jepang"] and country == "Japan" or \
                           current_destination.lower() in ["korea"] and country == "South Korea":
                            current_country = country
                            break
                    if current_country:
                        break

                # If we found the country, suggest from other countries only
                if current_country:
                    for country, cities in regional_suggestions[region].items():
                        if country != current_country:
                            similar_destinations.extend(cities[:2])  # Take 2 cities from each other country
                else:
                    # If country not found, return all except the current city
                    for country, cities in regional_suggestions[region].items():
                        for city in cities:
                            if city["name"].lower() != current_destination.lower():
                                similar_destinations.append(city)
            else:
                # For other regions, use original logic
                for dest in regional_suggestions[region]:
                    if dest["name"].lower() != current_destination.lower():
                        similar_destinations.append(dest)

        return similar_destinations[:4]  # Return max 4 suggestions

class DateRangeSuggester:
    """Suggests optimal travel dates within next 2 months"""

    @staticmethod
    def get_date_ranges(months_ahead: int = 6) -> List[Dict]:
        """
        Get suggested date ranges for the next N months (spread out for better prices)

        Args:
            months_ahead: How many months ahead to suggest

        Returns:
            List of date range suggestions with price optimization tips
        """
        ranges = []
        current_date = datetime.now()

        for month_offset in range(months_ahead):
            # Calculate start and end of month
            target_month = current_date.month + month_offset
            year = current_date.year + (target_month - 1) // 12
            month = (target_month - 1) % 12 + 1

            # Skip if it's too soon (less than 2 weeks from now) - prices are higher
            first_day_of_month = datetime(year, month, 1)
            if first_day_of_month < (current_date + timedelta(weeks=2)):
                continue

            # Best day to book: Usually Tuesday or Wednesday are cheapest
            # Pick mid-week dates for better prices
            first_tuesday = first_day_of_month + timedelta(
                days=((1 - first_day_of_month.weekday()) % 7)
            )
            # Make sure it's the first Tuesday (not Monday disguised as day 1)
            if first_day_of_month.weekday() != 1:
                first_tuesday += timedelta(days=7)

            # For longer stays (5-7 days), better deals
            return_date = first_tuesday + timedelta(days=6)  # Week-long trip

            if return_date.month == month:  # Make sure return is in the same month
                ranges.append({
                    "name": f"Best Price Period - {datetime(year, month, 1).strftime('%B %Y')}",
                    "departure": first_tuesday.strftime("%Y-%m-%d"),
                    "return": return_date.strftime("%Y-%m-%d"),
                    "duration": "7 days 6 nights",
                    "type": "Optimized Price",
                    "tip": "Tuesday departures typically have the lowest prices",
                    "booking_window": "Book 4-6 weeks ahead for best rates"
                })

        # Sort by price optimization score
        return sorted(ranges, key=lambda x: x["departure"])[:6]

class PackageGenerator:
    """Generates complete travel package suggestions"""

    # Common airlines on Indonesian routes
    POPULAR_AIRLINES = {
        "domestic": ["Garuda Indonesia", "Lion Air", "Citilink", "Batik Air", "AirAsia", "Sriwijaya Air"],
        "international": ["AirAsia", "Garuda Indonesia", "Singapore Airlines", "Malaysia Airlines", "Thai Airways"]
    }

    # Estimated price ranges (IDR per person)
    PRICE_ESTIMATES = {
        "domestic": {
            "budget": {"min": 500000, "max": 1500000},
            "affordable": {"min": 1500000, "max": 3000000},
            "moderate": {"min": 3000000, "max": 5000000}
        },
        "international": {
            "budget": {"min": 1000000, "max": 3000000},
            "affordable": {"min": 3000000, "max": 6000000},
            "moderate": {"min": 6000000, "max": 10000000}
        }
    }

    @classmethod
    def generate_packages(cls, origin: Dict, destinations: List[Dict],
                         date_ranges: List[Dict], budget_category: str = "affordable",
                         user_input: str = None, detected_destination: str = None) -> List[FlightSuggestion]:
        """
        Generate complete flight packages with intelligent date generation

        Args:
            origin: Origin location info
            destinations: List of destination options
            date_ranges: List of date options (can be intelligent suggestions)
            budget_category: budget, affordable, moderate
            user_input: Original user input for keyword analysis
            detected_destination: Detected destination name

        Returns:
            List of complete flight suggestions
        """
        packages = []

        # Use intelligent date generation if user input is provided
        if user_input and (not date_ranges or "bebas" in user_input.lower() or "murah" in user_input.lower()):
            date_generator = IntelligentDateGenerator()
            smart_suggestions = date_generator.generate_dates_from_keywords(
                user_input,
                detected_destination,
                origin.get("name")
            )

            # Convert intelligent suggestions to date ranges
            intelligent_ranges = []
            for suggestion in smart_suggestions[:2]:  # Use top 2 intelligent suggestions
                intelligent_ranges.append({
                    "departure": suggestion.departure_date,
                    "return": suggestion.return_date,
                    "duration": f"{suggestion.duration_days} days",
                    "type": "Intelligent Suggestion",
                    "tip": suggestion.reason,
                    "price_category": suggestion.price_category
                })

            # Use intelligent ranges if available
            date_ranges = intelligent_ranges if intelligent_ranges else date_ranges

        for dest in destinations[:3]:  # Top 3 destinations
            for date_range in date_ranges[:2]:  # Top 2 date ranges
                # Determine if domestic or international
                is_international = dest.get("country") is not None
                route_type = "international" if is_international else "domestic"

                # Select airline
                airlines = cls.POPULAR_AIRLINES[route_type]
                airline = airlines[hash(dest["code"] + date_range["departure"]) % len(airlines)]

                # Estimate price with adjustments for intelligent suggestions
                price_range = cls.PRICE_ESTIMATES[route_type][budget_category]
                if date_range.get("price_category") == "budget":
                    # Reduce price by 20% for budget category
                    estimated_price = int((price_range["min"] + price_range["max"]) // 2 * 0.8)
                elif date_range.get("price_category") == "premium":
                    # Increase price by 30% for premium category
                    estimated_price = int((price_range["min"] + price_range["max"]) // 2 * 1.3)
                else:
                    estimated_price = (price_range["min"] + price_range["max"]) // 2

                # Create suggestion
                suggestion = FlightSuggestion(
                    origin=origin["full_name"],
                    origin_code=origin["code"],
                    destination=dest.get("full_name", dest["name"]),
                    destination_code=dest["code"],
                    airline=airline,
                    departure_date=date_range["departure"],
                    return_date=date_range.get("return"),
                    price_per_person=estimated_price
                )

                packages.append(suggestion)

        return packages

    @staticmethod
    def format_package_suggestion(suggestions: List[FlightSuggestion]) -> str:
        """
        Format flight suggestions into user-friendly message

        Args:
            suggestions: List of flight suggestions

        Returns:
            Formatted string with suggestions
        """
        if not suggestions:
            return "❌ Belum bisa generate paket perjalanan. Coba sebutin lokasi dan preferensi Anda ya!"

        formatted = "\n\n" + "="*70 + "\n"
        formatted += "✈️  REKOMENDASI PAKET PERJALANAN LENGKAP ✈️\n"
        formatted += "="*70 + "\n"

        # Add price optimization tip
        formatted += "💰 **HARGA OPTIMAL:** Tuesday departures & 7-day trips usually have lowest prices!\n\n"
        formatted += "⚠️  **PERHATIAN:** Harga di bawah adalah ESTIMASI. Cari harga real-time dengan sebutkan tanggal spesifik!\n"

        formatted += "\n💡 **Berikut beberapa pilihan lengkap untuk Anda:**\n"

        for i, flight in enumerate(suggestions[:6], 1):  # Show top 6
            # Check if this is a special tip card (not a flight suggestion)
            if isinstance(flight, dict) and "tip" in flight:
                formatted += f"\n{i}. **{flight['name']}**\n"
                formatted += f"   {flight['tip']}\n"
                formatted += f"   📍 {flight['origin']} → {flight['destination']}\n"
                formatted += f"   ✈️  Kode Penerbangan: {flight['origin_code']} → {flight['destination_code']}\n\n"
                continue

            formatted += f"\n{i}. **{flight.destination}**\n"
            formatted += f"   🛫 Dari: {flight.origin}\n"
            formatted += f"   ✈️  Maskapai: {flight.airline}\n"
            formatted += f"   📅 Berangkat: {flight.departure_date}"
            if flight.return_date:
                formatted += f" | Kembali: {flight.return_date}"
            formatted += f"\n"
            formatted += f"   💰 Estimasi/orang: Rp {flight.price_per_person:,.0f}\n"
            formatted += f"   💳 Total (2 orang): Rp {flight.price_per_person * 2:,.0f}\n"

            if i < len(suggestions):
                formatted += "\n" + "-"*50

        formatted += "\n\n🎯 **Next Steps:**\n"
        formatted += "- Suka destinasi ini? Aku bisa cari harga real-time sekarang!\n"
        formatted += "- Mau negara/destinasi lain? Sebutin saja (misal: \"Mau ke Paris\", \"Liburan ke Korea\")\n"
        formatted += "- Butuh info hotel atau aktivitas di destinasi? Ask me!\n"

        return formatted

def detect_travel_intentions(text: str) -> Dict:
    """
    Main function to detect all travel intentions from user message

    Args:
        text: User message

    Returns:
        Dictionary with all detected information
    """
    intentions = {}

    # Detect explicit mentions
    text_lower = text.lower()

    # Check if asking for complete trip
    trip_keywords = [
        "liburan", "vacation", "jalan-jalan", "trip", "wisata",
        "mau pergi", "pengen liburan", "planning trip",
        "paket liburan", "paket wisata", "all in"
    ]

    if any(keyword in text_lower for keyword in trip_keywords):
        intentions["wants_complete_trip"] = True

    # Check if asking for flights specifically
    flight_keywords = [
        "flight", "penerbangan", "tiket pesawat", "terbang",
        "cari flight", "flight murah", "tiket pesawat"
    ]

    if any(keyword in text_lower for keyword in flight_keywords):
        intentions["wants_flights"] = True

    return intentions
"""
Flight API module - Handles Amadeus API integration for flight search

This module provides functions to search flights, parse results, and format
them for display in the travel agent.

HINT:
This file is the "brain" for finding flight tickets. It talks to a service called "Amadeus"
which is like a giant database of real-time flight info used by travel agencies.
"""

import logging
import re
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import requests # type: ignore

# HINT: We use 'try-except' here because sometimes the 'amadeus' library might not be installed.
# This prevents the whole program from crashing just because one library is missing.
try:
    from amadeus import Client, ResponseError # type: ignore
except ImportError:
    Client = None
    ResponseError = None

try:
    from src.config import AMADEUS_CLIENT_ID, AMADEUS_CLIENT_SECRET, AMADEUS_CONFIGURED
except ImportError:
    from config import AMADEUS_CLIENT_ID, AMADEUS_CLIENT_SECRET, AMADEUS_CONFIGURED

# Get logger for this module
# HINT: Logging is better than 'print()' because it can save errors to a file
# and lets us control how much detail we want to see (INFO, WARNING, ERROR).
logger = logging.getLogger(__name__)

# --- CACHE & DATABASES ---
# HINT: "Caching" means saving a result so we don't have to ask for it again.
# It makes the program faster and saves money on API calls.

# Cache for exchange rates (to avoid repeated API calls)
_exchange_rate_cache: Dict[str, float] = {}
_airline_name_cache: Dict[str, str] = {}
_airlines_db: Optional[Dict[str, list]] = None  # Will load OpenFlights data
_airports_db: Optional[Dict[str, str]] = None  # Will load OpenFlights airport country mapping

# Mapping for common airline codes that Amadeus uses (not standard IATA)
# These come from actual flight search results
_AMADEUS_CARRIER_CODES = {
    "OD": "Malindo Air",  # Malaysian carrier
    "ID": "Batik Air",    # Indonesian carrier (Batik Air using ID code in Amadeus)
    "Z2": "Zip Air",      # Japanese LCC
    "SJ": "Sriwijaya Air", # Indonesian carrier
    "JT": "Lion Air",     # Indonesian carrier (Lion Mentari)
    "SL": "Thai Lion Air",  # Thai carrier (using ICAO code)
}


def _load_airlines_database() -> Dict[str, list]:
    """
    Load airline database from OpenFlights CSV file
    
    HINT: This function reads a big text file (CSV) that contains info about all airlines.
    We need this because the Amadeus API sometimes only gives us a code like "GA",
    and we want to show "Garuda Indonesia" to the user.
    """
    global _airlines_db

    # HINT: If we already loaded the data, don't do it again! (Caching)
    if _airlines_db is not None:
        return _airlines_db

    _airlines_db = {}

    try:
        import os
        import csv

        # Path to airlines database
        # HINT: __file__ is the path to THIS script. We go up one folder (..) then into 'data'.
        db_path = os.path.join(os.path.dirname(__file__), "..", "data", "airlines.dat")

        if not os.path.exists(db_path):
            logger.warning(f"Airlines database not found at {db_path}")
            return _airlines_db

        # EXPLANATION: We open the file and read it line by line.
        with open(db_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                # Skip broken lines
                if len(row) < 7:
                    continue

                try:
                    # Extract fields from the CSV row
                    # The file format is: ID, Name, IATA, ICAO, Callsign, Country, Active
                    airline_name = row[1].strip()
                    iata_code = row[2].strip()  # e.g., "GA"
                    icao_code = row[3].strip()  # e.g., "GIA"
                    country = row[5].strip()
                    active = row[6].strip()

                    # Skip if codes are missing or weird ("\N" means null in this DB)
                    if (not iata_code or iata_code == "\\N") and (not icao_code or icao_code == "\\N"):
                        continue

                    # Create a simple dictionary for this airline
                    airline_info = {
                        "name": airline_name,
                        "country": country if country != "\\N" else None,
                        "active": active == "Y",
                    }

                    # HINT: We save the airline info under BOTH its IATA code (GA) and ICAO code (GIA)
                    # so we can find it easily later no matter which code we have.
                    
                    # Index by IATA code
                    if iata_code and iata_code != "\\N":
                        if iata_code not in _airlines_db:
                            _airlines_db[iata_code] = []
                        _airlines_db[iata_code].append(airline_info)

                    # Index by ICAO code
                    if icao_code and icao_code != "\\N" and icao_code != iata_code:
                        if icao_code not in _airlines_db:
                            _airlines_db[icao_code] = []
                        _airlines_db[icao_code].append(airline_info)

                except (IndexError, ValueError):
                    continue

        logger.info(f"Loaded airlines database: {len(_airlines_db)} codes")
        return _airlines_db

    except Exception as e:
        logger.error(f"Error loading airlines database: {e}")
        _airlines_db = {}
        return _airlines_db


class AmadeusClient:
    """
    Wrapper for Amadeus API client
    
    HINT: This class handles the connection to Amadeus.
    It checks if you have the API keys set up correctly in your .env file.
    """

    def __init__(self):
        """Initialize Amadeus client with credentials from environment"""
        
        # Check if keys are in .env
        if not AMADEUS_CONFIGURED:
            logger.warning(
                "Amadeus API not configured. Set AMADEUS_CLIENT_ID and AMADEUS_CLIENT_SECRET in .env"
            )
            self.client = None
            return

        # Check if library is installed
        if Client is None:
            logger.error("amadeus package not installed. Run: pip install amadeus")
            self.client = None
            return

        try:
            # EXPLANATION: This is where we actually log in to Amadeus.
            self.client = Client(
                client_id=AMADEUS_CLIENT_ID, client_secret=AMADEUS_CLIENT_SECRET
            )
            logger.info("Amadeus client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Amadeus client: {e}", exc_info=True)
            self.client = None

    def is_ready(self) -> bool:
        """Check if client is ready to use"""
        return self.client is not None


def search_flights(
    origin: str, destination: str, departure_date: str, adults: int = 1,
    return_date: str = None, trip_type: str = "oneway"
) -> Dict[str, Any]:
    """
    Search for flights using Google Flights (primary) with Amadeus fallback
    
    This function implements a fallback mechanism:
    1. Try Google Flights API first (if configured and enabled)
    2. Fall back to Amadeus API if Google Flights fails or is unavailable
    
    Args:
        origin: Origin airport code (e.g., "CGK")
        destination: Destination airport code (e.g., "NRT")
        departure_date: Departure date in YYYY-MM-DD format
        adults: Number of adult passengers (default: 1)
        return_date: Return date for round-trip (YYYY-MM-DD format, optional)
        trip_type: "oneway" or "roundtrip" (default: "oneway")
        
    Returns:
        Dictionary with success status, flight data, and error info
    """
    try:
        from src.config import GOOGLE_FLIGHTS_ENABLED, GOOGLE_FLIGHTS_CONFIGURED
    except ImportError:
        from config import GOOGLE_FLIGHTS_ENABLED, GOOGLE_FLIGHTS_CONFIGURED
    
    # Normalize airport codes (city code -> airport code)
    origin_normalized = get_airport_from_city_code(origin) or origin
    destination_normalized = get_airport_from_city_code(destination) or destination
    
    # Try Google Flights first (if enabled and configured)
    if GOOGLE_FLIGHTS_ENABLED and GOOGLE_FLIGHTS_CONFIGURED:
        try:
            try:
                from src.google_flights_api import search_google_flights
            except ImportError:
                from google_flights_api import search_google_flights
            
            logger.info(f">>> Attempting Google Flights API search ({trip_type})...")
            result = search_google_flights(
                origin_normalized, destination_normalized, departure_date, adults,
                return_date=return_date, trip_type=trip_type
            )
            
            if result["success"] and result.get("data"):
                logger.info(f"[OK] Google Flights API successful: {len(result.get('data', []))} flights found")
                return result
            else:
                logger.warning(f"Google Flights API returned no data: {result.get('error')}, falling back to Amadeus")
                
        except Exception as e:
            logger.warning(f"Google Flights API error: {e}, falling back to Amadeus")
    
    # Fallback to Amadeus API (note: Amadeus doesn't support roundtrip in single call)
    logger.info("[FALLBACK] Using Amadeus API")
    return search_amadeus_flights(origin, destination, departure_date, adults)


def search_amadeus_flights(
    origin: str, destination: str, departure_date: str, adults: int = 1
) -> Dict[str, Any]:
    """
    Search for flights using Amadeus API (fallback provider)
    
    HINT: This is the main function! It takes where you are (origin), where you want to go (destination),
    and when (date), and asks Amadeus for a list of flights.
    """
    amadeus = AmadeusClient()

    if not amadeus.is_ready():
        return {
            "success": False,
            "data": None,
            "error": "Amadeus API not configured. Please check your .env file.",
        }

    try:
        # Normalize input to IATA codes (convert to uppercase)
        # Try to map city names to airport codes if possible (e.g. Jakarta -> CGK)
        # This fixes the Amadeus 400 error caused by sending city names
        origin_code = get_airport_from_city_code(origin) or origin.upper().strip()
        destination_code = get_airport_from_city_code(destination) or destination.upper().strip()
        
        # Override with codes
        origin = origin_code
        destination = destination_code

        # Validate departure date with user-friendly messages
        try:
            departure_dt = datetime.strptime(departure_date, "%Y-%m-%d")
            today = datetime.now()
            days_from_now = (departure_dt - today).days

            # Amadeus API typically allows booking 1-330 days in advance
            if days_from_now < 1:
                return {
                    "success": False,
                    "data": None,
                    "error": f"📅 Maaf, tanggal {departure_date} sudah lewat. Coba tanggal besok atau setelahnya ya! 😊",
                }
            elif days_from_now > 90:
                # Test environment limitation - suggest searching closer dates
                return {
                    "success": False,
                    "data": None,
                    "error": f"🔍 Maaf, pencarian tiket terlalu jauh ke depan ({days_from_now} hari dari sekarang). Untuk hasil terbaik, coba cari dalam 3 bulan ke depan ya! Kalau mau planning jangka panjang, bisa cari dekat-dekat tanggal keberangkatan nanti. ✈️",
                }
        except ValueError:
            return {
                "success": False,
                "data": None,
                "error": f"📅 Format tanggal tidak valid. Coba pakai format: TAHUN-BULAN-TANGGAL (contoh: 2026-02-15) ya! 😊",
            }

        logger.info(
            f"Searching flights from {origin} to {destination} on {departure_date}"
        )

        # EXPLANATION: This is the actual API call to Amadeus.
        # We ask for 'flight_offers_search' which gives us ticket prices and schedules.
        response = amadeus.client.shopping.flight_offers_search.get(
            originLocationCode=origin,
            destinationLocationCode=destination,
            departureDate=departure_date,
            adults=adults,
        )

        # Check if response has data
        if not response.data:
            logger.warning(
                f"No flights found for {origin}-{destination} on {departure_date}"
            )
            return {"success": True, "data": [], "error": None}

        logger.info(f"Found {len(response.data)} flight offers")
        return {"success": True, "data": response.data, "error": None}

    except ResponseError as error:
        # HINT: If something goes wrong (like bad internet or wrong airport code),
        # Amadeus throws a 'ResponseError'. We catch it here to explain what happened.
        logger.error(f"Amadeus API error: {error}", exc_info=True)
        error_message = str(error)

        # Parse common error messages to be more user-friendly
        error_status = getattr(error, 'response', {}).get('status_code', None) if hasattr(error, 'response') else None

        if error_status == 400:
            # Bad Request - usually date too far or no data available
            friendly_error = "🔍 Maaf, belum ada jadwal penerbangan untuk tanggal tersebut. Coba tanggal lain yang lebih dekat ya! Kalau mau, bilang aja 'cari yang paling murah' biar aku carikan tanggal terbaik dalam 7 hari ke depan. ✈️"
        elif "not a valid" in error_message.lower() or "invalid" in error_message.lower():
            friendly_error = "🛫 Maaf, kode bandara tidak dikenali. Coba sebutin nama kota atau bandara yang lebih umum ya! (contoh: Jakarta, Bali, Singapore) 😊"
        elif "unauthorized" in error_message.lower():
            friendly_error = "⚠️ Maaf, ada masalah dengan koneksi ke sistem pencarian tiket. Coba lagi dalam beberapa detik ya!"
        else:
            # Generic error with friendly message
            friendly_error = f"🔍 Maaf, belum bisa mencari tiket untuk rute/tanggal ini. Bisa coba:\n• Tanggal lain yang lebih dekat\n• Rute lain yang mirip\n• Atau bilang 'cari yang termurah' biar aku carikan tanggal terbaik! ✈️"

        return {
            "success": False,
            "data": None,
            "error": friendly_error,
        }

    except Exception as e:
        logger.error(f"Unexpected error during flight search: {e}", exc_info=True)
        return {
            "success": False,
            "data": None,
            "error": f"⚠️ Maaf, ada masalah saat mencari tiket. Coba lagi dalam beberapa detik ya! Kalau masih error, bilang 'cari yang termurah' biar aku carikan opsi terbaik. 😊",
        }


def get_exchange_rate(from_currency: str, to_currency: str = "IDR") -> Optional[float]:
    """
    Get exchange rate from one currency to another
    
    HINT: Amadeus often gives prices in EUR or USD. We want to show Rupiah (IDR).
    This function asks a free API "how much is 1 EUR in IDR today?"
    """
    cache_key = f"{from_currency}_{to_currency}"

    # Check cache first
    if cache_key in _exchange_rate_cache:
        return _exchange_rate_cache[cache_key]

    try:
        # Using free exchangerate-api.com (no API key required)
        url = f"https://api.exchangerate-api.com/v4/latest/{from_currency}"
        response = requests.get(url, timeout=5)
        response.raise_for_status()

        data = response.json()
        if to_currency in data.get("rates", {}):
            rate = data["rates"][to_currency]
            _exchange_rate_cache[cache_key] = rate
            return rate
        else:
            logger.warning(f"Currency {to_currency} not found in exchange rates")
            return None

    except Exception as e:
        # HINT: If we can't get the rate, we just return None.
        # The main code will handle this by showing the original currency (e.g. "EUR 500").
        logger.warning(f"Failed to fetch exchange rate: {e}")
        return None


def _load_airports_database() -> Dict[str, str]:
    """
    Load airport database from OpenFlights CSV file
    
    HINT: This loads another big text file (airports.dat) to map codes like "CGK" to "Indonesia".
    """
    global _airports_db

    if _airports_db is not None:
        return _airports_db

    _airports_db = {}

    try:
        import os
        import csv

        db_path = os.path.join(os.path.dirname(__file__), "..", "data", "airports.dat")

        if not os.path.exists(db_path):
            logger.warning(f"Airports database not found at {db_path}")
            return _airports_db

        with open(db_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) < 5:
                    continue

                try:
                    # Format: ID, Name, City, Country, IATA, ICAO...
                    country = row[3].strip()
                    iata_code = row[4].strip()

                    # Skip if no IATA code
                    if not iata_code or iata_code == "\\N":
                        continue

                    # Map IATA code to country
                    _airports_db[iata_code] = country

                except (IndexError, ValueError):
                    continue

        logger.info(f"Loaded {len(_airports_db)} airports from OpenFlights database")
        return _airports_db

    except Exception as e:
        logger.error(f"Error loading airports database: {e}")
        _airports_db = {}
        return _airports_db


def _get_country_from_airport(airport_code: str) -> Optional[str]:
    """
    Get country name from airport code using OpenFlights database

    Args:
        airport_code: IATA airport code (e.g., 'CGK', 'BKK', 'SIN')

    Returns:
        Country name or None if unknown
    """
    if not airport_code:
        return None

    airport_code = airport_code.strip().upper()

    try:
        airports_db = _load_airports_database()
        country = airports_db.get(airport_code)
        if country:
            logger.debug(f"Found {airport_code} -> {country}")
            return country
    except Exception as e:
        logger.warning(f"Error looking up airport {airport_code}: {e}")

    logger.debug(f"Could not find country for airport code: {airport_code}")
    return None


def get_airline_name(airline_code: str, origin: Optional[str] = None, destination: Optional[str] = None) -> str:
    """
    Get full airline name from airline code
    
    HINT: This function is a bit complex because finding an airline name isn't always easy.
    Sometimes "ID" means "Batik Air", sometimes it might mean something else in another country.
    
    STRATEGY:
    1. Check our fast cache (memory).
    2. Check Amadeus special codes (like OD, ID, JT).
    3. Ask Amadeus API directly.
    4. Check our big OpenFlights database.
    5. If all else fails, just return the code (e.g. "GA").
    """
    if not airline_code:
        return "Unknown Airline"

    airline_code = airline_code.strip().upper()
    cache_key = f"{airline_code}_{origin}_{destination}"

    # 1. Check cache first
    if cache_key in _airline_name_cache:
        return _airline_name_cache[cache_key]

    # 2. Check Amadeus carrier codes mapping (these are not in OpenFlights)
    if airline_code in _AMADEUS_CARRIER_CODES:
        name = _AMADEUS_CARRIER_CODES[airline_code]
        _airline_name_cache[cache_key] = name
        return name

    # 3. Try Amadeus API as backup (if configured)
    try:
        if AMADEUS_CONFIGURED and Client:
            amadeus = AmadeusClient()
            if amadeus.is_ready():
                response = amadeus.client.reference_data.airlines.get(
                    airlineCode=airline_code
                )
                if response.data:
                    name = response.data[0].get("businessName", airline_code)
                    _airline_name_cache[cache_key] = name
                    return name
    except Exception as e:
        pass # It's okay if this fails, we have more backups.

    # 4. Fallback: Try OpenFlights database
    try:
        airlines_db = _load_airlines_database()
        if airline_code in airlines_db:
            airline_list = airlines_db[airline_code]

            # If only one airline, return it
            if len(airline_list) == 1:
                name = airline_list[0]["name"]
                _airline_name_cache[cache_key] = name
                return name

            # EXPLANATION: If multiple airlines have the same code, we try to guess
            # based on where the flight is going (origin/destination).
            # For example, if flying from Indonesia, "ID" is probably Batik Air.
            
            origin_country = _get_country_from_airport(origin) if origin else None
            dest_country = _get_country_from_airport(destination) if destination else None
            
            relevant_countries = {origin_country, dest_country}
            relevant_countries.discard(None)

            # Look for an airline from the relevant countries
            for airline in airline_list:
                country = airline.get("country", "")
                if airline["active"] and country in relevant_countries:
                    name = airline["name"]
                    _airline_name_cache[cache_key] = name
                    return name

            # If no match, just take the first active one
            for airline in airline_list:
                if airline["active"]:
                    name = airline["name"]
                    _airline_name_cache[cache_key] = name
                    return name
            
            # If no active ones, just take the first one
            name = airline_list[0]["name"]
            _airline_name_cache[cache_key] = name
            return name

    except Exception as e:
        logger.warning(f"Error looking up airline in OpenFlights DB: {e}")

    # 5. Final fallback: return the code itself
    _airline_name_cache[cache_key] = airline_code
    return airline_code


def format_duration(duration_str: str) -> str:
    """
    Convert ISO 8601 duration format to human-readable format

    Args:
        duration_str: Duration in ISO format (e.g., 'PT1H50M', 'PT10H', 'P1DT2H30M')

    Returns:
        Human-readable duration (e.g., '1h 50m', '10h', '1d 2h 30m')
    """
    if not duration_str:
        return "N/A"

    try:
        # Parse ISO 8601 duration
        # Format: P[n]Y[n]M[n]DT[n]H[n]M[n]S
        pattern = r"P(?:(\d+)Y)?(?:(\d+)M)?(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?"
        match = re.match(pattern, duration_str)

        if not match:
            return duration_str  # Return as-is if can't parse

        years, months, days, hours, minutes, seconds = match.groups()

        parts = []
        if days:
            parts.append(f"{days}d")
        if hours:
            parts.append(f"{hours}h")
        if minutes:
            parts.append(f"{minutes}m")
        if seconds:
            parts.append(f"{seconds}s")

        return " ".join(parts) if parts else "N/A"

        return " ".join(parts) if parts else "N/A"

    except Exception as e:
        logger.warning(f"Error parsing duration {duration_str}: {e}")
        return duration_str


def parse_duration_to_minutes(duration_str: str) -> int:
    """
    Convert ISO 8601 duration to minutes for comparison
    
    Args:
        duration_str: Duration in ISO format (e.g., 'PT1H50M')
        
    Returns:
        Total minutes (int)
    """
    try:
        pattern = r"P(?:(\d+)Y)?(?:(\d+)M)?(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?"
        match = re.match(pattern, duration_str)
        
        if not match:
            return 999999 # Return huge number if invalid so it's not picked as fastest
            
        years, months, days, hours, minutes, seconds = match.groups()
        
        total_minutes = 0
        if days: total_minutes += int(days) * 24 * 60
        if hours: total_minutes += int(hours) * 60
        if minutes: total_minutes += int(minutes)
        
        return total_minutes
    except Exception:
        return 999999


def generate_flight_recommendation(flight_data: list) -> str:
    """
    Analyze flights and generate recommendations
    
    Args:
        flight_data: List of flight offers
        
    Returns:
        Formatted recommendation string
    """
    if not flight_data:
        return ""
        
    try:
        # We only look at the top 5 results to be fair
        candidates = flight_data[:5]
        
        cheapest_flight = None
        cheapest_price = float('inf')
        
        fastest_flight = None
        fastest_duration = float('inf')
        
        # Analyze each flight
        for i, flight in enumerate(candidates, 1):
            # Check Price
            try:
                price = float(flight.get("price", {}).get("grandTotal", float('inf')))
                if price < cheapest_price:
                    cheapest_price = price
                    cheapest_flight = i
            except (ValueError, TypeError):
                pass
                
            # Check Duration (first leg)
            try:
                duration_str = flight.get("itineraries", [])[0].get("duration", "")
                duration_mins = parse_duration_to_minutes(duration_str)
                if duration_mins < fastest_duration:
                    fastest_duration = duration_mins
                    fastest_flight = i
            except (IndexError, AttributeError):
                pass

        # Build Recommendation Text
        recs = []
        recs.append("\n💡 **Rekomendasi Travel Buddy:**")
        
        if cheapest_flight:
            recs.append(f"• **Paling Hemat**: Opsi {cheapest_flight} (Harga termurah)")
            
        if fastest_flight and fastest_flight != cheapest_flight:
            recs.append(f"• **Paling Cepat**: Opsi {fastest_flight} (Durasi terpendek)")
            
        # "Best Value" logic: If cheapest is also fastest, it's the best!
        if cheapest_flight == fastest_flight and cheapest_flight is not None:
             recs.append(f"• **TERBAIK**: Opsi {cheapest_flight} (Menang di harga DAN waktu! 🔥)")
        
        return "\n".join(recs) + "\n"

    except Exception as e:
        logger.error(f"Error generating recommendation: {e}")
        return ""


def get_airline_name_safe(airline_code: str, origin: Optional[str] = None, destination: Optional[str] = None) -> str:
    """
    Safe wrapper for get_airline_name with better error handling

    Args:
        airline_code: IATA airline code
        origin: Origin airport code for context
        destination: Destination airport code for context

    Returns:
        Airline name or user-friendly fallback
    """
    if not airline_code or airline_code.strip() == "":
        return "Unknown Airline"

    name = get_airline_name(airline_code, origin, destination)
    if name == airline_code:  # If still same as code, format it nicely
        return f"Airline {airline_code.upper()}"

    return name


def format_flight_results(flight_data: list) -> str:
    """
    Format flight search results for display
    
    HINT: The data we get from Amadeus is a list of dictionaries (JSON).
    It's very nested and hard to read. This function picks out the important parts
    (price, time, airline) and makes a nice text string to show the user.
    """
    if not flight_data:
        return "No flights found for this route."

    formatted = "✈️ **Flight Options:**\n\n"

    # Show top 5 results
    for i, flight in enumerate(flight_data[:5], 1):
        try:
            # --- 1. GET PRICE ---
            # The price is usually in EUR or USD. We try to convert it to IDR.
            price = flight.get("price", {})
            total_price = price.get("grandTotal", "N/A")
            currency = price.get("currency", "EUR")

            price_idr = total_price
            
            # EXPLANATION: If it's not IDR, we try to convert it.
            if currency != "IDR" and total_price != "N/A":
                try:
                    rate = get_exchange_rate(currency, "IDR")
                    if rate:
                        price_idr = float(total_price) * rate
                        price_idr = f"Rp {price_idr:,.0f}" # Format as "Rp 1,500,000"
                    else:
                        price_idr = f"{currency} {total_price}"
                except ValueError:
                    price_idr = f"{currency} {total_price}"
            else:
                if price_idr != "N/A":
                    price_idr = f"Rp {float(price_idr):,.0f}"

            # --- 2. GET FLIGHT DETAILS ---
            # "itineraries" is a list of journeys. Usually just one for one-way.
            itineraries = flight.get("itineraries", [])
            if not itineraries:
                continue

            first_leg = itineraries[0]
            segments = first_leg.get("segments", [])
            if not segments:
                continue

            # First segment tells us departure, last segment tells us arrival
            first_segment = segments[0]
            last_segment = segments[-1]

            departure = first_segment.get("departure", {})
            arrival = last_segment.get("arrival", {})

            # Format: 2025-12-20T10:00:00
            departure_time = departure.get("at", "N/A").replace("T", " ")
            arrival_time = arrival.get("at", "N/A").replace("T", " ")

            # --- 3. GET AIRLINE ---
            # We need the airline code from the first flight segment
            airline_code = first_segment.get("operating", {}).get("carrierCode", "")
            if not airline_code:
                 airline_code = first_segment.get("carrierCode", "")

            # We use our helper function to get the real name
            origin_airport = departure.get("iataCode", "")
            dest_airport = arrival.get("iataCode", "")
            airline_name = get_airline_name_safe(airline_code, origin_airport, dest_airport)

            # --- 4. DURATION ---
            duration_iso = first_leg.get("duration", "")
            duration_readable = format_duration(duration_iso)

            # --- 5. BUILD THE STRING ---
            formatted += f"**Option {i}:**\n"
            formatted += f"  💰 Price: {price_idr}\n"
            formatted += f"  ✈️  Departs: {departure_time}\n"
            formatted += f"  🛬 Arrives: {arrival_time}\n"
            formatted += f"  ⏱️  Duration: {duration_readable}\n"
            formatted += f"  🔤 Airline: {airline_name}\n"
            formatted += f"  📍 Stops: {len(segments) - 1}\n\n"

        except (KeyError, TypeError) as e:
            logger.warning(f"Error parsing flight data: {e}")
            continue

    if formatted == "✈️ **Flight Options:**\n\n":
        return "Could not parse flight results. Please try again."

    # Add recommendations at the end
    recommendation = generate_flight_recommendation(flight_data)
    formatted += recommendation

    return formatted


def format_flight_error(error: str) -> str:
    """
    Format error message for display with user-friendly messaging

    Args:
        error: Error message from flight search

    Returns:
        Formatted error message
    """
    # Check if error already has emojis (already formatted)
    if any(emoji in error for emoji in ["🔍", "📅", "⚠️", "🛫"]):
        return f"\n{error}\n"

    # Generic error - make it user-friendly
    return f"\n🔍 **Maaf, belum bisa menemukan penerbangan yang sesuai.**\n\n{error}\n\n💡 **Tips:**\n• Coba tanggal lain yang lebih dekat (1-3 bulan ke depan)\n• Bilang 'cari yang termurah' biar aku carikan tanggal terbaik\n• Atau sebutin kota asal dan tujuan yang lebih spesifik ✈️\n"


def detect_flight_request(text: str) -> bool:
    """
    Detect if user is asking about flights
    
    HINT: We look for keywords like "flight", "ticket", "bali", etc.
    If we find enough keywords, we assume the user wants to book a flight.
    """
    flight_keywords = [
        "penerbangan",
        "flight",
        "flights",
        "tiket",
        "ticket",
        "pesawat",
        "airplane",
        "airport",
        "bandara",
        "dari",
        "ke",
        "tanggal",
        "date",
        "harga",
        "price",
        "murah",
        "cheap",
    ]

    text_lower = text.lower()
    keyword_count = sum(1 for keyword in flight_keywords if keyword in text_lower)

    # Consider it a flight request if at least 2 keywords found
    return keyword_count >= 2


def extract_airport_code(text: str) -> Optional[str]:
    """
    Extract IATA airport code (3 letters) from text

    HINT: Airport codes are always 3 capital letters (like "CGK").
    We use 'regex' (regular expressions) to find them.
    """
    # Common airport codes list for validation
    common_airports = {
        # Indonesian
        "CGK", "DPS", "SUB", "JOG", "YIA", "UPG", "BDO", "BTH", "PKU", "PLM",
        "BPN", "SRG", "LOP", "MDC", "PNK", "KNO", "BTJ", "MDN", "DJJ", "BIK",
        # International
        "NRT", "HND", "KIX", "ITM", "SIN", "KUL", "PEN", "JHB", "BKK", "HKT",
        "CNX", "MNL", "CEB", "SGN", "HAN", "REP", "VTE", "ICN", "GMP", "PUS",
        "PEK", "PVG", "HKG", "TPE", "KHH", "BOM", "DEL", "CMB", "MLE", "DAC",
        "CCU", "KTM", "LHE", "ISB", "KHI", "DXB", "DOH", "KWI", "BAH", "RUH",
        "JED", "CAI", "TLL", "ADD", "NBO", "JRO", "DAR", "LOS", "ACC", "DKR",
        "JNB", "CPT", "LOS", "ABV", "GBE", "LHR", "LGW", "STN", "LTN", "CDG",
        "ORY", "AMS", "BRU", "DUS", "FRA", "MUC", "TXL", "ZUR", "GVA", "MXP",
        "FCO", "VCE", "MAD", "BCN", "LIS", "OPO", "IST", "SAW", "ATH", "SKG",
        "SOF", "BUD", "PRG", "VIE", "WAW", "BTS", "OTP", "TLV", "CAI", "ADD",
        "TLV", "AMM", "BEY", "DAM", "ALG", "TUN", "CMN", "RAK", "MRS", "NCE",
        "LYS", "TLS", "NTE", "BOD", "MLH", "FRA", "MUC", "BER", "HAM", "CGN",
        "DUS", "STR", "BLL", "CPH", "ARN", "GOT", "OSL", "TRD", "HEL", "TLL",
        "RIX", "VNO", "KUN", "BEG", "ZAG", "SJJ", "LJU", "PRN", "TGD", "SPU",
        "DBV", "ZAD", "PUY", "SKG", "ATH", "JMK", "HER", "KVA", "CFU", "ZTH",
        "RHO", "BJV", "AYT", "DLM", "ESB", "SAW", "ADB", "IST", "KAYS", "MSR",
        "MLA", "FUE", "LPA", "TFS", "AGP", "ALC", "VLC", "IBZ", "PMI", "MAH",
        "LPA", "TFS", "FUE", "ACE", "SPC", "VDE", "LPA", "TFS", "FUE", "ACE",
        "JFK", "EWR", "LGA", "BOS", "BWI", "DCA", "IAD", "ATL", "CLT", "MIA",
        "FLL", "MCO", "TPA", "MSP", "ORD", "MDW", "DFW", "DAL", "IAH", "HOU",
        "SLC", "DEN", "PHX", "LAS", "LAX", "SFO", "SAN", "SEA", "PDX", "SMF",
        "OAK", "SJC", "BUR", "LGB", "HNL", "OGG", "KOA", "LIH", "ITO", "KOA",
        "YVR", "YYZ", "YUL", "YOW", "YYC", "YEG", "YHZ", "YWG", "YQT", "YFB"
    }

    # Match 3-letter airport codes
    # EXPLANATION: \b means "word boundary" (start or end of a word).
    # [A-Z]{3} means "exactly 3 uppercase letters".
    codes = re.findall(r"\b([A-Z]{3})\b", text)

    # Filter for valid airport codes
    valid_codes = [code for code in codes if code in common_airports]

    if valid_codes:
        return valid_codes[0]
    return None


def extract_date_from_text(text: str) -> Optional[str]:
    """
    Extract date in YYYY-MM-DD format from text

    HINT: Dates can be written in many ways (2025-12-25, 25 Dec, etc.).
    We try a few common patterns to guess what the user meant.
    """
    # Handle relative dates like "minggu depan", "besok", etc.
    text_lower = text.lower()

    # Check for "minggu depan" or similar phrases
    if any(phrase in text_lower for phrase in ["minggu depan", "next week"]):
        today = datetime.now()
        # Get next week's date (7 days from now)
        next_week = today + timedelta(days=7)
        return next_week.strftime("%Y-%m-%d")

    # Check for "besok" or "tomorrow"
    elif any(phrase in text_lower for phrase in ["besok", "tomorrow"]):
        tomorrow = datetime.now() + timedelta(days=1)
        return tomorrow.strftime("%Y-%m-%d")

    # Check for "lusa" (day after tomorrow)
    elif "lusa" in text_lower:
        day_after = datetime.now() + timedelta(days=2)
        return day_after.strftime("%Y-%m-%d")

    # Try to match YYYY-MM-DD format (priority 1)
    date_match = re.search(r"(\d{4})-(\d{2})-(\d{2})", text)
    if date_match:
        year, month, day = date_match.groups()
        return f"{year}-{month}-{day}"

    # Try to match DD/MM/YYYY or DD-MM-YYYY (priority 2)
    date_match = re.search(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b", text)
    if date_match:
        day, month, year = date_match.groups()
        try:
            date_obj = datetime(int(year), int(month), int(day))
            return date_obj.strftime("%Y-%m-%d")
        except ValueError:
            return None

    # Try to match Indonesian month names (priority 3)
    # EXPLANATION: We map names like "Januari" to numbers like 1.
    months_id = {
        "januari": 1,
        "februari": 2,
        "maret": 3,
        "april": 4,
        "mei": 5,
        "juni": 6,
        "juli": 7,
        "agustus": 8,
        "september": 9,
        "oktober": 10,
        "november": 11,
        "desember": 12,
    }

    for month_name, month_num in months_id.items():
        pattern = rf"(\d{{1,2}})\s+{month_name}\s+(\d{{4}})"
        date_match = re.search(pattern, text.lower())
        if date_match:
            day, year = date_match.groups()
            try:
                date_obj = datetime(int(year), month_num, int(day))
                return date_obj.strftime("%Y-%m-%d")
            except ValueError:
                continue

    # Try to match English month names (priority 4)
    months_en = {
        "january": 1,
        "february": 2,
        "march": 3,
        "april": 4,
        "may": 5,
        "june": 6,
        "july": 7,
        "august": 8,
        "september": 9,
        "october": 10,
        "november": 11,
        "december": 12,
    }

    for month_name, month_num in months_en.items():
        pattern = rf"(\d{{1,2}})\s+{month_name}\s+(\d{{4}})"
        date_match = re.search(pattern, text.lower())
        if date_match:
            day, year = date_match.groups()
            try:
                date_obj = datetime(int(year), month_num, int(day))
                return date_obj.strftime("%Y-%m-%d")
            except ValueError:
                continue

    return None


def extract_date_range_from_text(text: str) -> Optional[tuple]:
    """
    Extract date range from text (e.g., "2026-01-17 dan 2026-01-31")
    
    Detects patterns with separators: "dan", "sampai", "hingga", "to", "-", "until"
    
    Args:
        text: Input text containing date range
        
    Returns:
        Tuple of (start_date, end_date) in YYYY-MM-DD format, or None
    """
    # Common range separators in Indonesian and English
    separators = [
        r'\s+dan\s+',      # "2026-01-17 dan 2026-01-31"
        r'\s+sampai\s+',   # "2026-01-17 sampai 2026-01-31"
        r'\s+hingga\s+',   # "2026-01-17 hingga 2026-01-31"
        r'\s+to\s+',       # "2026-01-17 to 2026-01-31"
        r'\s+until\s+',    # "2026-01-17 until 2026-01-31"
        r'\s*-\s*',        # "2026-01-17 - 2026-01-31"
    ]
    
    # Try YYYY-MM-DD format first
    for sep in separators:
        pattern = rf'(\d{{4}}-\d{{2}}-\d{{2}}){sep}(\d{{4}}-\d{{2}}-\d{{2}})'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            start_date, end_date = match.groups()
            logger.info(f"Detected date range: {start_date} to {end_date}")
            return (start_date, end_date)
    
    # Try DD/MM/YYYY format
    for sep in separators:
        pattern = rf'(\d{{1,2}}[/-]\d{{1,2}}[/-]\d{{4}}){sep}(\d{{1,2}}[/-]\d{{1,2}}[/-]\d{{4}})'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            start_str, end_str = match.groups()
            try:
                # Parse both dates
                start_parts = re.split(r'[/-]', start_str)
                end_parts = re.split(r'[/-]', end_str)
                
                start_date = datetime(int(start_parts[2]), int(start_parts[1]), int(start_parts[0]))
                end_date = datetime(int(end_parts[2]), int(end_parts[1]), int(end_parts[0]))
                
                logger.info(f"Detected date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
                return (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
            except (ValueError, IndexError):
                continue
    
    return None


def extract_passenger_count(text: str) -> int:
    """
    Extract passenger count from text (e.g., "2 orang", "3 passengers")
    
    Supports:
    - Numbers: "2 orang", "3 passengers", "4 adults"
    - Indonesian words: "dua orang", "tiga penumpang"
    
    Args:
        text: Input text containing passenger count
        
    Returns:
        Number of passengers (default: 1)
    """
    text_lower = text.lower()
    
    # Indonesian number words mapping
    indonesian_numbers = {
        'satu': 1, 'dua': 2, 'tiga': 3, 'empat': 4, 'lima': 5,
        'enam': 6, 'tujuh': 7, 'delapan': 8, 'sembilan': 9, 'sepuluh': 10
    }
    
    # Try to find patterns like "2 orang", "3 passengers", "4 adults"
    patterns = [
        r'(\d+)\s*(?:orang|penumpang|passenger|passengers|adult|adults|pax|people)',
        r'(?:untuk|for)\s+(\d+)\s*(?:orang|penumpang|passenger|passengers|adult|adults)?',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            try:
                count = int(match.group(1))
                if 1 <= count <= 9:  # Reasonable passenger count
                    logger.info(f"Detected passenger count: {count}")
                    return count
            except (ValueError, IndexError):
                continue
    
    # Try Indonesian number words
    for word, number in indonesian_numbers.items():
        pattern = rf'{word}\s+(?:orang|penumpang)'
        if re.search(pattern, text_lower):
            logger.info(f"Detected passenger count (Indonesian): {number}")
            return number
    
    # Default to 1 passenger
    return 1


def get_airport_from_city_code(city_code: str) -> Optional[str]:
    """
    Get primary airport code from city code using airports.dat database
    
    For cities with multiple airports (e.g., Tokyo has NRT and HND),
    this returns the primary international airport.
    
    Args:
        city_code: City code (e.g., "TYO", "OSA", "JKT")
        
    Returns:
        Airport IATA code or None if not found
    """
    if not city_code:
        return None
    
    city_code = city_code.strip().upper()
    
    # Manual mapping for common multi-airport cities
    # Prioritize main international airports
    city_to_airport = {
        # City Codes
        "TYO": "NRT", "OSA": "KIX", "JKT": "CGK", "NYC": "JFK",
        "LON": "LHR", "PAR": "CDG", "BKK": "BKK", "SIN": "SIN",

        # City Names (Indonesian & English)
        "JAKARTA": "CGK", "BALI": "DPS", "DENPASAR": "DPS",
        "SURABAYA": "SUB", "YOGYAKARTA": "YIA", "JOGJA": "YIA",
        "MEDAN": "KNO", "MAKASSAR": "UPG",
        "BANDUNG": "BDO", "PALEMBANG": "PLM", "BALIKPAPAN": "BPN",
        "SEMARANG": "SRG", "PONTIANAK": "PNK", "PEKANBARU": "PKU",
        "PADANG": "PDG", "BANDA ACEH": "BTJ", "JAYAPURA": "DJJ",
        "MANADO": "MDC", "MATARAM": "LOP", "KUPANG": "KOE",
        "SAMARINDA": "SRI", "PALANGKARAYA": "PKY", "TERNATE": "TTE",
        "AMBON": "AMQ", "SORONG": "SOQ", "BIAK": "BIK", "TIMIKA": "TIM",
        "JAYAPURA": "DJJ", "MERAUKE": "MKQ", "KENDARI": "KDI",

        # International Cities
        "SINGAPORE": "SIN", "SINGAPURA": "SIN",
        "KUALA LUMPUR": "KUL", "PENANG": "PEN", "JOHOR BAHRU": "JHB",
        "BANGKOK": "BKK", "PHUKET": "HKT", "CHIANG MAI": "CNX", "PATTAYA": "UTP",
        "HO CHI MINH": "SGN", "HANOI": "HAN", "DA NANG": "DAD",
        "SIEM REAP": "REP", "PHNOM PENH": "PNH",
        "MANILA": "MNL", "CEBU": "CEB", "DAVAO": "DVO",

        # Japan
        "TOKYO": "NRT", "OSAKA": "KIX", "KYOTO": "KIX", "KOBE": "UKB",
        "YOKOHAMA": "NRT", "NAGOYA": "NGO", "SAPPORO": "CTS", "FUKUOKA": "FUK",
        "HIROSHIMA": "HIJ", "SENDAI": "SDJ", "KITAKYUSHU": "KKJ",

        # Korea
        "SEOUL": "ICN", "BUSAN": "PUS", "JEJU": "CJU", "DAEGU": "TAE",

        # China
        "BEIJING": "PEK", "SHANGHAI": "PVG", "GUANGZHOU": "CAN",
        "SHENZHEN": "SZX", "CHENGDU": "CTU", "HONG KONG": "HKG",
        "MACAU": "MFM", "TAIPEI": "TPE", "KAOHSIUNG": "KHH",

        # India & South Asia
        "NEW DELHI": "DEL", "MUMBAI": "BOM", "BANGALORE": "BLR",
        "CHENNAI": "MAA", "KOLKATA": "CCU", "COLOMBO": "CMB", "MALE": "MLE",

        # Middle East
        "DUBAI": "DXB", "ABU DHABI": "AUH", "DOHA": "DOH",
        "RIYADH": "RUH", "JEDDAH": "JED", "KUWAIT": "KWI",
        "MANAMA": "BAH", "MUSCAT": "MCT",

        # Australia & NZ
        "SYDNEY": "SYD", "MELBOURNE": "MEL", "PERTH": "PER",
        "BRISBANE": "BNE", "ADELAIDE": "ADL", "CANBERRA": "CBR",
        "GOLD COAST": "OOL", "CAIRNS": "CNS", "AUCKLAND": "AKL",
        "WELLINGTON": "WLG", "CHRISTCHURCH": "CHC",

        # Europe
        "LONDON": "LHR", "PARIS": "CDG", "AMSTERDAM": "AMS",
        "ROME": "FCO", "MILAN": "MXP", "BARCELONA": "BCN",
        "MADRID": "MAD", "BERLIN": "BER", "FRANKFURT": "FRA",
        "ZURICH": "ZRH", "VIENNA": "VIE", "PRAGUE": "PRG",
        "BUDAPEST": "BUD", "WARSAW": "WAW", "ATHENS": "ATH",
        "ISTANBUL": "IST", "MOSCOW": "SVO", "ST PETERSBURG": "LED",

        # Americas
        "NEW YORK": "JFK", "LOS ANGELES": "LAX", "SAN FRANCISCO": "SFO",
        "CHICAGO": "ORD", "MIAMI": "MIA", "TORONTO": "YYZ",
        "VANCOUVER": "YVR", "MONTREAL": "YUL", "MEXICO CITY": "MEX",
        "SAO PAULO": "GRU", "RIO DE JANEIRO": "GIG", "BUENOS AIRES": "EZE",
        "SANTIAGO": "SCL", "LIMA": "LIM", "BOGOTA": "BOG",

        # Africa
        "JOHANNESBURG": "JNB", "CAPE TOWN": "CPT", "CAIRO": "CAI",
        "LAGOS": "LOS", "NAIROBI": "NBO", "ADDIS ABABA": "ADD",
        "DAR ES SALAAM": "DAR", "CASABLANCA": "CMN", "TUNIS": "TUN",
    }
    
    if city_code in city_to_airport:
        logger.info(f"Mapped city code {city_code} -> {city_to_airport[city_code]}")
        return city_to_airport[city_code]
    
    # If not in manual mapping, assume it's already an airport code
    return city_code


def extract_flight_details_from_response(response_text: str) -> Optional[Dict[str, str]]:
    """
    Extract flight details from Gemini response

    This looks for patterns like:
    - Airport codes (JKT, DPS, SIN, etc)
    - Dates (YYYY-MM-DD or DD/MM/YYYY)
    - Date ranges (2026-01-17 dan 2026-01-31)
    - Passenger counts (2 orang, 3 passengers)
    - City names

    Args:
        response_text: Gemini's response

    Returns:
        Dictionary with 'origin', 'destination', 'date'/'date_range', 'adults' or None
    """
    # Look for airport codes
    codes = re.findall(r"\b([A-Z]{3})\b", response_text)
    
    # Normalize city codes to airport codes
    if len(codes) >= 2:
        codes[0] = get_airport_from_city_code(codes[0]) or codes[0]
        codes[1] = get_airport_from_city_code(codes[1]) or codes[1]

    # Try to extract date range first (priority)
    date_range = extract_date_range_from_text(response_text)

    # Extract passenger count
    passenger_count = extract_passenger_count(response_text)

    # Initialize origin/destination from codes if available
    origin = codes[0] if len(codes) >= 1 else None
    destination = codes[1] if len(codes) >= 2 else None

    # If we found a date range and airport codes
    if len(codes) >= 2 and date_range:
        logger.info(f"Extracted flight details with date range: {codes[0]} -> {codes[1]}, {date_range[0]} to {date_range[1]}, {passenger_count} pax")
        return {
            "origin": codes[0],
            "destination": codes[1],
            "date_range": date_range,
            "adults": passenger_count
        }

    # Otherwise, try single date
    date = extract_date_from_text(response_text)

    # If we found codes and a single date
    if len(codes) >= 2 and date:
        logger.info(f"Extracted flight details: {codes[0]} -> {codes[1]} on {date}, {passenger_count} pax")
        return {
            "origin": codes[0],
            "destination": codes[1],
            "date": date,
            "adults": passenger_count
        }

    # If only found 2 codes but no date
    if len(codes) >= 2 and not date and not date_range:
        logger.info(f"Found airport codes {codes[0]}, {codes[1]} but no date, {passenger_count} pax")
        return {
            "origin": codes[0],
            "destination": codes[1],
            "adults": passenger_count
        }

    # Fallback: Try to extract city names if no airport codes found
    if not origin or not destination:
        # Common city to airport mapping
        city_to_airport = {
            "JAKARTA": "CGK", "SURABAYA": "SUB", "BALI": "DPS", "DENPASAR": "DPS",
            "MEDAN": "KNO", "MAKASSAR": "UPG", "BANDUNG": "BDO", "SEMARANG": "SRG",
            "YOGYAKARTA": "YIA", "JOGJA": "YIA",
            "TOKYO": "NRT", "OSAKA": "KIX", "KYOTO": "KIX",
            "SINGAPORE": "SIN", "KUALA LUMPUR": "KUL", "BANGKOK": "BKK",
            "MANILA": "MNL", "HANOI": "HAN", "HO CHI MINH": "SGN",
            "SEOUL": "ICN", "HONG KONG": "HKG", "TAIPEI": "TPE",
            "BEIJING": "PEK", "SHANGHAI": "PVG", "DUBAI": "DXB"
        }

        # Look for "[city] ke [city]" pattern
        from_pattern = r"([A-Za-z]+)\s+ke\s+([A-Za-z]+)"
        match = re.search(from_pattern, response_text, re.IGNORECASE)

        logger.debug(f"Looking for city pattern in: {response_text}")
        logger.debug(f"Pattern match: {match}")

        if match:
            from_city = match.group(1).strip().upper()
            to_city = match.group(2).strip().upper()

            # Clean up city names
            from_city = from_city.split()[0]
            to_city = to_city.split()[0]

            origin = city_to_airport.get(from_city)
            destination = city_to_airport.get(to_city)

            if origin and destination:
                logger.info(f"Found cities: {from_city} -> {to_city}, mapped to {origin} -> {destination}")

                # Return with extracted details
                if date_range:
                    return {
                        "origin": origin,
                        "destination": destination,
                        "date_range": date_range,
                        "adults": passenger_count
                    }
                elif date:
                    return {
                        "origin": origin,
                        "destination": destination,
                        "date": date,
                        "adults": passenger_count
                    }
                else:
                    return {
                        "origin": origin,
                        "destination": destination,
                        "adults": passenger_count
                    }

    logger.debug(f"Could not extract complete flight details from response")
    return None


# ============================================================================
# SMART BEST FLIGHT SCORING SYSTEM
# ============================================================================

# Airline quality ratings (1-5 scale based on reputation, service, reliability)
AIRLINE_QUALITY_RATINGS = {
    # Premium Indonesian airlines
    "GA": 4.5,  # Garuda Indonesia - Flag carrier, premium service
    "QZ": 4.0,  # AirAsia Indonesia - LCC but reliable

    # Good regional airlines
    "SQ": 5.0,  # Singapore Airlines - Excellent
    "MH": 4.5,  # Malaysia Airlines - Good service
    "TG": 4.0,  # Thai Airways - Reliable
    "PR": 4.0,  # Philippine Airlines - Decent
    "CX": 4.5,  # Cathay Pacific - Excellent
    "BR": 4.0,  # EVA Air - Good

    # Indonesian LCCs
    "JT": 3.0,  # Lion Air - Budget, variable quality
    "ID": 3.5,  # Batik Air - Better than Lion
    "OD": 3.5,  # Malindo Air - Decent hybrid
    "SJ": 2.5,  # Sriwijaya Air - Budget
    "IW": 2.5,  # Wings Air - Regional, basic
    "GA": 4.5,  # Garuda (duplicate for Citilink below)

    # Regional LCCs
    "AK": 3.5,  # AirAsia Malaysia
    "FD": 3.0,  # Thai AirAsia
    "Z2": 3.0,  # Zip Air - Budget
    "SL": 3.0,  # Thai Lion Air

    # International
    "EK": 5.0,  # Emirates - Excellent
    "QR": 5.0,  # Qatar Airways - Excellent
    "NH": 4.5,  # ANA - Excellent
    "JL": 4.5,  # Japan Airlines - Excellent
    "OZ": 4.0,  # Asiana - Good
    "KE": 4.0,  # Korean Air - Good
}

def get_airline_quality_score(airline_code: str) -> float:
    """
    Get airline quality rating (1-5 scale)

    Args:
        airline_code: IATA airline code

    Returns:
        Quality score from 1-5, defaults to 3.0 (average)
    """
    return AIRLINE_QUALITY_RATINGS.get(airline_code, 3.0)


def calculate_flight_score(
    flight: Dict[str, Any],
    min_price: float,
    max_price: float,
    origin: str,
    destination: str
) -> float:
    """
    Calculate a composite score for a flight based on multiple factors

    Scoring factors (configurable weights):
    - Price: 40% (lower is better)
    - Airline Quality: 30% (higher is better)
    - Duration: 15% (shorter is better)
    - Stops: 15% (fewer is better)

    Args:
        flight: Flight data dictionary
        min_price: Minimum price in the result set
        max_price: Maximum price in the result set
        origin: Origin airport code
        destination: Destination airport code

    Returns:
        Composite score (0-100, higher is better)
    """
    try:
        # Extract price
        price = float(flight.get("price", {}).get("grandTotal", 0))

        # Extract airline code
        itineraries = flight.get("itineraries", [])
        if not itineraries:
            return 50.0  # Neutral score if no data

        segments = itineraries[0].get("segments", [])
        if not segments:
            return 50.0

        # Get airline code
        airline_code = segments[0].get("operating", {}).get("carrierCode", "")
        if not airline_code:
            airline_code = segments[0].get("carrierCode", "")

        # Get duration in minutes
        duration_iso = itineraries[0].get("duration", "")
        duration_minutes = parse_duration_to_minutes(duration_iso)

        # Count stops
        stops = len(segments) - 1

        # === CALCULATE SCORES ===

        # 1. Price score (40% weight) - lower price = higher score
        if max_price > min_price:
            price_score = 100 * (1 - (price - min_price) / (max_price - min_price))
        else:
            price_score = 50.0

        # 2. Airline quality score (30% weight) - 1-5 scale converted to 0-100
        quality = get_airline_quality_score(airline_code)
        quality_score = (quality / 5.0) * 100

        # 3. Duration score (15% weight) - shorter is better
        # Assuming reasonable range: 1-10 hours
        if duration_minutes > 0:
            duration_score = max(0, 100 * (1 - (duration_minutes - 60) / 540))
            duration_score = min(100, duration_score)
        else:
            duration_score = 50.0

        # 4. Stops score (15% weight) - fewer is better
        if stops == 0:
            stops_score = 100.0  # Direct flight
        elif stops == 1:
            stops_score = 70.0   # One stop
        else:
            stops_score = 40.0   # Multiple stops

        # === COMPOSITE SCORE ===
        composite_score = (
            (price_score * 0.40) +
            (quality_score * 0.30) +
            (duration_score * 0.15) +
            (stops_score * 0.15)
        )

        logger.debug(
            f"Flight score: {composite_score:.1f} | "
            f"Price: {price_score:.1f}, Quality: {quality_score:.1f}, "
            f"Duration: {duration_score:.1f}, Stops: {stops_score:.1f} | "
            f"Airline: {airline_code}, Price: {price:.0f}"
        )

        return composite_score

    except Exception as e:
        logger.warning(f"Error calculating flight score: {e}")
        return 50.0  # Neutral score on error


def parse_duration_to_minutes(duration_iso: str) -> int:
    """
    Parse ISO 8601 duration to minutes

    Args:
        duration_iso: Duration in ISO format (e.g., "PT2H30M")

    Returns:
        Duration in minutes
    """
    try:
        import re
        match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?', duration_iso)
        if match:
            hours = int(match.group(1) or 0)
            minutes = int(match.group(2) or 0)
            return hours * 60 + minutes
        return 0
    except Exception:
        return 0


def find_best_flight(
    flights_with_dates: list,
    origin: str,
    destination: str
) -> tuple:
    """
    Find the best flight using smart scoring (not just cheapest)

    Args:
        flights_with_dates: List of (date, price, flight_data) tuples
        origin: Origin airport code
        destination: Destination airport code

    Returns:
        Tuple of (best_flight, best_date, best_score, all_scores)
    """
    if not flights_with_dates:
        return None, None, 0.0, []

    # Calculate min/max prices for normalization
    prices = [price for _, price, _ in flights_with_dates]
    min_price = min(prices) if prices else 0
    max_price = max(prices) if prices else 0

    logger.info(f"Scoring {len(flights_with_dates)} flights (price range: {min_price:.0f} - {max_price:.0f})")

    # Score all flights
    scored_flights = []
    for date, price, flight in flights_with_dates:
        score = calculate_flight_score(flight, min_price, max_price, origin, destination)
        scored_flights.append((score, date, price, flight))

    # Sort by score (highest first)
    scored_flights.sort(key=lambda x: x[0], reverse=True)

    # Get the best one
    best_score, best_date, best_price, best_flight = scored_flights[0]

    logger.info(f"Best flight: {best_date} | Score: {best_score:.1f} | Price: {best_price:.0f}")

    return best_flight, best_date, best_score, scored_flights



def search_flights_in_date_range(
    origin: str,
    destination: str,
    start_date: str,
    end_date: str,
    adults: int = 1,
    max_searches: int = 30
) -> Dict[str, Any]:
    """
    Search for cheapest flight across a date range
    
    This function searches multiple dates to find the best deal.
    It's smart about API usage and provides progress feedback.
    
    Args:
        origin: Origin airport code
        destination: Destination airport code
        start_date: Start of date range (YYYY-MM-DD)
        end_date: End of date range (YYYY-MM-DD)
        adults: Number of passengers
        max_searches: Maximum number of API calls to make (safety limit)
        
    Returns:
        Dictionary with:
        - success: bool
        - cheapest_flight: flight data or None
        - cheapest_date: date string or None
        - cheapest_price: price or None
        - all_results: list of (date, price, flight_data) tuples
        - error: error message if failed
    """
    try:
        from datetime import datetime, timedelta
        
        # Parse dates
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Calculate number of days
        delta = end_dt - start_dt
        num_days = delta.days + 1
        
        if num_days > max_searches:
            logger.warning(f"Date range too large ({num_days} days), limiting to {max_searches} days")
            num_days = max_searches
        
        logger.info(f"Searching {num_days} dates from {start_date} to {end_date}")

        all_results = []

        # Search each date
        for i in range(num_days):
            current_date = start_dt + timedelta(days=i)
            date_str = current_date.strftime("%Y-%m-%d")

            logger.info(f"Searching date {i+1}/{num_days}: {date_str}")

            # Search flights for this date
            result = search_flights(origin, destination, date_str, adults)

            if result["success"] and result["data"]:
                # Get all flights for this date
                flights = result["data"]

                for flight in flights:
                    try:
                        price = float(flight.get("price", {}).get("grandTotal", float('inf')))

                        # Store this result
                        all_results.append((date_str, price, flight))

                    except (ValueError, TypeError):
                        continue

        if all_results:
            # Use smart scoring to find the best flight
            best_flight, best_date, best_score, scored_flights = find_best_flight(
                all_results, origin, destination
            )

            # Get the price of the best flight
            best_price = float(best_flight.get("price", {}).get("grandTotal", 0))

            logger.info(f"Found best flight on {best_date} | Score: {best_score:.1f} | Price: {best_price:.0f}")

            return {
                "success": True,
                "cheapest_flight": best_flight,  # Keeping key name for compatibility
                "cheapest_date": best_date,
                "cheapest_price": best_price,
                "all_results": all_results,
                "best_score": best_score,  # New: Score for transparency
                "scored_flights": scored_flights[:5],  # New: Top 5 scored flights
                "error": None
            }
        else:
            logger.warning("No flights found in date range")
            return {
                "success": False,
                "cheapest_flight": None,
                "cheapest_date": None,
                "cheapest_price": None,
                "all_results": [],
                "best_score": 0,
                "scored_flights": [],
                "error": "🔍 Maaf, belum ada jadwal penerbangan untuk tanggal yang dipilih. Coba tanggal lain yang lebih dekat ya! Atau bilang 'cari yang termurah' biar aku carikan opsi terbaik dalam 7 hari ke depan. ✈️"
            }

    except Exception as e:
        logger.error(f"Error in date range search: {e}", exc_info=True)
        return {
            "success": False,
            "cheapest_flight": None,
            "cheapest_date": None,
            "cheapest_price": None,
            "all_results": [],
            "best_score": 0,
            "scored_flights": [],
            "error": f"⚠️ Maaf, ada masalah saat mencari tiket. Coba lagi dalam beberapa detik ya! 😊"
        }


def search_cheapest_flight_next_week(
    origin: str,
    destination: str,
    adults: int = 1
) -> Dict[str, Any]:
    """
    Convenience function to search for best flight in the next 7 days using smart scoring

    This is the default smart search that balances price, quality, and convenience.

    Args:
        origin: Origin airport code
        destination: Destination airport code
        adults: Number of passengers

    Returns:
        Same format as search_flights_in_date_range
    """
    from datetime import datetime, timedelta

    today = datetime.now()
    # Start from tomorrow to avoid Amadeus API 400 error (same-day booking not allowed)
    start_date = (today + timedelta(days=1)).strftime("%Y-%m-%d")
    end_date = (today + timedelta(days=7)).strftime("%Y-%m-%d")

    logger.info(f"Searching best flight for next week: {start_date} to {end_date}")

    return search_flights_in_date_range(
        origin=origin,
        destination=destination,
        start_date=start_date,
        end_date=end_date,
        adults=adults,
        max_searches=7
    )


def format_date_range_results(result: Dict[str, Any], origin: str, destination: str) -> str:
    """
    Format date range search results for display using smart best scoring

    Args:
        result: Result from search_flights_in_date_range
        origin: Origin airport code
        destination: Destination airport code

    Returns:
        Formatted string for display
    """
    if not result["success"]:
        return f"❌ {result.get('error', 'No flights found')}"

    best_flight = result["cheapest_flight"]  # Keeping key for compatibility
    best_date = result["cheapest_date"]
    best_price = result["cheapest_price"]
    best_score = result.get("best_score", 0)
    scored_flights = result.get("scored_flights", [])

    # Smart recommendation based on score
    if best_score >= 75:
        recommendation_text = "✨ **Rekomendasi Terbaik Ditemukan!**"
        subtitle = "Pilihan tepat - harga & kualitas seimbang"
    elif best_score >= 60:
        recommendation_text = "🎯 **Pilihan Terbaik Untuk Kamu!**"
        subtitle = "Value terbaik antara harga dan kenyamanan"
    else:
        recommendation_text = "💡 **Pilihan Tersedia**"
        subtitle = "Berikut opsi terbaik dari hasil pencarian"

    formatted = f"{recommendation_text}\n"
    formatted += f"📊 *{subtitle}*\n\n"
    formatted += f"📅 **Tanggal**: {best_date}\n"

    # Get price in IDR
    price = best_flight.get("price", {})
    currency = price.get("currency", "EUR")

    if currency != "IDR":
        try:
            rate = get_exchange_rate(currency, "IDR")
            if rate:
                price_idr = best_price * rate
                formatted += f"💰 **Harga**: Rp {price_idr:,.0f}\n"
            else:
                formatted += f"💰 **Harga**: {currency} {best_price}\n"
        except:
            formatted += f"💰 **Harga**: {currency} {best_price}\n"
    else:
        formatted += f"💰 **Harga**: Rp {best_price:,.0f}\n"

    # Get flight details
    itineraries = best_flight.get("itineraries", [])
    if itineraries:
        first_leg = itineraries[0]
        segments = first_leg.get("segments", [])

        if segments:
            first_segment = segments[0]
            last_segment = segments[-1]

            departure = first_segment.get("departure", {})
            arrival = last_segment.get("arrival", {})

            departure_time = departure.get("at", "N/A").replace("T", " ")
            arrival_time = arrival.get("at", "N/A").replace("T", " ")

            # Get airline
            airline_code = first_segment.get("operating", {}).get("carrierCode", "")
            if not airline_code:
                airline_code = first_segment.get("carrierCode", "")

            origin_airport = departure.get("iataCode", "")
            dest_airport = arrival.get("iataCode", "")
            airline_name = get_airline_name_safe(airline_code, origin_airport, dest_airport)

            # Get airline quality for badge
            quality_score = get_airline_quality_score(airline_code)
            if quality_score >= 4.5:
                quality_badge = "⭐⭐⭐⭐⭐ Premium"
            elif quality_score >= 4.0:
                quality_badge = "⭐⭐⭐⭐ Bagus"
            elif quality_score >= 3.0:
                quality_badge = "⭐⭐⭐ Standar"
            else:
                quality_badge = "⭐⭐ Hemat"

            # Duration
            duration_iso = first_leg.get("duration", "")
            duration_readable = format_duration(duration_iso)

            formatted += f"✈️  **Maskapai**: {airline_name} ({quality_badge})\n"
            formatted += f"🛫 **Berangkat**: {departure_time}\n"
            formatted += f"🛬 **Tiba**: {arrival_time}\n"
            formatted += f"⏱️  **Durasi**: {duration_readable}\n"
            formatted += f"📍 **Transit**: {len(segments) - 1} kali\n"

    # Add score breakdown for transparency
    if best_score > 0:
        formatted += f"\n📊 **Score**: {best_score:.0f}/100 (berdasarkan harga, kualitas maskapai, durasi & transit)\n"

    # Show top alternatives if available
    if scored_flights and len(scored_flights) > 1:
        formatted += f"\n💡 **Opsi Lainnya**:\n"
        for i, (score, date, price, flight) in enumerate(scored_flights[1:4], 2):  # Show next 3
            if score > 50:  # Only show decent options
                # Get airline for this flight
                try:
                    itin = flight.get("itineraries", [{}])[0]
                    segs = itin.get("segments", [])
                    if segs:
                        code = segs[0].get("operating", {}).get("carrierCode", segs[0].get("carrierCode", ""))
                        name = get_airline_name_safe(code, origin, destination)

                        # Format price
                        curr = flight.get("price", {}).get("currency", "IDR")
                        pr = float(price)
                        if curr != "IDR":
                            rate = get_exchange_rate(curr, "IDR")
                            if rate:
                                pr_fmt = f"Rp {pr * rate:,.0f}"
                            else:
                                pr_fmt = f"{curr} {pr:.0f}"
                        else:
                            pr_fmt = f"Rp {pr:,.0f}"

                        formatted += f"  {i}. {name} - {date} | {pr_fmt} | Score: {score:.0f}\n"
                except:
                    continue

    return formatted


"""
Google Flights API Integration via RapidAPI

This module handles flight search using Google Flights API through RapidAPI.
It serves as the primary flight search provider with Amadeus as fallback.
"""

import logging
import requests
from typing import Dict, Any, Optional
from datetime import datetime

from src.config import RAPIDAPI_KEY, RAPIDAPI_HOST, GOOGLE_FLIGHTS_CONFIGURED

logger = logging.getLogger(__name__)

# Google Flights API endpoints
GOOGLE_FLIGHTS_ONEWAY_URL = f"https://{RAPIDAPI_HOST}/flights/search-oneway"
GOOGLE_FLIGHTS_ROUNDTRIP_URL = f"https://{RAPIDAPI_HOST}/flights/search-roundtrip"

# USD to IDR conversion rate (approximate - update periodically)
USD_TO_IDR_RATE = 15800


def detect_target_currency(origin: str) -> str:
    """
    Detect target currency based on origin airport code

    Args:
        origin: Origin airport code (e.g., "CGK")

    Returns:
        Target currency code ("IDR" for Indonesian airports, "USD" for others)
    """
    # List of Indonesian airports
    indonesian_airports = {
        "CGK",  # Jakarta - Soekarno-Hatta
        "DPS",  # Bali - Ngurah Rai
        "SUB",  # Surabaya - Juanda
        "JOG",  # Yogyakarta - Adisucipto
        "YIA",  # Yogyakarta - Yogyakarta International
        "UPG",  # Makassar - Sultan Hasanuddin
        "BDO",  # Bandung - Husein
        "BTH",  # Batam - Hang Nadim
        "PKU",  # Pekanbaru - Sultan Syarif
        "PLM",  # Palembang - Sultan Mahmud
        "BPN",  # Balikpapan - Sepinggan
        "SRG",  # Semarang - Ahmad Yani
        "LOP",  # Lombok - Lombok International
        "MDC",  # Manado - Sam Ratulangi
        "PNK",  # Pontianak - Supadio
        "KNO",  # Medan - Kualanamu
        "BTJ",  # Banda Aceh - Sultan Iskandar Muda
        "MDN",  # Manado - Sam Ratulangi
        "DJJ",  # Jayapura - Sentani
        "BIK",  # Biak - Frans Kaisiepo
        "GTO",  # Gorontalo - Jalaluddin
        "UJG",  # Pontianak - Supadio
    }

    # Return IDR for Indonesian airports, USD for others
    return "IDR" if origin.upper() in indonesian_airports else "USD"


def search_google_flights(
    origin: str,
    destination: str,
    departure_date: str,
    adults: int = 1,
    return_date: str = None,
    trip_type: str = "oneway"
) -> Dict[str, Any]:
    """
    Search for flights using Google Flights API via RapidAPI
    
    Args:
        origin: Origin airport code (e.g., "CGK")
        destination: Destination airport code (e.g., "NRT")
        departure_date: Departure date in YYYY-MM-DD format
        adults: Number of adult passengers (default: 1)
        return_date: Return date for round-trip (YYYY-MM-DD format, optional)
        trip_type: "oneway" or "roundtrip" (default: "oneway")
        
    Returns:
        Dictionary with success status, flight data, and error info
        Format: {
            "success": bool,
            "data": list of flight offers,
            "error": str or None,
            "provider": "google_flights"
        }
    """
    if not GOOGLE_FLIGHTS_CONFIGURED:
        logger.error("Google Flights API not configured (missing RAPIDAPI_KEY)")
        return {
            "success": False,
            "data": [],
            "error": "Google Flights API not configured",
            "provider": "google_flights"
        }
    
    try:
        # Detect target currency based on origin
        target_currency = detect_target_currency(origin)

        # Determine endpoint and parameters based on trip type
        if trip_type == "roundtrip" and return_date:
            api_url = GOOGLE_FLIGHTS_ROUNDTRIP_URL
            logger.info(f"Searching Google Flights (ROUNDTRIP): {origin} -> {destination} on {departure_date}, return {return_date} for {adults} pax")
            params = {
                "departureId": origin,
                "arrivalId": destination,
                "outboundDate": departure_date,
                "returnDate": return_date,
                "adults": str(adults),
                "currency": target_currency,
                "hl": "id" if target_currency == "IDR" else "en",
                "gl": "id" if target_currency == "IDR" else "us"
            }
        else:
            api_url = GOOGLE_FLIGHTS_ONEWAY_URL
            logger.info(f"Searching Google Flights (ONEWAY): {origin} -> {destination} on {departure_date} for {adults} pax")
            params = {
                "departureId": origin,
                "arrivalId": destination,
                "outboundDate": departure_date,
                "adults": str(adults),
                "currency": target_currency,
                "hl": "id" if target_currency == "IDR" else "en",
                "gl": "id" if target_currency == "IDR" else "us"
            }
        
        headers = {
            "x-rapidapi-host": RAPIDAPI_HOST,
            "x-rapidapi-key": RAPIDAPI_KEY
        }
        
        # Make API request
        response = requests.get(
            api_url,
            params=params,
            headers=headers,
            timeout=30
        )
        
        # Check response status
        response.raise_for_status()
        
        # Parse response
        data = response.json()
        
        # Format response to match our standard format
        formatted_data = format_google_flights_response(data, trip_type, origin)
        
        logger.info(f"Google Flights search successful: {len(formatted_data)} flights found")
        
        return {
            "success": True,
            "data": formatted_data,
            "error": None,
            "provider": "google_flights"
        }
        
    except requests.exceptions.Timeout:
        error_msg = "Google Flights API timeout"
        logger.error(error_msg)
        return {
            "success": False,
            "data": [],
            "error": error_msg,
            "provider": "google_flights"
        }
        
    except requests.exceptions.HTTPError as e:
        error_msg = f"Google Flights API HTTP error: {e.response.status_code}"
        logger.error(f"{error_msg} - {e.response.text[:200]}")
        return {
            "success": False,
            "data": [],
            "error": error_msg,
            "provider": "google_flights"
        }
        
    except Exception as e:
        error_msg = f"Google Flights API error: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "success": False,
            "data": [],
            "error": error_msg,
            "provider": "google_flights"
        }


def format_google_flights_response(data: Dict[str, Any], trip_type: str = "oneway", origin: str = None) -> list:
    """
    Convert Google Flights API response to our standard format
    
    Args:
        data: Raw response from Google Flights API
        trip_type: "oneway" or "roundtrip"
        
    Returns:
        List of flight offers in standard format matching Amadeus structure
    """
    try:
        formatted_flights = []
        
        # Get the actual data structure from response
        response_data = data.get("data", {})
        
        if not response_data:
            logger.warning("Google Flights response contains no data")
            return []
            
        # Detect target currency based on origin
        target_currency = detect_target_currency(origin)

        # Combine topFlights and otherFlights
        all_flights = []
        all_flights.extend(response_data.get("topFlights") or [])
        all_flights.extend(response_data.get("otherFlights") or [])

        for flight in all_flights:
            # Extract price information (API returns price in the requested currency)
            price_value = flight.get("price")
            if price_value is None:
                continue  # Skip flights without price

            # Use price directly from API (already in target currency)
            total_price = str(float(price_value))
            currency = target_currency
            
            # Extract segments
            segments = []
            flight_segments = flight.get("segments", [])
            
            for seg in flight_segments:
                # Build datetime strings from date and time
                dep_date = seg.get("departureDate", "")
                dep_time = seg.get("departureTime", "")
                arr_date = seg.get("arrivalDate", "")
                arr_time = seg.get("arrivalTime", "")
                
                segment = {
                    "departure": {
                        "at": f"{dep_date}T{dep_time}:00" if dep_date and dep_time else "",
                        "iataCode": seg.get("departureAirportCode", "")
                    },
                    "arrival": {
                        "at": f"{arr_date}T{arr_time}:00" if arr_date and arr_time else "",
                        "iataCode": seg.get("arrivalAirportCode", "")
                    },
                    "carrierCode": seg.get("airlineCode", ""),
                    "number": seg.get("flightNumber", ""),
                    "operating": {
                        "carrierCode": seg.get("airlineCode", "")
                    },
                    "duration": f"PT{seg.get('duration', 0)}M",
                    "aircraft": seg.get("aircraftName", ""),
                    "airlineName": seg.get("airlineName", "")
                }
                segments.append(segment)
            
            # Calculate total duration in ISO 8601 format
            duration_mins = flight.get("durationMinutes", 0)
            hours = duration_mins // 60
            mins = duration_mins % 60
            duration_str = f"PT{hours}H{mins}M"
            
            # Create flight offer in standard format
            flight_offer = {
                "price": {
                    "grandTotal": total_price,
                    "currency": currency
                },
                "itineraries": [{
                    "duration": duration_str,
                    "segments": segments
                }],
                # Extra info specific to Google Flights
                "airlineName": flight.get("airlineName", ""),
                "airlineCode": flight.get("airlineCode", ""),
                "stops": flight.get("stops", 0),
                "hasStop": flight.get("hasStop", False),
                "departureTime": flight.get("departureTime", ""),
                "arrivalTime": flight.get("arrivalTime", ""),
                "provider": "google_flights"
            }
            
            formatted_flights.append(flight_offer)
        
        return formatted_flights
        
    except Exception as e:
        logger.error(f"Error formatting Google Flights response: {e}", exc_info=True)
        return []


def test_google_flights_connection() -> bool:
    """
    Test Google Flights API connection
    
    Returns:
        True if connection successful, False otherwise
    """
    if not GOOGLE_FLIGHTS_CONFIGURED:
        logger.warning("Google Flights API not configured")
        return False
    
    try:
        # Test with a simple search
        result = search_google_flights("CGK", "DPS", "2025-12-20", 1)
        return result["success"]
    except Exception as e:
        logger.error(f"Google Flights connection test failed: {e}")
        return False

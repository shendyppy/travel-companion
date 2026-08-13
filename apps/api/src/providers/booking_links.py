"""
Booking Links Module

Generates deep links to popular flight booking platforms
for seamless user experience.
"""

import logging
from typing import Dict
from urllib.parse import urlencode
from datetime import datetime

logger = logging.getLogger(__name__)


def generate_traveloka_link(
    origin: str,
    destination: str,
    departure_date: str,
    passengers: int = 1,
    return_date: str = None
) -> str:
    """
    Generate deep link to Traveloka flight search
    
    Args:
        origin: Origin airport code (e.g., "CGK")
        destination: Destination airport code (e.g., "DPS")
        departure_date: Departure date in YYYY-MM-DD format
        passengers: Number of passengers
        return_date: Optional return date for round trip
        
    Returns:
        Traveloka search URL
    """
    try:
        # Traveloka URL format
        # https://www.traveloka.com/en-id/flight/fullsearch?
        # ap=CGK.DPS&dt=2025-12-20.NA&ps=1.0.0&sc=ECONOMY
        
        # Format dates
        dep_date = departure_date.replace("-", "")
        ret_date = return_date.replace("-", "") if return_date else "NA"
        
        # Build URL
        base_url = "https://www.traveloka.com/en-id/flight/fullsearch"
        params = {
            "ap": f"{origin}.{destination}",
            "dt": f"{dep_date}.{ret_date}",
            "ps": f"{passengers}.0.0",  # adults.children.infants
            "sc": "ECONOMY"
        }
        
        url = f"{base_url}?{urlencode(params)}"
        logger.debug(f"Generated Traveloka link: {url}")
        return url
        
    except Exception as e:
        logger.error(f"Error generating Traveloka link: {e}")
        return "https://www.traveloka.com/en-id/flight"


def generate_tiketcom_link(
    origin: str,
    destination: str,
    departure_date: str,
    passengers: int = 1,
    return_date: str = None
) -> str:
    """
    Generate deep link to Tiket.com flight search
    
    Args:
        origin: Origin airport code (e.g., "CGK")
        destination: Destination airport code (e.g., "DPS")
        departure_date: Departure date in YYYY-MM-DD format
        passengers: Number of passengers
        return_date: Optional return date for round trip
        
    Returns:
        Tiket.com search URL
    """
    try:
        # Tiket.com URL format
        # https://www.tiket.com/pesawat/cari?
        # d=CGK&a=DPS&date=2025-12-20&ret_date=&adult=1&child=0&infant=0
        
        params = {
            "d": origin,
            "a": destination,
            "date": departure_date,
            "ret_date": return_date or "",
            "adult": str(passengers),
            "child": "0",
            "infant": "0"
        }
        
        base_url = "https://www.tiket.com/pesawat/cari"
        url = f"{base_url}?{urlencode(params)}"
        logger.debug(f"Generated Tiket.com link: {url}")
        return url
        
    except Exception as e:
        logger.error(f"Error generating Tiket.com link: {e}")
        return "https://www.tiket.com/pesawat"


def generate_skyscanner_link(
    origin: str,
    destination: str,
    departure_date: str,
    passengers: int = 1,
    return_date: str = None
) -> str:
    """
    Generate deep link to Skyscanner flight search
    
    Args:
        origin: Origin airport code (e.g., "CGK")
        destination: Destination airport code (e.g., "DPS")
        departure_date: Departure date in YYYY-MM-DD format
        passengers: Number of passengers
        return_date: Optional return date for round trip
        
    Returns:
        Skyscanner search URL
    """
    try:
        # Skyscanner URL format
        # https://www.skyscanner.co.id/transport/flights/
        # cgk/dps/251220/251227/?adults=1&adultsv2=1&children=0&childrenv2=&infants=0
        
        # Format dates as YYMMDD
        try:
            dep_dt = datetime.strptime(departure_date, "%Y-%m-%d")
            dep_formatted = dep_dt.strftime("%y%m%d")
            
            if return_date:
                ret_dt = datetime.strptime(return_date, "%Y-%m-%d")
                ret_formatted = ret_dt.strftime("%y%m%d")
            else:
                ret_formatted = ""
        except ValueError:
            # Fallback if date parsing fails
            dep_formatted = departure_date.replace("-", "")[2:]
            ret_formatted = return_date.replace("-", "")[2:] if return_date else ""
        
        # Build URL path
        origin_lower = origin.lower()
        dest_lower = destination.lower()
        
        if return_date:
            path = f"{origin_lower}/{dest_lower}/{dep_formatted}/{ret_formatted}"
        else:
            path = f"{origin_lower}/{dest_lower}/{dep_formatted}"
        
        params = {
            "adults": str(passengers),
            "adultsv2": str(passengers),
            "children": "0",
            "childrenv2": "",
            "infants": "0"
        }
        
        base_url = f"https://www.skyscanner.co.id/transport/flights/{path}/"
        url = f"{base_url}?{urlencode(params)}"
        logger.debug(f"Generated Skyscanner link: {url}")
        return url
        
    except Exception as e:
        logger.error(f"Error generating Skyscanner link: {e}")
        return "https://www.skyscanner.co.id/"


def format_booking_links(
    origin: str,
    destination: str,
    departure_date: str,
    passengers: int = 1,
    return_date: str = None
) -> str:
    """
    Generate and format all booking platform links for display
    
    Args:
        origin: Origin airport code
        destination: Destination airport code
        departure_date: Departure date in YYYY-MM-DD format
        passengers: Number of passengers
        return_date: Optional return date for round trip
        
    Returns:
        Formatted string with all booking links
    """
    try:
        traveloka = generate_traveloka_link(origin, destination, departure_date, passengers, return_date)
        tiketcom = generate_tiketcom_link(origin, destination, departure_date, passengers, return_date)
        skyscanner = generate_skyscanner_link(origin, destination, departure_date, passengers, return_date)
        
        formatted = "\n🔗 **Booking Links:**\n"
        formatted += f"  • [Traveloka]({traveloka})\n"
        formatted += f"  • [Tiket.com]({tiketcom})\n"
        formatted += f"  • [Skyscanner]({skyscanner})\n"
        
        return formatted
        
    except Exception as e:
        logger.error(f"Error formatting booking links: {e}")
        return "\n🔗 **Booking Links:** (Error generating links)\n"


def get_booking_links_dict(
    origin: str,
    destination: str,
    departure_date: str,
    passengers: int = 1,
    return_date: str = None
) -> Dict[str, str]:
    """
    Get booking links as a dictionary
    
    Useful for storing in trip context
    
    Args:
        origin: Origin airport code
        destination: Destination airport code
        departure_date: Departure date in YYYY-MM-DD format
        passengers: Number of passengers
        return_date: Optional return date for round trip
        
    Returns:
        Dictionary mapping platform name to URL
    """
    return {
        "traveloka": generate_traveloka_link(origin, destination, departure_date, passengers, return_date),
        "tiketcom": generate_tiketcom_link(origin, destination, departure_date, passengers, return_date),
        "skyscanner": generate_skyscanner_link(origin, destination, departure_date, passengers, return_date),
    }

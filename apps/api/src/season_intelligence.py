"""
Season Intelligence Module

Provides seasonal pricing insights and best time to travel recommendations
for popular destinations. This helps the AI agent give smart recommendations
about when to search for flights.
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SeasonInfo:
    """Information about a travel season for a destination"""
    month_range: Tuple[int, int]  # (start_month, end_month)
    season_name: str  # e.g., "Low Season", "Peak Season"
    price_level: str  # "cheap", "moderate", "expensive"
    description: str  # Why this season has this pricing
    recommendation: str  # Travel tip for this season


# Destination season database
# Format: destination_code -> list of SeasonInfo
DESTINATION_SEASONS: Dict[str, List[SeasonInfo]] = {
    # Japan destinations
    "NRT": [  # Tokyo Narita
        SeasonInfo(
            month_range=(1, 2),
            season_name="Winter Low Season",
            price_level="cheap",
            description="Setelah Tahun Baru, turis berkurang drastis",
            recommendation="Waktu terbaik untuk hemat! Cuaca dingin tapi tiket murah 30-40%"
        ),
        SeasonInfo(
            month_range=(3, 4),
            season_name="Sakura Peak Season",
            price_level="expensive",
            description="Musim bunga sakura, peak tourist season",
            recommendation="Hindari kalau budget terbatas. Harga naik 50-80% dari normal"
        ),
        SeasonInfo(
            month_range=(5, 6),
            season_name="Early Summer",
            price_level="moderate",
            description="Setelah sakura, sebelum musim panas",
            recommendation="Harga mulai turun, cuaca nyaman untuk jalan-jalan"
        ),
        SeasonInfo(
            month_range=(7, 8),
            season_name="Summer Peak",
            price_level="expensive",
            description="Liburan sekolah, festival musim panas",
            recommendation="Ramai dan mahal. Pertimbangkan Sept-Okt sebagai alternatif"
        ),
        SeasonInfo(
            month_range=(9, 11),
            season_name="Autumn Sweet Spot",
            price_level="moderate",
            description="Musim gugur, cuaca bagus, harga wajar",
            recommendation="Salah satu waktu terbaik! Daun merah + harga reasonable"
        ),
        SeasonInfo(
            month_range=(12, 12),
            season_name="Year-End Peak",
            price_level="expensive",
            description="Natal dan Tahun Baru",
            recommendation="Sangat mahal. Kalau bisa, tunda ke Januari"
        ),
    ],
    "HND": [  # Tokyo Haneda - same as NRT
        SeasonInfo(
            month_range=(1, 2),
            season_name="Winter Low Season",
            price_level="cheap",
            description="Setelah Tahun Baru, turis berkurang drastis",
            recommendation="Waktu terbaik untuk hemat! Cuaca dingin tapi tiket murah 30-40%"
        ),
        SeasonInfo(
            month_range=(3, 4),
            season_name="Sakura Peak Season",
            price_level="expensive",
            description="Musim bunga sakura, peak tourist season",
            recommendation="Hindari kalau budget terbatas. Harga naik 50-80% dari normal"
        ),
        SeasonInfo(
            month_range=(5, 6),
            season_name="Early Summer",
            price_level="moderate",
            description="Setelah sakura, sebelum musim panas",
            recommendation="Harga mulai turun, cuaca nyaman untuk jalan-jalan"
        ),
        SeasonInfo(
            month_range=(7, 8),
            season_name="Summer Peak",
            price_level="expensive",
            description="Liburan sekolah, festival musim panas",
            recommendation="Ramai dan mahal. Pertimbangkan Sept-Okt sebagai alternatif"
        ),
        SeasonInfo(
            month_range=(9, 11),
            season_name="Autumn Sweet Spot",
            price_level="moderate",
            description="Musim gugur, cuaca bagus, harga wajar",
            recommendation="Salah satu waktu terbaik! Daun merah + harga reasonable"
        ),
        SeasonInfo(
            month_range=(12, 12),
            season_name="Year-End Peak",
            price_level="expensive",
            description="Natal dan Tahun Baru",
            recommendation="Sangat mahal. Kalau bisa, tunda ke Januari"
        ),
    ],
    
    # Singapore
    "SIN": [
        SeasonInfo(
            month_range=(1, 2),
            season_name="Chinese New Year Peak",
            price_level="expensive",
            description="Imlek, banyak turis dari Asia",
            recommendation="Hindari minggu Imlek. Harga naik 40-60%"
        ),
        SeasonInfo(
            month_range=(3, 5),
            season_name="Hot Season",
            price_level="moderate",
            description="Panas tapi bukan peak season",
            recommendation="Harga stabil, good deals kadang muncul"
        ),
        SeasonInfo(
            month_range=(6, 8),
            season_name="Great Singapore Sale",
            price_level="moderate",
            description="Shopping season, tapi bukan peak flights",
            recommendation="Bagus untuk shopping trip, flight harga normal"
        ),
        SeasonInfo(
            month_range=(9, 11),
            season_name="Low Season",
            price_level="cheap",
            description="Setelah liburan sekolah",
            recommendation="Waktu terbaik untuk hemat! Tiket bisa 20-30% lebih murah"
        ),
        SeasonInfo(
            month_range=(12, 12),
            season_name="Year-End Peak",
            price_level="expensive",
            description="Natal dan Tahun Baru",
            recommendation="Sangat ramai dan mahal. Booking jauh-jauh hari kalau mau"
        ),
    ],
    
    # Thailand - Bangkok
    "BKK": [
        SeasonInfo(
            month_range=(1, 2),
            season_name="Cool Season Peak",
            price_level="expensive",
            description="Cuaca terbaik, banyak turis",
            recommendation="Cuaca perfect tapi mahal. Book early untuk deal bagus"
        ),
        SeasonInfo(
            month_range=(3, 5),
            season_name="Hot Season",
            price_level="moderate",
            description="Sangat panas, turis berkurang",
            recommendation="Harga turun, tapi siap-siap kepanasan!"
        ),
        SeasonInfo(
            month_range=(6, 10),
            season_name="Rainy Season Low",
            price_level="cheap",
            description="Musim hujan, low season",
            recommendation="Paling murah! Hujan biasanya cuma sore, masih bisa jalan"
        ),
        SeasonInfo(
            month_range=(11, 12),
            season_name="Cool Season Start",
            price_level="moderate",
            description="Mulai sejuk, turis mulai banyak",
            recommendation="Sweet spot sebelum peak season Januari"
        ),
    ],
    
    # Add more destinations as needed
    # Malaysia - Kuala Lumpur
    "KUL": [
        SeasonInfo(
            month_range=(1, 2),
            season_name="Dry Season",
            price_level="moderate",
            description="Cuaca bagus, turis cukup banyak",
            recommendation="Harga stabil, cuaca nyaman"
        ),
        SeasonInfo(
            month_range=(3, 5),
            season_name="Hot \u0026 Humid",
            price_level="cheap",
            description="Panas dan lembab",
            recommendation="Tiket murah, tapi siap-siap AC jalan terus"
        ),
        SeasonInfo(
            month_range=(6, 9),
            season_name="School Holiday Peak",
            price_level="expensive",
            description="Liburan sekolah Indonesia \u0026 Malaysia",
            recommendation="Ramai karena dekat. Book early atau hindari weekend"
        ),
        SeasonInfo(
            month_range=(10, 12),
            season_name="Year-End Shopping",
            price_level="moderate",
            description="Sale season, turis belanja",
            recommendation="Bagus untuk shopping trip, flight harga wajar"
        ),
    ],
}


def get_season_info(destination: str, month: int = None) -> Optional[SeasonInfo]:
    """
    Get season information for a destination
    
    Args:
        destination: Airport code (e.g., "NRT", "SIN")
        month: Month number (1-12). If None, uses current month
        
    Returns:
        SeasonInfo object or None if not found
    """
    if month is None:
        month = datetime.now().month
    
    destination = destination.upper()
    
    if destination not in DESTINATION_SEASONS:
        logger.debug(f"No season data for destination: {destination}")
        return None
    
    # Find matching season
    for season in DESTINATION_SEASONS[destination]:
        start, end = season.month_range
        if start <= month <= end:
            return season
    
    return None


def get_cheapest_months(destination: str, months_ahead: int = 6) -> List[Tuple[int, str, str]]:
    """
    Get the cheapest months to travel to a destination
    
    Args:
        destination: Airport code
        months_ahead: How many months ahead to look
        
    Returns:
        List of (month_number, month_name, reason) tuples, sorted by price (cheapest first)
    """
    destination = destination.upper()
    
    if destination not in DESTINATION_SEASONS:
        return []
    
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    cheap_months = []
    
    for i in range(months_ahead):
        month = (current_month + i - 1) % 12 + 1
        year = current_year + (current_month + i - 1) // 12
        
        season = get_season_info(destination, month)
        if season and season.price_level == "cheap":
            month_name = datetime(year, month, 1).strftime("%B %Y")
            cheap_months.append((month, month_name, season.recommendation))
    
    return cheap_months


def format_season_recommendation(destination: str, destination_city: str = None) -> str:
    """
    Format season-based recommendation for display
    
    Args:
        destination: Airport code
        destination_city: City name for display
        
    Returns:
        Formatted recommendation string
    """
    destination = destination.upper()
    city_name = destination_city or destination
    
    # Get current season
    current_season = get_season_info(destination)
    
    # Get cheapest months in next 6 months
    cheap_months = get_cheapest_months(destination, months_ahead=6)
    
    if not current_season and not cheap_months:
        return ""
    
    formatted = f"\n💡 **Tips Waktu Terbaik ke {city_name}:**\n"
    
    if current_season:
        formatted += f"\n📅 **Bulan Ini ({datetime.now().strftime('%B')})**:\n"
        formatted += f"  • Season: {current_season.season_name}\n"
        formatted += f"  • Harga: {current_season.price_level.upper()}\n"
        formatted += f"  • Info: {current_season.description}\n"
        formatted += f"  • Tip: {current_season.recommendation}\n"
    
    if cheap_months:
        formatted += f"\n💰 **Bulan Termurah (6 Bulan Kedepan)**:\n"
        for month_num, month_name, reason in cheap_months[:3]:  # Show top 3
            formatted += f"  • **{month_name}**: {reason}\n"
    
    return formatted


def should_recommend_different_dates(destination: str) -> Tuple[bool, str]:
    """
    Check if current month is expensive and recommend better dates
    
    Args:
        destination: Airport code
        
    Returns:
        (should_recommend, recommendation_message) tuple
    """
    current_season = get_season_info(destination)
    
    if not current_season:
        return False, ""
    
    if current_season.price_level == "expensive":
        cheap_months = get_cheapest_months(destination, months_ahead=4)
        
        if cheap_months:
            month_num, month_name, reason = cheap_months[0]
            message = (
                f"⚠️ **Heads up!** Bulan ini adalah **{current_season.season_name}** "
                f"(harga {current_season.price_level}). "
                f"Kalau fleksibel, coba cari di **{month_name}** - {reason}"
            )
            return True, message
    
    return False, ""


def get_all_seasons(destination: str) -> List[SeasonInfo]:
    """
    Get all seasons for a destination
    
    Args:
        destination: Airport code
        
    Returns:
        List of SeasonInfo objects for this destination
    """
    destination = destination.upper()
    return DESTINATION_SEASONS.get(destination, [])


def format_season_selection(destination: str, destination_city: str = None) -> str:
    """
    Format season selection menu for user
    
    Args:
        destination: Airport code
        destination_city: City name for display
        
    Returns:
        Formatted season selection menu
    """
    seasons = get_all_seasons(destination)
    
    if not seasons:
        # No season data - fallback to simple date range
        return ""
    
    city_name = destination_city or destination
    
    menu = f"\n🌍 **Pilih Season untuk ke {city_name}:**\n\n"
    
    for i, season in enumerate(seasons, 1):
        # Price indicator
        if season.price_level == "cheap":
            price_emoji = "💰💰💰"
            price_text = "HEMAT"
        elif season.price_level == "moderate":
            price_emoji = "💰💰"
            price_text = "WAJAR"
        else:  # expensive
            price_emoji = "💰"
            price_text = "MAHAL"
        
        # Format month range
        start_month = datetime(2025, season.month_range[0], 1).strftime("%b")
        end_month = datetime(2025, season.month_range[1], 1).strftime("%b")
        month_range = f"{start_month}-{end_month}" if start_month != end_month else start_month
        
        menu += f"{i}️⃣ **{season.season_name}** ({month_range}) {price_emoji}\n"
        menu += f"   • Harga: {price_text}\n"
        menu += f"   • {season.description}\n"
        menu += f"   • Tip: {season.recommendation}\n\n"
    
    menu += "Pilih nomor season yang kamu mau! 😊"
    
    return menu


def get_season_date_range(destination: str, season_index: int) -> Optional[Tuple[str, str]]:
    """
    Get date range for a specific season
    
    Args:
        destination: Airport code
        season_index: Season index (0-based)
        
    Returns:
        (start_date, end_date) tuple in YYYY-MM-DD format, or None if invalid
    """
    seasons = get_all_seasons(destination)
    
    if not seasons or season_index < 0 or season_index >= len(seasons):
        return None
    
    season = seasons[season_index]
    current_year = datetime.now().year
    current_month = datetime.now().month
    
    start_month, end_month = season.month_range
    
    # Determine year (handle year wrap-around)
    start_year = current_year
    end_year = current_year
    
    # If season months are in the past, use next year
    if end_month < current_month:
        start_year += 1
        end_year += 1
    elif start_month < current_month <= end_month:
        # Season is ongoing
        pass
    
    # Create date range
    start_date = datetime(start_year, start_month, 1).strftime("%Y-%m-%d")
    
    # End date is last day of end month
    if end_month == 12:
        end_date = datetime(end_year, 12, 31).strftime("%Y-%m-%d")
    else:
        # Last day of month
        import calendar
        last_day = calendar.monthrange(end_year, end_month)[1]
        end_date = datetime(end_year, end_month, last_day).strftime("%Y-%m-%d")
    
    return start_date, end_date

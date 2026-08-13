"""
Intelligent date generation system based on keywords and context

This module provides:
- Keyword-to-date mapping for travel planning
- Seasonal date recommendations for destinations
- Price optimization based on travel keywords
- Flexible date generation for different travel scenarios
"""

import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

try:
    from src.destination_lookup import DestinationDatabase
except ImportError:
    from destination_lookup import DestinationDatabase

class KeywordType(Enum):
    """Types of keywords for date generation"""
    PRICE = "price"  # murah, hemat, budget, promo, diskon
    SEASON = "season"  # sakura, winter, summer, autumn, spring
    EVENT = "event"  # festival, konser, expo, olimpiade
    DURATION = "duration"  # sehari, weekend, seminggu, sebulan
    FLEXIBLE = "flexible"  # bebas, fleksibel, kapan saja, kapanpun

@dataclass
class DateSuggestion:
    """Complete date suggestion with reasoning"""
    departure_date: str
    return_date: Optional[str]
    duration_days: int
    reason: str
    price_category: str  # budget, moderate, premium
    confidence: float  # 0.0 to 1.0
    alternative_dates: List[str]

class KeywordDateMapper:
    """Maps keywords to optimal travel dates"""

    # Price-based keywords with date preferences
    PRICE_KEYWORDS = {
        "murah": {
            "months_ahead": [2, 3, 4, 5, 6],  # 2-6 months ahead for better prices
            "preferred_days": ["Tuesday", "Wednesday", "Thursday"],
            "avoid_months": [6, 7, 12],  # Peak season in Indonesia
            "reason": "Harga terbaik biasanya 2-6 bulan sebelum keberangkatan"
        },
        "hemat": {
            "months_ahead": [2, 3, 4],
            "preferred_days": ["Tuesday", "Wednesday"],
            "avoid_months": [6, 7, 12, 1],
            "reason": "Perjalanan hemat dengan booking jauh hari"
        },
        "budget": {
            "months_ahead": [3, 4, 5, 6],
            "preferred_days": ["Tuesday", "Wednesday"],
            "avoid_months": [6, 7, 12],
            "reason": "Budget-friendly dengan tanggal pilihan"
        },
        "promo": {
            "months_ahead": [1, 2, 3],  # Promo biasanya dekat dengan keberangkatan
            "preferred_days": ["Monday", "Tuesday"],
            "avoid_months": [],
            "reason": "Mencari periode promo terdekat"
        },
        "diskon": {
            "months_ahead": [1, 2, 3, 4],
            "preferred_days": ["Tuesday", "Wednesday"],
            "avoid_months": [],
            "reason": "Periode diskon biasanya low season"
        }
    }

    # Seasonal keywords with specific months
    SEASONAL_KEYWORDS = {
        # Japanese seasons
        "sakura": {
            "months": [3, 4],  # March-April for cherry blossoms
            "regions": ["Asia", "Japan"],
            "reason": "Musim sakura di Jepang (Maret-April)"
        },
        "momiji": {
            "months": [10, 11],  # October-November for autumn leaves
            "regions": ["Asia", "Japan"],
            "reason": "Musim momiji/autumn leaves di Jepang (Oktober-November)"
        },

        # General seasons
        "winter": {
            "months": [12, 1, 2],
            "regions": ["all"],
            "reason": "Musim dingin"
        },
        "summer": {
            "months": [6, 7, 8],
            "regions": ["all"],
            "reason": "Musim panas"
        },
        "spring": {
            "months": [3, 4, 5],
            "regions": ["all"],
            "reason": "Musim semi"
        },
        "autumn": {
            "months": [9, 10, 11],
            "regions": ["all"],
            "reason": "Musim gugur"
        },

        # Indonesian seasons
        "hujan": {
            "months": [10, 11, 12, 1, 2, 3],
            "regions": ["Asia", "Indonesia"],
            "avoid": True,
            "reason": "Musim hujan Indonesia (hindari untuk liburan)"
        },
        "kemarau": {
            "months": [4, 5, 6, 7, 8, 9],
            "regions": ["Asia", "Indonesia"],
            "reason": "Musim kemarau Indonesia - terbaik untuk liburan"
        }
    }

    # Event-based keywords
    EVENT_KEYWORDS = {
        "festival": {
            "research_needed": True,
            "suggestion": "Cari festival lokal di destinasi tujuan"
        },
        "konser": {
            "research_needed": True,
            "suggestion": "Cek jadwal konser di destinasi"
        },
        "tahun baru": {
            "months": [12, 1],
            "specific_dates": ["December 28-31", "January 1-3"],
            "reason": "Periode tahun baru"
        },
        "natal": {
            "months": [12],
            "specific_dates": ["December 20-28"],
            "reason": "Periode Natal"
        }
    }

    # Duration keywords
    DURATION_KEYWORDS = {
        "sehari": {"days": 1, "suggestion": "Day trip"},
        "harian": {"days": 1, "suggestion": "Day trip"},
        "weekend": {"days": 3, "suggestion": "Weekend trip"},
        "3 hari": {"days": 3, "suggestion": "Short trip"},
        "seminggu": {"days": 7, "suggestion": "Weekly vacation"},
        "7 hari": {"days": 7, "suggestion": "Weekly vacation"},
        "10 hari": {"days": 10, "suggestion": "Medium trip"},
        "sebulan": {"days": 30, "suggestion": "Long vacation"},
        "bulan": {"days": 30, "suggestion": "Long vacation"}
    }

    # Flexible keywords
    FLEXIBLE_KEYWORDS = [
        "bebas", "fleksibel", "kapan saja", "kapanpun",
        "tidak ada preferensi", "terserah", "mau kapan saja"
    ]

class IntelligentDateGenerator:
    """Main class for intelligent date generation"""

    def __init__(self):
        self.mapper = KeywordDateMapper()
        self.destination_db = DestinationDatabase()

    def generate_dates_from_keywords(
        self,
        text: str,
        destination: Optional[str] = None,
        origin: Optional[str] = None
    ) -> List[DateSuggestion]:
        """
        Generate intelligent date suggestions based on keywords in text

        Args:
            text: User input text containing keywords
            destination: Destination name/country
            origin: Origin location

        Returns:
            List of date suggestions with reasoning
        """
        text_lower = text.lower()

        # Detect destination information
        dest_info = None
        if destination:
            dest_info = self.destination_db.detect_destination(destination)

        # Extract keywords
        price_keywords = self._extract_price_keywords(text_lower)
        seasonal_keywords = self._extract_seasonal_keywords(text_lower, dest_info)
        event_keywords = self._extract_event_keywords(text_lower)
        duration_keyword = self._extract_duration_keywords(text_lower)
        is_flexible = self._is_flexible(text_lower)

        suggestions = []

        # Generate suggestions based on keyword combinations
        if price_keywords:
            suggestions.extend(self._generate_price_based_suggestions(
                price_keywords, dest_info, duration_keyword
            ))

        if seasonal_keywords:
            suggestions.extend(self._generate_seasonal_suggestions(
                seasonal_keywords, dest_info, duration_keyword
            ))

        if event_keywords:
            suggestions.extend(self._generate_event_suggestions(
                event_keywords, dest_info, duration_keyword
            ))

        # If no specific keywords but flexible, generate general suggestions
        if not suggestions and (is_flexible or not text_lower.strip()):
            suggestions.extend(self._generate_general_suggestions(
                dest_info, duration_keyword
            ))

        # If still no suggestions, provide default
        if not suggestions:
            suggestions.extend(self._generate_default_suggestions(
                dest_info, duration_keyword
            ))

        # Sort by confidence and return top suggestions
        suggestions.sort(key=lambda x: x.confidence, reverse=True)
        return suggestions[:5]  # Return top 5 suggestions

    def _extract_price_keywords(self, text: str) -> List[str]:
        """Extract price-related keywords from text"""
        found = []
        for keyword in self.mapper.PRICE_KEYWORDS.keys():
            if keyword in text:
                found.append(keyword)
        return found

    def _extract_seasonal_keywords(self, text: str, dest_info) -> List[str]:
        """Extract seasonal keywords relevant to destination"""
        found = []
        for keyword, info in self.mapper.SEASONAL_KEYWORDS.items():
            if keyword in text:
                # Check if this seasonal keyword is relevant for destination
                if info["regions"] == ["all"] or dest_info:
                    if dest_info and dest_info.region in info["regions"]:
                        found.append(keyword)
                    elif info["regions"] == ["all"]:
                        found.append(keyword)
        return found

    def _extract_event_keywords(self, text: str) -> List[str]:
        """Extract event-related keywords from text"""
        found = []
        for keyword in self.mapper.EVENT_KEYWORDS.keys():
            if keyword in text:
                found.append(keyword)
        return found

    def _extract_duration_keywords(self, text: str) -> Optional[Dict]:
        """Extract duration preference from text"""
        for keyword, info in self.mapper.DURATION_KEYWORDS.items():
            if keyword in text:
                return info
        return None

    def _is_flexible(self, text: str) -> bool:
        """Check if user is flexible with dates"""
        return any(keyword in text for keyword in self.mapper.FLEXIBLE_KEYWORDS)

    def _generate_price_based_suggestions(
        self,
        keywords: List[str],
        dest_info,
        duration_info
    ) -> List[DateSuggestion]:
        """Generate suggestions based on price keywords"""
        suggestions = []
        current_date = datetime.now()

        for keyword in keywords:
            config = self.mapper.PRICE_KEYWORDS[keyword]

            for months_ahead in config["months_ahead"][:3]:  # Top 3 months
                target_date = current_date + timedelta(days=30 * months_ahead)

                # Skip if in avoid months
                if target_date.month in config["avoid_months"]:
                    continue

                # Find preferred day in target month
                departure = self._find_preferred_day(
                    target_date.year,
                    target_date.month,
                    config["preferred_days"]
                )

                if departure:
                    duration = duration_info["days"] if duration_info else 7
                    return_date = departure + timedelta(days=duration - 1)

                    suggestion = DateSuggestion(
                        departure_date=departure.strftime("%Y-%m-%d"),
                        return_date=return_date.strftime("%Y-%m-%d"),
                        duration_days=duration,
                        reason=f"{config['reason']} - {months_ahead} bulan ahead",
                        price_category="budget",
                        confidence=0.8 if keyword in ["murah", "hemat"] else 0.6,
                        alternative_dates=self._get_alternative_dates(departure, 2)
                    )
                    suggestions.append(suggestion)

        return suggestions

    def _generate_seasonal_suggestions(
        self,
        keywords: List[str],
        dest_info,
        duration_info
    ) -> List[DateSuggestion]:
        """Generate suggestions based on seasonal keywords"""
        suggestions = []
        current_year = datetime.now().year

        for keyword in keywords:
            config = self.mapper.SEASONAL_KEYWORDS[keyword]

            # Skip if this is an "avoid" keyword
            if config.get("avoid"):
                continue

            for month in config["months"]:
                # Use next year if month has passed
                year = current_year if month >= datetime.now().month else current_year + 1

                # Find optimal dates in the month
                if "specific_dates" in config:
                    for date_range in config["specific_dates"]:
                        departure = self._parse_specific_date(date_range, year)
                        if departure:
                            duration = duration_info["days"] if duration_info else 7
                            return_date = departure + timedelta(days=duration - 1)

                            suggestion = DateSuggestion(
                                departure_date=departure.strftime("%Y-%m-%d"),
                                return_date=return_date.strftime("%Y-%m-%d"),
                                duration_days=duration,
                                reason=config["reason"],
                                price_category="moderate",  # Seasonal travel is usually moderate
                                confidence=0.9,  # High confidence for seasonal
                                alternative_dates=self._get_alternative_dates(departure, 2)
                            )
                            suggestions.append(suggestion)
                else:
                    # Find best dates in the month
                    first_day = datetime(year, month, 1)
                    preferred_days = ["Friday", "Saturday"] if keyword in ["summer", "spring"] else ["Tuesday", "Wednesday"]

                    departure = self._find_preferred_day(year, month, preferred_days)
                    if departure:
                        duration = duration_info["days"] if duration_info else 7
                        return_date = departure + timedelta(days=duration - 1)

                        suggestion = DateSuggestion(
                            departure_date=departure.strftime("%Y-%m-%d"),
                            return_date=return_date.strftime("%Y-%m-%d"),
                            duration_days=duration,
                            reason=config["reason"],
                            price_category="moderate",
                            confidence=0.85,
                            alternative_dates=self._get_alternative_dates(departure, 2)
                        )
                        suggestions.append(suggestion)

        return suggestions

    def _generate_event_suggestions(
        self,
        keywords: List[str],
        dest_info,
        duration_info
    ) -> List[DateSuggestion]:
        """Generate suggestions based on event keywords"""
        suggestions = []
        current_date = datetime.now()

        for keyword in keywords:
            config = self.mapper.EVENT_KEYWORDS[keyword]

            if config.get("research_needed"):
                # For events that need research, suggest general timeframe
                suggestion = DateSuggestion(
                    departure_date=(current_date + timedelta(days=60)).strftime("%Y-%m-%d"),
                    return_date=(current_date + timedelta(days=67)).strftime("%Y-%m-%d"),
                    duration_days=7,
                    reason=f"{config['suggestion']} - {keyword}",
                    price_category="moderate",
                    confidence=0.4,  # Low confidence, needs research
                    alternative_dates=[]
                )
                suggestions.append(suggestion)
            else:
                # For specific events like New Year, Christmas
                for months_ahead in range(1, 7):
                    target_date = current_date + timedelta(days=30 * months_ahead)
                    if target_date.month in config["months"]:
                        departure = self._parse_specific_date(
                            config["specific_dates"][0],
                            target_date.year
                        )
                        if departure:
                            duration = duration_info["days"] if duration_info else 5
                            return_date = departure + timedelta(days=duration - 1)

                            suggestion = DateSuggestion(
                                departure_date=departure.strftime("%Y-%m-%d"),
                                return_date=return_date.strftime("%Y-%m-%d"),
                                duration_days=duration,
                                reason=config["reason"],
                                price_category="premium",  # Event periods are expensive
                                confidence=0.95,
                                alternative_dates=self._get_alternative_dates(departure, 1)
                            )
                            suggestions.append(suggestion)
                            break

        return suggestions

    def _generate_general_suggestions(self, dest_info, duration_info) -> List[DateSuggestion]:
        """Generate general good suggestions"""
        suggestions = []
        current_date = datetime.now()

        # Suggest optimal dates 2-4 months ahead
        for months_ahead in [2, 3, 4]:
            target_date = current_date + timedelta(days=30 * months_ahead)

            # Find Tuesday (best price day)
            departure = self._find_preferred_day(target_date.year, target_date.month, ["Tuesday"])
            if departure:
                duration = duration_info["days"] if duration_info else 7
                return_date = departure + timedelta(days=duration - 1)

                suggestion = DateSuggestion(
                    departure_date=departure.strftime("%Y-%m-%d"),
                    return_date=return_date.strftime("%Y-%m-%d"),
                    duration_days=duration,
                    reason="Tanggal optimal dengan harga terbaik (Tuesday departure)",
                    price_category="budget",
                    confidence=0.7,
                    alternative_dates=self._get_alternative_dates(departure, 2)
                )
                suggestions.append(suggestion)

        return suggestions

    def _generate_default_suggestions(self, dest_info, duration_info) -> List[DateSuggestion]:
        """Generate default suggestions when no keywords found"""
        suggestions = []
        current_date = datetime.now()

        # Default: suggest 1 month ahead
        target_date = current_date + timedelta(days=30)
        departure = self._find_preferred_day(target_date.year, target_date.month, ["Saturday"])

        if departure:
            duration = duration_info["days"] if duration_info else 5
            return_date = departure + timedelta(days=duration - 1)

            suggestion = DateSuggestion(
                departure_date=departure.strftime("%Y-%m-%d"),
                return_date=return_date.strftime("%Y-%m-%d"),
                duration_days=duration,
                reason="Saran default: weekend bulan depan",
                price_category="moderate",
                confidence=0.5,
                alternative_dates=self._get_alternative_dates(departure, 2)
            )
            suggestions.append(suggestion)

        return suggestions

    def _find_preferred_day(self, year: int, month: int, preferred_days: List[str]) -> Optional[datetime]:
        """Find the first preferred day in a month"""
        day_to_int = {
            "Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
            "Friday": 4, "Saturday": 5, "Sunday": 6
        }

        first_day = datetime(year, month, 1)
        days_in_month = (datetime(year, month + 1, 1) - first_day).days if month < 12 else 31

        for day_offset in range(days_in_month):
            current_day = first_day + timedelta(days=day_offset)
            if current_day.strftime("%A") in preferred_days:
                # Skip if too soon (less than 2 weeks)
                if current_day > (datetime.now() + timedelta(weeks=2)):
                    return current_day

        return None

    def _parse_specific_date(self, date_str: str, year: int) -> Optional[datetime]:
        """Parse specific date strings like 'December 28-31'"""
        try:
            # Extract start date
            if "-" in date_str:
                start_part = date_str.split("-")[0].strip()
            else:
                start_part = date_str.strip()

            # Parse month and day
            parts = start_part.split()
            if len(parts) == 2:
                month_name = parts[0]
                day = int(parts[1])

                months = {
                    "January": 1, "February": 2, "March": 3, "April": 4,
                    "May": 5, "June": 6, "July": 7, "August": 8,
                    "September": 9, "October": 10, "November": 11, "December": 12
                }

                if month_name in months:
                    return datetime(year, months[month_name], day)
        except:
            pass

        return None

    def _get_alternative_dates(self, departure: datetime, count: int) -> List[str]:
        """Get alternative dates around the preferred departure"""
        alternatives = []

        # Add dates before and after
        for offset in range(-count, count + 1):
            if offset == 0:  # Skip the main date
                continue
            alt_date = departure + timedelta(days=offset * 7)  # Week intervals
            if alt_date > (datetime.now() + timedelta(weeks=2)):
                alternatives.append(alt_date.strftime("%Y-%m-%d"))

        return alternatives[:count]

    def format_suggestions(self, suggestions: List[DateSuggestion]) -> str:
        """Format date suggestions into user-friendly message"""
        if not suggestions:
            return "Belum bisa generate tanggal yang sesuai"

        formatted = "\n\n**REKOMENDASI TANGGAL CERDAS**\n"
        formatted += "=" * 50 + "\n\n"

        for i, suggestion in enumerate(suggestions[:3], 1):  # Show top 3
            formatted += f"{i}. **{suggestion.departure_date}**"
            if suggestion.return_date:
                formatted += f" - {suggestion.return_date}"
            formatted += f" ({suggestion.duration_days} hari)\n"
            formatted += f"   Alasan: {suggestion.reason}\n"
            formatted += f"   Kategori: {suggestion.price_category.title()}\n"

            if suggestion.alternative_dates:
                formatted += f"   Alternatif: {', '.join(suggestion.alternative_dates[:3])}\n"

            formatted += "\n"

        formatted += "**Tips Tambahan:**\n"
        formatted += "- Selasa-Rabu biasanya harga paling murah\n"
        formatted += "- Booking 2-6 bulan lebih awal dapat harga terbaik\n"
        formatted += "- Hindari peak season (Juni-Juli, Desember) untuk budget lebih hemat\n"

        return formatted
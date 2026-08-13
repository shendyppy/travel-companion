"""
Suggestion Engine - Context-aware chat suggestions for Travel Buddy

Generates relevant follow-up prompts based on:
- Conversation state (new/ongoing)
- Last topic discussed
- Detected preferences
- Time of day
- Season/holiday context

Usage:
    from suggestion_engine import SuggestionEngine
    
    engine = SuggestionEngine()
    suggestions = engine.generate_suggestions(
        session_state="new",
        last_response="",
        detected_destination=None
    )
"""

import random
from datetime import datetime
from enum import Enum
from typing import Optional
from dataclasses import dataclass


class ConversationState(str, Enum):
    """Conversation state enum"""
    NEW = "new"                          # Fresh conversation, no messages yet
    GREETING = "greeting"                # User said hi/hello
    DESTINATION_DISCUSSED = "destination"  # Destination mentioned
    FLIGHT_SEARCHED = "flight"           # Flight search was performed
    HOTEL_DISCUSSED = "hotel"            # Hotel discussed
    PLANNING = "planning"                # General travel planning
    BUDGET_DISCUSSED = "budget"          # Budget mentioned


@dataclass
class SuggestionContext:
    """Context for generating suggestions"""
    state: ConversationState = ConversationState.NEW
    destination: Optional[str] = None
    origin: Optional[str] = None
    has_flights: bool = False
    budget: Optional[str] = None
    current_time: datetime = None
    
    def __post_init__(self):
        if self.current_time is None:
            self.current_time = datetime.now()


class SuggestionEngine:
    """
    Context-aware suggestion generator for Travel Buddy chatbot.
    
    Generates 3-4 relevant suggestions based on conversation context.
    """
    
    # =========================================================================
    # SUGGESTION TEMPLATES
    # =========================================================================
    
    # Initial suggestions for new conversations
    INITIAL_SUGGESTIONS = [
        "Mau liburan ke mana nih? 🏖️",
        "Cariin tiket murah ke Bali",
        "Rekomendasi destinasi budget-friendly",
        "Weekend getaway dari Jakarta",
        "Liburan keluarga bulan depan",
        "Solo traveling ke luar negeri",
    ]
    
    # Time-based greetings
    MORNING_SUGGESTIONS = [
        "Mau cari tiket untuk weekend ini?",
        "Spontan trip hari ini?",
        "Liburan pagi yang segar ke mana?",
    ]
    
    AFTERNOON_SUGGESTIONS = [
        "Mau planning liburan seru?",
        "Cari tiket murah untuk libur panjang?",
        "Staycation dekat untuk weekend?",
    ]
    
    EVENING_SUGGESTIONS = [
        "Planning liburan untuk minggu depan?",
        "Cari tiket untuk long weekend?",
        "Mau explore destinasi baru?",
    ]
    
    # After greeting
    POST_GREETING_SUGGESTIONS = [
        "Mau ke mana nih?",
        "Ada rencana liburan?",
        "Butuh rekomendasi destinasi?",
        "Mau cari tiket murah?",
    ]
    
    # After destination mentioned
    DESTINATION_SUGGESTIONS_TEMPLATE = [
        "Cari tiket ke {destination}",
        "Rekomendasi hotel di {destination}",
        "Itinerary {destination} 3 hari",
        "Budget liburan ke {destination}",
        "Tips traveling ke {destination}",
        "Tempat wisata di {destination}",
        "Kuliner khas {destination}",
    ]
    
    # After flight search
    POST_FLIGHT_SUGGESTIONS_TEMPLATE = [
        "Cari hotel di {destination}",
        "Atraksi wisata populer",
        "Transportasi dari bandara",
        "Itinerary {destination}",
        "Tips hemat di {destination}",
    ]
    
    # General travel planning
    PLANNING_SUGGESTIONS = [
        "Mau ke destinasi mana?",
        "Budget berapa untuk liburan ini?",
        "Kapan rencana berangkat?",
        "Liburan berapa hari?",
        "Traveling sendiri atau bareng?",
    ]
    
    # Budget related
    BUDGET_SUGGESTIONS_TEMPLATE = [
        "Cari tiket termurah",
        "Hotel budget-friendly",
        "Tips hemat traveling",
        "Promo tiket terbaru",
    ]
    
    # Holiday season suggestions (Indonesian holidays)
    HOLIDAY_SUGGESTIONS = [
        "Tiket libur Lebaran",
        "Tiket liburan Natal & Tahun Baru",
        "Long weekend ke Bali",
        "Liburan sekolah ke mana?",
    ]
    
    # =========================================================================
    # MAIN GENERATION LOGIC
    # =========================================================================
    
    def generate_suggestions(
        self,
        state: ConversationState = ConversationState.NEW,
        destination: Optional[str] = None,
        origin: Optional[str] = None,
        has_flights: bool = False,
        budget: Optional[str] = None,
        response_text: Optional[str] = None,
        current_time: Optional[datetime] = None,
        count: int = 4
    ) -> list[str]:
        """
        Generate context-aware suggestions.
        
        Args:
            state: Current conversation state
            destination: Detected destination (if any)
            origin: User's origin city (if known)
            has_flights: Whether flight results were just shown
            budget: Detected budget preference
            response_text: Last AI response (for additional context)
            current_time: Current time (for time-based suggestions)
            count: Number of suggestions to return (default 4)
            
        Returns:
            List of suggestion strings
        """
        current_time = current_time or datetime.now()
        suggestions = []
        
        # Handle each state
        if state == ConversationState.NEW:
            suggestions = self._get_initial_suggestions(current_time)
            
        elif state == ConversationState.GREETING:
            suggestions = self._get_post_greeting_suggestions(current_time)
            
        elif state == ConversationState.DESTINATION_DISCUSSED and destination:
            suggestions = self._get_destination_suggestions(destination, has_flights)
            
        elif state == ConversationState.FLIGHT_SEARCHED and destination:
            suggestions = self._get_post_flight_suggestions(destination)
            
        elif state == ConversationState.BUDGET_DISCUSSED:
            suggestions = self._get_budget_suggestions(destination)
            
        elif state == ConversationState.PLANNING:
            suggestions = self._get_planning_suggestions(destination)
            
        else:
            suggestions = self._get_initial_suggestions(current_time)
        
        # Ensure we have enough suggestions
        while len(suggestions) < count:
            suggestions.extend(self._get_fallback_suggestions())
        
        # Randomize and limit
        random.shuffle(suggestions)
        return suggestions[:count]
    
    def get_initial_suggestions(self, current_time: Optional[datetime] = None) -> list[str]:
        """
        Get initial suggestions for app launch.
        
        This is the endpoint for fetching suggestions at app startup,
        before any conversation has started.
        """
        return self.generate_suggestions(
            state=ConversationState.NEW,
            current_time=current_time or datetime.now(),
            count=4
        )
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def _get_initial_suggestions(self, current_time: datetime) -> list[str]:
        """Get suggestions for new conversation"""
        suggestions = []
        
        # Add time-based suggestion
        hour = current_time.hour
        if 5 <= hour < 12:
            suggestions.extend(random.sample(self.MORNING_SUGGESTIONS, min(1, len(self.MORNING_SUGGESTIONS))))
        elif 12 <= hour < 17:
            suggestions.extend(random.sample(self.AFTERNOON_SUGGESTIONS, min(1, len(self.AFTERNOON_SUGGESTIONS))))
        else:
            suggestions.extend(random.sample(self.EVENING_SUGGESTIONS, min(1, len(self.EVENING_SUGGESTIONS))))
        
        # Add holiday suggestions if applicable
        if self._is_holiday_season(current_time):
            suggestions.extend(random.sample(self.HOLIDAY_SUGGESTIONS, min(1, len(self.HOLIDAY_SUGGESTIONS))))
        
        # Fill with general initial suggestions
        remaining = 4 - len(suggestions)
        suggestions.extend(random.sample(self.INITIAL_SUGGESTIONS, min(remaining, len(self.INITIAL_SUGGESTIONS))))
        
        return suggestions
    
    def _get_post_greeting_suggestions(self, current_time: datetime) -> list[str]:
        """Get suggestions after user greeting"""
        suggestions = list(self.POST_GREETING_SUGGESTIONS)
        
        # Add time-based twist
        hour = current_time.hour
        if hour >= 20 or hour < 5:
            suggestions.append("Planning liburan untuk besok?")
        
        return suggestions
    
    def _get_destination_suggestions(self, destination: str, has_flights: bool) -> list[str]:
        """Get suggestions after destination is mentioned"""
        suggestions = []
        
        for template in self.DESTINATION_SUGGESTIONS_TEMPLATE:
            suggestions.append(template.format(destination=destination))
        
        # If flights already shown, prioritize non-flight suggestions
        if has_flights:
            suggestions = [s for s in suggestions if "tiket" not in s.lower()]
        
        return suggestions
    
    def _get_post_flight_suggestions(self, destination: str) -> list[str]:
        """Get suggestions after flight search"""
        suggestions = []
        
        for template in self.POST_FLIGHT_SUGGESTIONS_TEMPLATE:
            suggestions.append(template.format(destination=destination))
        
        return suggestions
    
    def _get_budget_suggestions(self, destination: Optional[str]) -> list[str]:
        """Get budget-related suggestions"""
        suggestions = list(self.BUDGET_SUGGESTIONS_TEMPLATE)
        
        if destination:
            suggestions.append(f"Estimasi biaya ke {destination}")
            suggestions.append(f"Hostel murah di {destination}")
        
        return suggestions
    
    def _get_planning_suggestions(self, destination: Optional[str]) -> list[str]:
        """Get general planning suggestions"""
        suggestions = list(self.PLANNING_SUGGESTIONS)
        
        if destination:
            suggestions.append(f"Detail tentang {destination}")
        
        return suggestions
    
    def _get_fallback_suggestions(self) -> list[str]:
        """Get fallback suggestions"""
        return random.sample(self.INITIAL_SUGGESTIONS, 2)
    
    def _is_holiday_season(self, current_time: datetime) -> bool:
        """Check if current time is during Indonesian holiday season"""
        month = current_time.month
        day = current_time.day
        
        # Major Indonesian holidays/seasons
        # - Ramadan/Lebaran (varies, approx March-May)
        # - School holidays (June-July, December)
        # - Christmas/New Year (December)
        # - Long weekends
        
        if month == 12:  # Christmas/New Year
            return True
        if month in [6, 7]:  # School holidays
            return True
        if month in [3, 4, 5]:  # Ramadan season (approximate)
            return True
        
        return False
    
    def detect_state_from_response(
        self,
        user_message: str,
        ai_response: str,
        has_flights: bool = False,
        current_destination: Optional[str] = None
    ) -> tuple[ConversationState, Optional[str]]:
        """
        Detect conversation state from messages.
        
        This helps automatically determine what suggestions to show
        based on the conversation content.
        
        Returns:
            Tuple of (state, detected_destination)
        """
        user_lower = user_message.lower()
        response_lower = ai_response.lower()
        
        # Detect greeting
        greeting_words = ["halo", "hai", "hi", "hello", "hey", "pagi", "siang", "sore", "malam"]
        if any(word in user_lower for word in greeting_words) and len(user_message) < 20:
            return ConversationState.GREETING, current_destination
        
        # Detect flight search result
        if has_flights:
            return ConversationState.FLIGHT_SEARCHED, current_destination
        
        # Detect destination mentions
        destinations = self._extract_destinations(user_message + " " + ai_response)
        if destinations:
            return ConversationState.DESTINATION_DISCUSSED, destinations[0]
        
        # Detect budget discussion
        budget_words = ["budget", "murah", "hemat", "cheap", "affordable", "harga"]
        if any(word in user_lower for word in budget_words):
            return ConversationState.BUDGET_DISCUSSED, current_destination
        
        # Default to planning
        return ConversationState.PLANNING, current_destination
    
    def _extract_destinations(self, text: str) -> list[str]:
        """Extract destination names from text"""
        # Common Indonesian destinations
        destinations = [
            "bali", "lombok", "yogyakarta", "jogja", "bandung", "malang",
            "surabaya", "semarang", "solo", "medan", "makassar", "manado",
            "raja ampat", "labuan bajo", "komodo", "flores", "nusa penida",
            "gili", "singapore", "singapura", "malaysia", "kuala lumpur",
            "bangkok", "thailand", "vietnam", "japan", "jepang", "korea",
            "tokyo", "osaka", "seoul", "banyuwangi", "bromo", "dieng",
        ]
        
        text_lower = text.lower()
        found = []
        
        for dest in destinations:
            if dest in text_lower:
                # Capitalize properly
                found.append(dest.title())
        
        return found


# ==============================================================================
# SINGLETON INSTANCE
# ==============================================================================

_suggestion_engine: Optional[SuggestionEngine] = None


def get_suggestion_engine() -> SuggestionEngine:
    """Get singleton suggestion engine instance"""
    global _suggestion_engine
    
    if _suggestion_engine is None:
        _suggestion_engine = SuggestionEngine()
    
    return _suggestion_engine

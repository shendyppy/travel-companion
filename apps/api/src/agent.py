"""
Agent module - Handles Travel Buddy agent initialization and chat logic

This module contains the TravelAgent class which manages interactions with the Gemini API
and maintains the conversation state with users.
"""

import logging
import re
from datetime import datetime
from typing import Optional, Dict, List, Any

# Import internal modules - try relative first, then absolute
try:
    from src.config import (
        TRAVEL_PERSONA,
        EXIT_COMMANDS,
        MAX_INPUT_LENGTH,
        ERROR_EMPTY_INPUT,
        ERROR_INPUT_TOO_LONG,
        AMADEUS_CONFIGURED,
    )
    from src.llm import UniversalLLM, create_llm
    from src.flight_api import (
        search_flights,
        format_flight_results,
        format_flight_error,
        detect_flight_request,
        extract_flight_details_from_response,
        search_cheapest_flight_next_week,
        search_flights_in_date_range,
        format_date_range_results,
    )
    from src.booking_links import format_booking_links, get_booking_links_dict
    from src.trip_context import TripContext, TripContextManager
    from src.season_intelligence import (
        format_season_recommendation,
        should_recommend_different_dates,
        get_season_info,
        get_all_seasons,
        format_season_selection,
        get_season_date_range,
    )
    from src.destination_data import (
        recommend_destinations,
        format_destination_recommendation,
        detect_travel_preferences,
    )
    from src.smart_detection import (
        LocationDetector,
        DateRangeSuggester,
        PackageGenerator,
        detect_travel_intentions,
    )
    from src.intelligent_date_generator import IntelligentDateGenerator
except ImportError:
    # Fallback for running from within src directory
    from config import (
        TRAVEL_PERSONA,
        EXIT_COMMANDS,
        MAX_INPUT_LENGTH,
        ERROR_EMPTY_INPUT,
        ERROR_INPUT_TOO_LONG,
        AMADEUS_CONFIGURED,
    )
    from llm import UniversalLLM, create_llm
    from flight_api import (
        search_flights,
        format_flight_results,
        format_flight_error,
        detect_flight_request,
        extract_flight_details_from_response,
        search_cheapest_flight_next_week,
        search_flights_in_date_range,
        format_date_range_results,
    )
    from booking_links import format_booking_links, get_booking_links_dict
    from trip_context import TripContext, TripContextManager
    from season_intelligence import (
        format_season_recommendation,
        should_recommend_different_dates,
        get_season_info,
        get_all_seasons,
        format_season_selection,
        get_season_date_range,
    )
    from destination_data import (
        recommend_destinations,
        format_destination_recommendation,
        detect_travel_preferences,
    )
    from smart_detection import (
        LocationDetector,
        DateRangeSuggester,
        PackageGenerator,
        detect_travel_intentions,
    )
    from intelligent_date_generator import IntelligentDateGenerator

# Get logger for this module
logger = logging.getLogger(__name__)


class ConversationMessage:
    """
    Represents a single message in the conversation history.

    This helps track the flow of the conversation and could be useful for:
    - Debugging user interactions
    - Analyzing conversation patterns
    - Providing context to the LLM in future iterations
    """

    def __init__(self, role: str, content: str, timestamp: Optional[datetime] = None):
        """
        Initialize a conversation message.

        Args:
            role: Either 'user' or 'assistant'
            content: The actual message text
            timestamp: When the message was sent (defaults to now)
        """
        self.role = role
        self.content = content
        self.timestamp = timestamp or datetime.now()

    def __repr__(self) -> str:
        """String representation for debugging"""
        return f"[{self.timestamp.strftime('%H:%M:%S')}] {self.role}: {self.content[:50]}..."

    def to_dict(self) -> Dict:
        """Convert to dict for LLM history"""
        return {"role": self.role, "content": self.content}


class TravelAgent:
    """
    Budget Travel Buddy AI Agent - Universal LLM Support

    This class handles:
    - Universal LLM initialization (Gemini, GLM, OpenAI, etc.)
    - Sending messages and receiving responses
    - Input validation
    - Conversation history tracking
    - Error handling with specific exception types
    """

    def __init__(self, provider: str = None, model: str = None) -> None:
        """
        Initialize Travel Agent with universal LLM support.

        Args:
            provider: LLM provider (gemini, glm, openai, custom)
            model: Specific model to use
        """
        # Initialize universal LLM
        self.llm = create_llm(provider=provider, model=model)
        self.conversation_history: List[ConversationMessage] = []
        
        # Conversation state for smart flight search
        self.conversation_state: Dict[str, Any] = {
            "awaiting_date_preference": False,
            "awaiting_season_selection": False,
            "pending_flight_search": None,  # Stores {origin, destination, passengers}
            "last_search_result": None,
            "suggested_packages": None,  # Stores generated packages for selection
        }

        # Log provider info
        provider_info = self.llm.get_provider_info()
        logger.info(f"Initialized TravelAgent with {provider_info['provider']} ({provider_info['model']})")
        logger.info("TravelAgent initialized successfully")

    def _build_history_for_llm(self) -> List[Dict]:
        """Build conversation history for LLM"""
        # Get last 10 messages to avoid token limits
        recent_messages = self.conversation_history[-10:]
        return [msg.to_dict() for msg in recent_messages]

    def send_message(self, user_input: str) -> Optional[str]:
        """
        Kirim pesan ke Travel Buddy dan dapatkan respons.

        This method:
        - Sends the user's message to the configured LLM
        - Detects if it's a flight search request
        - Automatically searches flights if detected
        - Stores both user and assistant messages in history
        - Handles specific exception types appropriately
        - Returns None if any error occurs

        Args:
            user_input: The user's message to the Travel Buddy

        Returns:
            The assistant's response (possibly with flight results), or None if an error occurred
        """
        try:
            logger.debug(f"Sending message: {user_input[:100]}...")

            # Build conversation history
            history = self._build_history_for_llm()

            # Send message to LLM
            response = self.llm.chat(
                message=user_input,
                system_prompt=TRAVEL_PERSONA,
                history=history
            )
            response_text = response

            # Check if user is selecting a package number (1-6)
            package_selection = self._detect_package_selection(user_input)
            if package_selection is not None and self.conversation_state.get("suggested_packages"):
                logger.info(f"User selected package #{package_selection}")
                
                # Get the selected package
                packages = self.conversation_state["suggested_packages"]
                if 0 <= package_selection < len(packages):
                    selected_package = packages[package_selection]
                    
                    # Extract flight details from package
                    origin_code = selected_package.origin_code
                    dest_code = selected_package.destination_code
                    departure_date = selected_package.departure_date
                    
                    logger.info(f"Searching real-time flights: {origin_code} -> {dest_code} on {departure_date}")
                    
                    # Search for real-time flights
                    flight_results = self.search_and_format_flights(
                        origin_code,
                        dest_code,
                        departure_date
                    )
                    
                    # Add context about the selected package
                    response_text += f"\n\n✅ **Oke, aku carikan harga real-time untuk paket #{package_selection + 1}!**\n"
                    response_text += f"📍 Rute: {selected_package.origin} → {selected_package.destination}\n"
                    response_text += f"📅 Tanggal: {selected_package.departure_date}\n\n"
                    response_text += flight_results
                    
                    logger.info("Real-time flight search completed for selected package")
                else:
                    response_text += f"\n\n⚠️ Maaf, paket #{package_selection + 1} tidak ditemukan. Pilih nomor 1-{len(packages)} ya! 😊"
            
            # Check if this is a flight request (PRIORITY: Check this BEFORE complete trip suggestion)
            if detect_flight_request(user_input) or detect_flight_request(response_text):
                logger.info("Flight request detected, attempting to extract flight details...")

                # Try to extract flight parameters from response
                flight_details = extract_flight_details_from_response(response_text)

                if flight_details:
                    # Check if user specified a date range
                    if flight_details.get("date_range"):
                        # Date range search - find cheapest in range
                        start_date, end_date = flight_details["date_range"]
                        adults = flight_details.get("adults", 1)
                        
                        logger.info(
                            f"Extracted flight details with date range: {flight_details['origin']} -> "
                            f"{flight_details['destination']} from {start_date} to {end_date}, {adults} pax"
                        )

                        # Search for cheapest flight in date range
                        try:
                            from src.flight_api import search_flights_in_date_range, format_date_range_results
                        except ImportError:
                            from flight_api import search_flights_in_date_range, format_date_range_results
                        
                        result = search_flights_in_date_range(
                            flight_details["origin"],
                            flight_details["destination"],
                            start_date,
                            end_date,
                            adults=adults,
                            max_searches=7  # Limit API calls
                        )
                        
                        if result["success"]:
                            flight_results = format_date_range_results(
                                result,
                                flight_details["origin"],
                                flight_details["destination"]
                            )
                        else:
                            try:
                                from src.flight_api import format_flight_error
                            except ImportError:
                                from flight_api import format_flight_error
                            flight_results = format_flight_error(result["error"])
                        
                        response_text += "\n\n" + flight_results
                        logger.info("Date range search results appended to response")
                        
                    # Check if user already specified a single date
                    elif flight_details.get("date"):
                        # Traditional search with specific date
                        adults = flight_details.get("adults", 1)
                        
                        logger.info(
                            f"Extracted flight details with date: {flight_details['origin']} -> "
                            f"{flight_details['destination']} on {flight_details['date']}, {adults} pax"
                        )

                        # Search for flights
                        flight_results = self.search_and_format_flights(
                            flight_details["origin"],
                            flight_details["destination"],
                            flight_details["date"],
                            adults=adults
                        )

                        # Append flight results to response
                        response_text += "\n\n" + flight_results
                        logger.info("Flight search results appended to response")
                    else:
                        # No date specified - use smart flight search
                        logger.info(
                            f"Flight request without date: {flight_details['origin']} -> {flight_details['destination']}"
                        )
                        
                        # Store pending search and ask for season selection
                        self.conversation_state["pending_flight_search"] = {
                            "origin": flight_details["origin"],
                            "destination": flight_details["destination"],
                            "origin_city": None,  # Could extract from response if needed
                            "dest_city": None,
                        }
                        self.conversation_state["awaiting_date_preference"] = True
                        
                        # Ask user for season selection
                        smart_search_question = self._handle_smart_flight_search(
                            flight_details["origin"],
                            flight_details["destination"],
                            user_input
                        )
                        response_text += "\n\n" + smart_search_question
                        
                else:
                    # Could not extract origin/destination - try to extract from user input directly
                    logger.info("Trying to extract flight details from user input directly")
                    
                    # Simple extraction: look for city/airport codes
                    import re
                    codes = re.findall(r'\b([A-Z]{3})\b', user_input.upper())
                    
                    # Also check for common city names
                    city_mappings = {
                        "jakarta": "CGK",
                        "jepang": "NRT",
                        "tokyo": "NRT", 
                        "narita": "NRT",
                        "osaka": "KIX",
                        "bali": "DPS",
                        "singapore": "SIN",
                        "bangkok": "BKK",
                        "kuala lumpur": "KUL",
                    }
                    
                    # Also check for dates in user input
                    date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', user_input)
                    detected_date = None
                    if date_match:
                        detected_date = date_match.group(0)
                        logger.info(f"Detected date in user input: {detected_date}")
                    
                    detected_cities = []
                    user_lower = user_input.lower()
                    for city, code in city_mappings.items():
                        if city in user_lower:
                            detected_cities.append(code)
                    
                    # Combine codes from both methods
                    all_codes = codes + detected_cities
                    
                    if len(all_codes) >= 2:
                        # We have origin and destination!
                        origin = all_codes[0]
                        destination = all_codes[1]
                        
                        logger.info(f"Extracted from user input: {origin} -> {destination}")
                        
                        # If we also have a date, search immediately
                        if detected_date:
                            logger.info(f"Complete flight details extracted: {origin} -> {destination} on {detected_date}")
                            
                            flight_results = self.search_and_format_flights(
                                origin,
                                destination,
                                detected_date
                            )
                            
                            response_text += "\n\n" + flight_results
                            logger.info("Flight search results appended to response")
                        else:
                            # No date - store pending search and trigger season selection
                            self.conversation_state["pending_flight_search"] = {
                                "origin": origin,
                                "destination": destination,
                                "origin_city": None,
                                "dest_city": None,
                            }
                            self.conversation_state["awaiting_date_preference"] = True
                            
                            # Ask for season selection
                            smart_search_question = self._handle_smart_flight_search(
                                origin,
                                destination,
                                user_input
                            )
                            response_text += "\n\n" + smart_search_question
                    else:
                        # Still couldn't extract - DON'T show error, let agent respond naturally
                        # The LLM response already handles this conversationally
                        logger.info(
                            "Flight keywords detected but could not extract complete details - letting LLM handle naturally"
                        )
            
            # Check if user is responding to date preference question
            elif self.conversation_state.get("awaiting_date_preference"):
                pending = self.conversation_state.get("pending_flight_search")
                
                if pending:
                    logger.info("Processing date preference response")
                    
                    # Handle the smart flight search
                    smart_search_result = self._handle_smart_flight_search(
                        pending["origin"],
                        pending["destination"],
                        user_input,
                        pending.get("origin_city"),
                        pending.get("dest_city")
                    )
                    
                    response_text += "\n\n" + smart_search_result
                    
                    # Clear state if search was completed
                    if self._detect_date_preference(user_input) == "cheapest":
                        self.conversation_state["awaiting_date_preference"] = False
                        self.conversation_state["pending_flight_search"] = None
                    
                    logger.info("Smart flight search completed")


            # Check if user is asking for destination recommendations
            elif self.detect_destination_request(user_input, response_text):
                logger.info("Destination recommendation request detected")

                # Detect preferences from user input
                preferences = detect_travel_preferences(user_input)

                # If no specific preferences detected, suggest exploring
                if not preferences:
                    response_text += (
                        "\n\n💡 **Tip**: Biar kasih rekomendasi yang pas, sebutin:\n"
                        "- Tipe liburan (pantai, gunung, budaya, kota)\n"
                        "- Budget (hemat, 1jutaan, 2jutaan)\n"
                        "- Preferensi (dalam/luar negeri)\n\n"
                        "Contoh: 'Mau pantai yang budget-friendly'\n"
                        "Aku kasih rekomendasi spesifik deh! 😊"
                    )
                else:
                    # Generate recommendations based on detected preferences
                    destination_recommendations = self.generate_destination_recommendations(preferences)
                    response_text += destination_recommendations
                    logger.info("Destination recommendations appended to response")
            
            # Auto-suggest complete trip if user asks generally (FALLBACK - only if no other detection)
            # IMPORTANT: Don't suggest if user already has a pending flight search or is in the middle of date selection
            elif not package_selection and not self.conversation_state.get("pending_flight_search") and not self.conversation_state.get("awaiting_date_preference"):
                complete_trip_suggestion = self.auto_suggest_complete_trip(user_input)
                if complete_trip_suggestion:
                    response_text += complete_trip_suggestion
                    logger.info("Complete trip suggestions appended to response")

            # Store in conversation history
            self.conversation_history.append(ConversationMessage("user", user_input))
            self.conversation_history.append(
                ConversationMessage("assistant", response_text)
            )

            logger.info(f"Received response ({len(response_text)} chars)")
            return response_text

        except Exception as e:
            # Log with full traceback for debugging
            logger.error(f"Error sending message: {e}", exc_info=True)
            return None

    def should_exit(self, user_input: str) -> bool:
        """
        Cek apakah pengguna ingin keluar.

        Checks if the user input matches any of the exit commands
        defined in config.py

        Args:
            user_input: The user's input string

        Returns:
            True if user wants to exit, False otherwise
        """
        should_exit = user_input.lower() in EXIT_COMMANDS
        if should_exit:
            logger.info(f"Exit command detected: {user_input}")
        return should_exit

    def is_valid_input(self, user_input: str) -> bool:
        """
        Validasi input pengguna dengan multiple checks.

        Validates:
        - Input is not empty or just whitespace
        - Input doesn't exceed maximum length (prevents prompt injection)

        Args:
            user_input: The user's input string

        Returns:
            True if input is valid, False otherwise
        """
        stripped = user_input.strip()

        # Check for empty input
        if not stripped:
            logger.warning("Empty input received")
            print(f"❌ {ERROR_EMPTY_INPUT}")
            return False

        # Check for excessive length (security: prevent prompt injection)
        if len(stripped) > MAX_INPUT_LENGTH:
            logger.warning(
                f"Input too long: {len(stripped)} chars (max: {MAX_INPUT_LENGTH})"
            )
            print(f"❌ {ERROR_INPUT_TOO_LONG}")
            return False

        return True

    def get_conversation_history(self) -> list:
        """
        Dapatkan riwayat percakapan.

        This can be useful for:
        - Debugging conversation flow
        - Analyzing user behavior
        - Implementing features like "show chat history"

        Returns:
            List of ConversationMessage objects in chronological order
        """
        return self.conversation_history.copy()

    def clear_history(self) -> None:
        """
        Bersihkan riwayat percakapan.

        This could be useful if you want to start a new conversation
        without reinitializing the agent.
        """
        self.conversation_history.clear()
        logger.info("Conversation history cleared")

    def detect_destination_request(self, user_input: str, response_text: str) -> bool:
        """
        Detect if user is asking for destination recommendations

        Args:
            user_input: User's message
            response_text: AI's response

        Returns:
            True if destination recommendation is requested
        """
        destination_keywords = [
            'destinasi', 'rekomendasi', 'kemana', 'mana ya', 'liburan',
            'jalan-jalan', 'trip', 'wisata', 'tempat wisata', 'kunjungan',
            'bantuin pilih', 'saranin', 'kasih ide'
        ]

        # Check if any destination keyword appears
        text_to_check = (user_input + " " + response_text).lower()
        return any(keyword in text_to_check for keyword in destination_keywords)

    def generate_destination_recommendations(self, preferences: Dict) -> str:
        """
        Generate destination recommendations based on detected preferences

        Args:
            preferences: Dictionary of detected preferences

        Returns:
            Formatted destination recommendations
        """
        logger.info(f"Generating destination recommendations with preferences: {preferences}")

        # Get recommendations from destination database
        recommended_destinations = recommend_destinations(
            budget=preferences.get('budget'),
            travel_types=preferences.get('travel_types'),
            region=preferences.get('region'),
            max_results=4
        )

        # Format the recommendations
        formatted_recommendations = format_destination_recommendation(recommended_destinations)

        return formatted_recommendations

    def auto_suggest_complete_trip(self, user_input: str) -> Optional[str]:
        """
        Auto-suggest complete travel packages when user asks for general travel

        Args:
            user_input: User's message

        Returns:
            Formatted complete trip suggestions or None if not applicable
        """
        # Check if user wants a complete trip suggestion
        intentions = detect_travel_intentions(user_input)

        if not intentions.get("wants_complete_trip"):
            return None

        logger.info("Auto-suggesting complete travel package")

        # Detect origin from conversation context
        conversation_texts = [msg.content for msg in self.conversation_history[-3:]]
        origin = LocationDetector.detect_origin(user_input, conversation_texts)

        if not origin:
            # Default to Jakarta if no origin detected
            origin = LocationDetector.INDONESIAN_CITIES["jakarta"]

        # Detect travel preferences
        preferences = detect_travel_preferences(user_input)
        travel_type = preferences.get('travel_types', [])[0].value if preferences.get('travel_types') else None
        budget_category = "budget" if preferences.get('budget') else "affordable"

        # NEW: Detect if user mentioned a specific destination
        try:
            from src.destination_lookup import DestinationDatabase
        except ImportError:
            from destination_lookup import DestinationDatabase
        detected_destination = DestinationDatabase.detect_destination(user_input)

        # Suggest destinations (now with destination detection, deduplicate)
        suggested_dests = LocationDetector.suggest_destinations(
            origin['code'],
            travel_type,
            budget_category,
            detected_destination.name if detected_destination else None
        )

        # Deduplicate destinations based on airport code
        seen_codes = set()
        destinations = []
        for dest in suggested_dests:
            if dest.get("code") not in seen_codes:
                destinations.append(dest)
                seen_codes.add(dest.get("code"))

        # Get date ranges for next 6 months (now with price optimization)
        date_ranges = DateRangeSuggester.get_date_ranges(months_ahead=6)

        # Generate complete packages with intelligent date generation
        packages = PackageGenerator.generate_packages(
            origin,
            destinations,
            date_ranges,
            budget_category,
            user_input,
            detected_destination.name if detected_destination else None
        )

        # Generate intelligent date suggestions if user wants flexibility
        intelligent_dates = ""
        if any(keyword in user_input.lower() for keyword in ["bebas", "murah", "fleksibel", "kapan saja"]):
            date_generator = IntelligentDateGenerator()
            smart_suggestions = date_generator.generate_dates_from_keywords(
                user_input,
                detected_destination.name if detected_destination else None,
                origin.get("name")
            )
            if smart_suggestions:
                intelligent_dates = date_generator.format_suggestions(smart_suggestions)

        # Store packages in conversation state for later selection
        self.conversation_state["suggested_packages"] = packages
        
        # Format the suggestions
        flight_suggestions = PackageGenerator.format_package_suggestion(packages)
        return flight_suggestions + intelligent_dates

    def search_and_format_flights(
        self, origin: str, destination: str, departure_date: str, adults: int = 1
    ) -> str:
        """
        Search for flights and return formatted results.

        This method integrates with the Amadeus API to search for real flight data.

        Args:
            origin: IATA code or city name (e.g., 'JKT' for Jakarta)
            destination: IATA code or city name (e.g., 'DPS' for Bali)
            departure_date: Date in YYYY-MM-DD format

        Returns:
            Formatted flight results or error message
        """
        if not AMADEUS_CONFIGURED:
            logger.warning("Amadeus API not configured")
            return "⚠️ Flight search is not available. Please configure Amadeus API credentials."

        logger.info(
            f"Flight search requested: {origin} -> {destination} on {departure_date}"
        )

        result = search_flights(origin, destination, departure_date, adults=adults)

        if result["success"]:
            formatted = format_flight_results(result["data"])
            logger.info(f"Flight search successful, found {len(result['data'])} flights")
            return formatted
        else:
            formatted_error = format_flight_error(result["error"])
            logger.error(f"Flight search failed: {result['error']}")
            return formatted_error
    
    def _detect_date_preference(self, user_input: str) -> Optional[str]:
        """
        Detect if user wants 'cheapest' or 'custom' date search
        
        Args:
            user_input: User's message
            
        Returns:
            'cheapest', 'custom', or None if unclear
        """
        user_lower = user_input.lower()
        
        # Keywords for "cheapest" preference
        cheapest_keywords = [
            "termurah", "murah", "hemat", "cheapest", "cheap",
            "paling murah", "budget", "irit", "seminggu kedepan",
            "next week", "minggu depan", "auto", "otomatis"
        ]
        
        # Keywords for "custom" preference
        custom_keywords = [
            "pilih sendiri", "custom", "tanggal", "date",
            "spesifik", "specific", "atur sendiri", "tentukan",
            "januari", "februari", "maret", "april", "mei", "juni",
            "juli", "agustus", "september", "oktober", "november", "desember"
        ]
        
        has_cheapest = any(kw in user_lower for kw in cheapest_keywords)
        has_custom = any(kw in user_lower for kw in custom_keywords)
        
        if has_cheapest and not has_custom:
            return "cheapest"
        elif has_custom and not has_cheapest:
            return "custom"
        else:
            return None
    
    def _detect_package_selection(self, user_input: str) -> Optional[int]:
        """
        Detect if user is selecting a package number (1-6)
        
        Args:
            user_input: User's message
            
        Returns:
            Package index (0-based) or None if not a selection
        """
        user_lower = user_input.lower()
        
        # Common selection phrases
        selection_phrases = [
            r"(?:pilih|pilihan|paket|nomer|nomor|number|opsi|option)\s*(?:#|no\.?|num\.?)?\s*(\d+)",
            r"(?:yang|yg)\s*(?:nomer|nomor|number|no\.?|num\.?)?\s*(\d+)",
            r"^(\d+)$",  # Just a number
            r"cari\s+(?:harga\s+)?(?:real-time\s+)?(?:yang\s+)?(?:nomer|nomor|number|no\.?)?\s*(\d+)",
            r"mau\s+(?:yang\s+)?(?:nomer|nomor|number|no\.?)?\s*(\d+)",
        ]
        
        for pattern in selection_phrases:
            match = re.search(pattern, user_lower)
            if match:
                try:
                    number = int(match.group(1))
                    # Valid package numbers are 1-6, convert to 0-based index
                    if 1 <= number <= 6:
                        return number - 1
                except (ValueError, IndexError):
                    continue
        
        return None
    
    def _ask_date_preference(self, origin: str, destination: str, origin_city: str = None, dest_city: str = None) -> str:
        """
        Generate season selection menu for user
        
        Args:
            origin: Origin airport code
            destination: Destination airport code
            origin_city: Origin city name (optional)
            dest_city: Destination city name (optional)
            
        Returns:
            Season selection menu or fallback question
        """
        # Try to get season selection menu
        season_menu = format_season_selection(destination, dest_city)
        
        if season_menu:
            # We have season data - show season selection
            intro = f"\n✈️ **Oke, siap carikan tiket {origin_city or origin} → {dest_city or destination}!**\n"
            intro += "\nAku bakal cari **pilihan terbaik** (harga & kualitas) di season yang kamu pilih:\n"

            return intro + season_menu
        else:
            # No season data - fallback to simple question
            origin_name = origin_city or origin
            dest_name = dest_city or destination

            question = f"\n✈️ **Oke, siap carikan tiket {origin_name} → {dest_name}!**\n\n"
            question += "Kamu mau:\n"
            question += "1️⃣ **Aku carikan yang TERBAIK** seminggu ke depan (smart search: harga + kualitas)\n"
            question += "2️⃣ **Aku pilih tanggal sendiri** (kasih tau range tanggalnya)\n\n"
            question += "Pilih yang mana? 😊"

            return question
    
    def _handle_smart_flight_search(self, origin: str, destination: str, user_input: str, origin_city: str = None, dest_city: str = None) -> str:
        """
        Handle smart flight search with season selection
        
        Args:
            origin: Origin airport code
            destination: Destination airport code
            user_input: User's input
            origin_city: Origin city name
            dest_city: Destination city name
            
        Returns:
            Response string
        """
        try:
            from src.config import ENABLE_BOOKING_LINKS, ENABLE_SEASON_INTELLIGENCE, TRIP_CONTEXT_FILE
        except ImportError:
            from config import ENABLE_BOOKING_LINKS, ENABLE_SEASON_INTELLIGENCE, TRIP_CONTEXT_FILE
        
        # Check if user is selecting a season (number 1-6)
        season_match = re.search(r'\b([1-6])\b', user_input)
        if season_match and get_all_seasons(destination):
            season_num = int(season_match.group(1))
            season_index = season_num - 1  # Convert to 0-based
            
            # Get date range for selected season
            date_range = get_season_date_range(destination, season_index)
            
            if date_range:
                start_date, end_date = date_range
                seasons = get_all_seasons(destination)
                selected_season = seasons[season_index]
                
                logger.info(f"User selected season {season_num}: {selected_season.season_name}")
                logger.info(f"Searching in date range: {start_date} to {end_date}")

                # Search for best flight in this season using smart scoring
                result = search_flights_in_date_range(
                    origin, destination,
                    start_date, end_date,
                    adults=1,
                    max_searches=7  # Limit to 7 searches within the season
                )
                
                if result["success"]:
                    # Format results
                    response = format_date_range_results(result, origin, destination)
                    
                    # Add context about the season
                    response += f"\n\n📊 **Season Info:**\n"
                    response += f"  • Season: {selected_season.season_name}\n"
                    response += f"  • Searched: {start_date} to {end_date}\n"
                    response += f"  • {selected_season.recommendation}\n"
                    
                    # Add booking links
                    if ENABLE_BOOKING_LINKS and result["cheapest_date"]:
                        booking_links = format_booking_links(
                            origin, destination,
                            result["cheapest_date"],
                            passengers=1
                        )
                        response += f"\n{booking_links}"
                    
                    # Save trip context with season info
                    self._save_trip_context(
                        origin, destination, origin_city, dest_city,
                        result["cheapest_date"], result["cheapest_flight"],
                        season_name=selected_season.season_name
                    )
                    
                    return response
                else:
                    return f"❌ {result.get('error', 'Tidak ada penerbangan ditemukan di season ini')}"
        
        # Detect date preference (for fallback if no season data)
        preference = self._detect_date_preference(user_input)
        
        if preference == "cheapest":
            # Search best flight in next week using smart scoring
            logger.info(f"User chose 'best value' - running smart search for next 7 days")
            result = search_cheapest_flight_next_week(origin, destination, adults=1)
            
            if result["success"]:
                # Format results
                response = format_date_range_results(result, origin, destination)
                
                # Add season intelligence
                if ENABLE_SEASON_INTELLIGENCE:
                    season_rec = format_season_recommendation(destination, dest_city)
                    if season_rec:
                        response += f"\n{season_rec}"
                
                # Add booking links
                if ENABLE_BOOKING_LINKS and result["cheapest_date"]:
                    booking_links = format_booking_links(
                        origin, destination,
                        result["cheapest_date"],
                        passengers=1
                    )
                    response += f"\n{booking_links}"
                
                # Save trip context
                self._save_trip_context(
                    origin, destination, origin_city, dest_city,
                    result["cheapest_date"], result["cheapest_flight"]
                )
                
                return response
            else:
                return f"❌ {result.get('error', 'Tidak ada penerbangan ditemukan')}"
        
        elif preference == "custom":
            # Ask for custom date range
            return ("\n📅 **Oke, mau pilih tanggal sendiri!**\n\n"
                   "Kasih tau range tanggalnya ya, contoh:\n"
                   "- '25-30 Januari 2025'\n"
                   "- '2025-01-25 sampai 2025-01-30'\n"
                   "- 'Tanggal 15 Februari'\n\n"
                   "Mau cari tanggal berapa? 😊")
        
        else:
            # Unclear - ask for clarification (show season selection if available)
            return self._ask_date_preference(origin, destination, origin_city, dest_city)
    
    def _save_trip_context(
        self,
        origin: str,
        destination: str,
        origin_city: Optional[str],
        dest_city: Optional[str],
        date: str,
        flight_data: Dict[str, Any],
        season_name: Optional[str] = None
    ) -> None:
        """
        Save trip context for future itinerary generation
        
        Args:
            origin: Origin airport code
            destination: Destination airport code
            origin_city: Origin city name
            dest_city: Destination city name
            date: Departure date
            flight_data: Flight data from API
            season_name: Selected season name (optional)
        """
        try:
            try:
                from src.config import TRIP_CONTEXT_FILE, ENABLE_BOOKING_LINKS
            except ImportError:
                from config import TRIP_CONTEXT_FILE, ENABLE_BOOKING_LINKS
            
            # Extract flight details
            price_info = flight_data.get("price", {})
            price = float(price_info.get("grandTotal", 0))
            currency = price_info.get("currency", "EUR")
            
            # Convert to IDR if needed
            if currency != "IDR":
                try:
                    from src.flight_api import get_exchange_rate
                except ImportError:
                    from flight_api import get_exchange_rate
                rate = get_exchange_rate(currency, "IDR")
                if rate:
                    price = price * rate
                    currency = "IDR"
            
            # Get airline info
            itineraries = flight_data.get("itineraries", [])
            airline = None
            duration = None
            stops = None
            
            if itineraries:
                first_leg = itineraries[0]
                segments = first_leg.get("segments", [])
                if segments:
                    try:
                        from src.flight_api import get_airline_name_safe, format_duration
                    except ImportError:
                        from flight_api import get_airline_name_safe, format_duration
                    airline_code = segments[0].get("operating", {}).get("carrierCode", "")
                    if not airline_code:
                        airline_code = segments[0].get("carrierCode", "")
                    airline = get_airline_name_safe(airline_code, origin, destination)
                    duration = format_duration(first_leg.get("duration", ""))
                    stops = len(segments) - 1
            
            # Build notes with season info if available
            notes = None
            if season_name:
                notes = f"Searched in {season_name}"
            
            # Create trip context
            context = TripContext(
                origin=origin,
                origin_city=origin_city or origin,
                destination=destination,
                destination_city=dest_city or destination,
                departure_date=date,
                passengers=1,
                price=price,
                currency=currency,
                airline=airline,
                flight_duration=duration,
                stops=stops,
                booking_links=get_booking_links_dict(origin, destination, date, 1) if ENABLE_BOOKING_LINKS else None,
                notes=notes
            )
            
            # Save to file
            manager = TripContextManager(TRIP_CONTEXT_FILE)
            success = manager.save_context(context)
            
            if success:
                logger.info(f"Saved trip context: {origin} -> {destination} on {date}")
            else:
                logger.warning("Failed to save trip context")
                
        except Exception as e:
            logger.error(f"Error saving trip context: {e}", exc_info=True)



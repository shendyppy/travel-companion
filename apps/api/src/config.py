"""
Configuration module for Travel Buddy AI Assistant

This module contains all constants and configuration settings for the Travel Buddy application.
It's the single source of truth for settings, preventing hardcoded values scattered throughout the code.
"""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv # type: ignore

# Load environment variables from .env file
load_dotenv()

# ============================================================================
# PATHS
# ============================================================================
# Anchored once here instead of being counted with '..' from each file that
# needs it. flight_api.py used to locate its datasets via
# dirname(__file__)/../data, which broke the moment the module moved into
# providers/. This way the data path does not care where the caller lives.
BASE_DIR = Path(__file__).resolve().parent.parent  # apps/api/
DATA_DIR = BASE_DIR / "data"

# ============================================================================
# LLM CONFIGURATION
# ============================================================================

# Default LLM provider (options: gemini, glm, openai, custom)
# Set via environment variable: LLM_PROVIDER
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")

# Thinking budget for LLM extended reasoning (where supported)
# Higher values = more reasoning (better quality, more tokens used)
# 0 = disabled, 5000-10000 = good balance for travel planning
THINKING_BUDGET = int(os.getenv("THINKING_BUDGET", "5000"))

# LLM temperature (0.0 = deterministic, 1.0 = creative)
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))

# ============================================================================
# REMOVED: agent persona and CLI-era constants
# ============================================================================
#
# TRAVEL_PERSONA moved to src/agent/persona.py and was rewritten in English.
# An Indonesian system prompt biases every reply toward Indonesian regardless
# of what the user actually wrote, and the agent is multilingual.
#
# UI_*, EXIT_COMMANDS, MAX_INPUT_LENGTH and the ERROR_* strings existed for the
# interactive CLI in main.py, which went away when this became an HTTP service.

# ============================================================================
# AMADEUS API CONFIGURATION
# ============================================================================

# Amadeus API credentials for flight search
AMADEUS_CLIENT_ID = os.getenv("AMADEUS_CLIENT_ID")
AMADEUS_CLIENT_SECRET = os.getenv("AMADEUS_CLIENT_SECRET")

# Check if Amadeus credentials are available
AMADEUS_CONFIGURED = bool(AMADEUS_CLIENT_ID and AMADEUS_CLIENT_SECRET)

# ============================================================================
# GOOGLE FLIGHTS API CONFIGURATION (via RapidAPI)
# ============================================================================

# RapidAPI credentials for Google Flights
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST", "google-flights-data.p.rapidapi.com")

# Enable/disable Google Flights as primary provider
GOOGLE_FLIGHTS_ENABLED = os.getenv("GOOGLE_FLIGHTS_ENABLED", "true").lower() == "true"

# Check if Google Flights credentials are available
GOOGLE_FLIGHTS_CONFIGURED = bool(RAPIDAPI_KEY)

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

# Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL = logging.INFO

# Log message format: includes timestamp, level, logger name, and message
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Log file location (optional, comment out to disable file logging)
LOG_FILE = "travel_buddy.log"

# ============================================================================
# SMART FLIGHT SEARCH CONFIGURATION
# ============================================================================

# Default date range for automatic "cheapest" search (in days)
# 7 days = 1 week, balances API cost with finding good deals
DEFAULT_DATE_RANGE_DAYS = 7

# Maximum number of API calls allowed in a single date range search
# Safety limit to prevent excessive API usage
MAX_DATE_SEARCH_CALLS = 30

# Trip context storage file location
TRIP_CONTEXT_FILE = str(DATA_DIR / "trip_contexts.json")

# Enable/disable booking links feature
ENABLE_BOOKING_LINKS = True

# Enable/disable season intelligence recommendations
ENABLE_SEASON_INTELLIGENCE = True


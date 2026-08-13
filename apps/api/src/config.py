"""
Configuration module for Travel Buddy AI Assistant

This module contains all constants and configuration settings for the Travel Buddy application.
It's the single source of truth for settings, preventing hardcoded values scattered throughout the code.
"""

import logging
import os
from dotenv import load_dotenv # type: ignore

# Load environment variables from .env file
load_dotenv()

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
# AI AGENT PERSONA & BEHAVIOR
# ============================================================================

# System prompt that defines the Travel Buddy's personality and behavior
# This is crucial for shaping how the AI responds to users
TRAVEL_PERSONA = (
    "Anda adalah 'Budget Travel Buddy', ahli perjalanan AI spesialis liburan hemat dengan fokus pada nilai terbaik untuk setiap rupiah! "
    "Passion Anda adalah menemukan hidden gems, destinasi worth-it, dan tips traveling yang tidak akan menguras kantong. "
    "\n\nPersona Anda:\n"
    "- Sangat antusias dengan budget traveling dan tips hemat\n"
    "- Selalu bersemangat sharing tempat-tempat murah yang amazing\n"
    "- Expert dalam traveling di Indonesia dan Asia Tenggara\n"
    "- Percaya bahwa traveling berkualitas tidak harus mahal\n"
    "- Suka kasih pro tips untuk nabung biaya traveling\n"
    "\n\nGaya bahasa Anda:\n"
    "- Energetik dan selalu excited dengan destinasi hemat\n"
    "- Sering pakai kata-kata seperti 'budget-friendly', 'worth-it', 'hidden gem', 'anti ribet'\n"
    "- Kasih estimasi biaya realistis dalam IDR\n"
    "- Fokus pada value for money bukan cuma harga murah\n"
    "- Proaktif nanyain preferensi: budget, tipe liburan, durasi\n"
    "\n\nKemampuan Khusus:\n"
    "1. **Rekomendasi Destinasi Hemat**: Tanpa flight details pun, Anda bisa kasih rekomendasi!\n"
    "   - Tanya dulu: Tipe libaran apa? (pantai, gunung, budaya, kota)\n"
    "   - Tanya budget harian atau total trip\n"
    "   - Tanya preferensi dalam negeri atau luar negeri\n"
    "   - Kasih rekomendasi dengan estimasi biaya jelas\n\n"
    "2. **Flight Search Expert (PENTING)**:\n"
    "   - Anda DAPAT mencari penerbangan REAL via Amadeus API\n"
    "   - Untuk cari flight: butuh asal (Jakarta/JKT), tujuan (Bali/DPS), tanggal (YYYY-MM-DD)\n"
    "   - Selalu kasih insights tentang harga termurah dan waktu terbaik\n\n"
    "3. **Budget Breakdown Specialist**:\n"
    "   - Kasih estimasi detail: akomodasi, makan, transport, aktivitas\n"
    "   - Kasih tips hemat untuk setiap kategori\n"
    "   - Suggest alternatif untuk irit biaya\n\n"
    "4. **Hidden Gems Hunter**:\n"
    "   - Tau destinasi less mainstream tapi bagus\n"
    "   - Kasih tips waktu terbaik kunjungi biar lebih hemat\n"
    "\n\nCara Respon (INI WAJIB!):\n"
    "- **Mulai dengan energy**: 'Wih, seru banget!', 'Perfect!', 'Love this idea!'\n"
    "- **Detect kebutuhan**: Jika user belum jelas destinasi, tanya preferensi dulu\n"
    "- **Proaktif dengan budget**: Sering tanyakan 'Budget sekitar berapa ya?' atau 'Pengiritan di bagian mana?'\n"
    "- **Kasih value**: Setiap rekomendasi harus ada 'kenapa worth-it'\n"
    "- **End dengan action**: 'Mau cari flightnya sekarang?' atau 'Destinasi ini cocok nih!'\n\n"
    "Contoh flow:\n"
    "User: 'Mau liburan kemana ya yg bagus?'\n"
    "Anda: 'Wih, perfect timing buat planning! Biar kasih rekomendasi yang pas, kamu suka liburan tipe apa? Pantai, gunung, kulineran, atau explore kota? Budget sekitar berapa per hari atau total tripnya?'\n"
)

# ============================================================================
# INPUT VALIDATION RULES
# ============================================================================

# Commands that signal user wants to exit the application
EXIT_COMMANDS = ["keluar", "exit", "quit", "stop"]

# Maximum input length to prevent prompt injection attacks
MAX_INPUT_LENGTH = 5000

# ============================================================================
# USER INTERFACE MESSAGES
# ============================================================================

# Header displayed when app starts
UI_HEADER = (
    "\n" + "=" * 50 + "\n"
    "🌍 TRAVEL BUDDY - AI Travel Assistant 🌍\n" + "=" * 50 + "\n"
)

# Instructions shown to user on startup
UI_INSTRUCTIONS = (
    f"AI Provider: Budget Travel Agent (Universal LLM Support)\n"
    "Supported: Gemini, GLM, OpenAI | Ketik 'keluar'/'exit' untuk mengakhiri.\n"
    "=" * 50 + "\n"
)

# Message shown when user exits gracefully
UI_EXIT_MESSAGE = (
    "\n✈️  Sampai jumpa! Selamat menikmati perjalanan Anda! Safe travels! 🌴\n"
)

# Message shown when user provides empty input
UI_EMPTY_INPUT = "❌ Silakan masukkan pertanyaan Anda.\n"

# Message shown while AI is processing
UI_THINKING = "Travel Buddy sedang memikirkan..."

# Error message prefix (followed by error details)
UI_ERROR_PREFIX = "❌ Terjadi kesalahan: "

# ============================================================================
# ERROR MESSAGES
# ============================================================================

ERROR_EMPTY_INPUT = "Input tidak boleh kosong"
ERROR_INPUT_TOO_LONG = f"Input terlalu panjang (maksimal {MAX_INPUT_LENGTH} karakter)"
ERROR_API_KEY_MISSING = "Tidak ada API key yang ditemukan. Set salah satu: GEMINI_API_KEY, GLM_API_KEY, atau OPENAI_API_KEY"
ERROR_INIT_FAILED = "Gagal menginisialisasi LLM client."
ERROR_NETWORK = "❌ Kesalahan jaringan. Periksa koneksi internet Anda."
ERROR_API = "❌ Kesalahan layanan. Coba lagi nanti."
ERROR_UNEXPECTED = "❌ Kesalahan tidak terduga."

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
TRIP_CONTEXT_FILE = "data/trip_contexts.json"

# Enable/disable booking links feature
ENABLE_BOOKING_LINKS = True

# Enable/disable season intelligence recommendations
ENABLE_SEASON_INTELLIGENCE = True


"""
Travel Agent Main Application
Entry point untuk Travel Buddy AI Assistant

This module serves as the entry point for the Travel Buddy application.
It handles:
- Logging initialization
- Gemini API client setup
- Main conversation loop
- User interaction handling
- Graceful error handling and exit
"""

import logging
import os
import sys
from typing import Optional

# Fix encoding for emojis on Windows
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    # Try to enable UTF-8 mode for stdout/stderr on Windows
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    except Exception:
        pass

from dotenv import load_dotenv # type: ignore

try:
    from src.agent import TravelAgent
    from src.config import (
        LOG_LEVEL,
        LOG_FORMAT,
        LOG_FILE,
        UI_HEADER,
        UI_INSTRUCTIONS,
        UI_EXIT_MESSAGE,
        UI_THINKING,
        ERROR_API_KEY_MISSING,
        ERROR_NETWORK,
        ERROR_API,
    )
except ImportError:
    from agent import TravelAgent
    from config import (
        LOG_LEVEL,
        LOG_FORMAT,
        LOG_FILE,
        UI_HEADER,
        UI_INSTRUCTIONS,
        UI_EXIT_MESSAGE,
        UI_THINKING,
        ERROR_API_KEY_MISSING,
        ERROR_NETWORK,
        ERROR_API,
    )

# ============================================================================
# LOGGING SETUP
# ============================================================================


def setup_logging() -> None:
    """
    Configure logging for the application.

    This sets up:
    - Console output for user-facing messages
    - File output for debugging
    - Appropriate log levels for different components

    The logging system helps with:
    - Debugging issues in production
    - Tracking user interactions
    - Performance monitoring
    - Error tracking
    """
    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT)

    # Set up console handler (for development/debugging)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(
        logging.WARNING
    )  # Only show warnings and errors in console
    console_handler.setFormatter(formatter)

    # Set up file handler (for complete logs)
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(LOG_LEVEL)
    file_handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(LOG_LEVEL)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Get logger for this module
    logger = logging.getLogger(__name__)
    logger.info("=" * 80)
    logger.info("Budget Travel Agent Application Started")
    logger.info("Universal LLM Support: Gemini, GLM, OpenAI")
    logger.info("=" * 80)


# ============================================================================
# INITIALIZATION
# ============================================================================


def load_environment() -> None:
    """
    Load environment variables from .env file.

    The .env file should be in the root directory of the project and contain:
    - GEMINI_API_KEY: Your Google Gemini API key

    Why this approach?
    - Keeps secrets out of version control
    - Different .env files for different environments (dev, staging, prod)
    - Easy to change without code changes
    """
    load_dotenv()
    logger = logging.getLogger(__name__)
    logger.debug("Environment variables loaded")


def check_api_keys() -> Optional[str]:
    """
    Check if any LLM API key is available and return provider name.

    This function:
    - Checks for API keys from all supported providers
    - Returns the first available provider
    - Provides helpful error messages if no keys found

    Returns:
        str: Provider name if found, None if none available
    """
    logger = logging.getLogger(__name__)

    # Check in order of preference
    provider_checks = [
        ("gemini", "GEMINI_API_KEY", "https://makersuite.google.com/app/apikey"),
        ("glm", "GLM_API_KEY", "https://open.bigmodel.cn/"),
        ("openai", "OPENAI_API_KEY", "https://platform.openai.com/api-keys"),
        ("custom", "CUSTOM_API_KEY", None),
    ]

    for provider, env_key, url in provider_checks:
        if os.getenv(env_key):
            logger.info(f"Found API key for provider: {provider}")
            return provider

    # No keys found
    print("❌ " + ERROR_API_KEY_MISSING)
    print("\n💡 Tips: Set one of these environment variables in your .env file:")
    for provider, env_key, url in provider_checks:
        if url:
            print(f"  - {env_key}: Get from {url}")
    return None


# ============================================================================
# MAIN APPLICATION LOGIC
# ============================================================================


def handle_user_interaction(agent: TravelAgent) -> bool:
    """
    Handle a single user interaction cycle.

    This function:
    - Gets input from user
    - Validates input
    - Checks for exit commands
    - Sends message to agent
    - Displays response

    Args:
        agent: The TravelAgent instance

    Returns:
        True if the conversation should continue, False if user wants to exit
    """
    logger = logging.getLogger(__name__)

    try:
        # Get user input
        user_input = input("Anda: ").strip()

        # Validate input
        if not agent.is_valid_input(user_input):
            return True  # Continue loop

        # Check if user wants to exit
        if agent.should_exit(user_input):
            return False  # Exit loop

        # Show thinking message
        print(f"\n{UI_THINKING}")

        # Send message and get response
        response = agent.send_message(user_input)

        # Display response if successful
        if response:
            print(f"\nTravel Buddy: {response}\n")
        else:
            print(f"\n{ERROR_API}\n")

        return True  # Continue loop

    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received (Ctrl+C)")
        return False

    except Exception as e:
        logger.error(f"Unexpected error in user interaction: {e}", exc_info=True)
        print(f"\n❌ Terjadi kesalahan yang tidak terduga: {e}")
        print("Silakan coba lagi atau ketik 'exit' untuk keluar.\n")
        return True  # Continue loop


def run_travel_agent() -> None:
    """
    Jalankan Budget Travel Agent dengan universal LLM support.

    This is the main application function that:
    1. Displays welcome message
    2. Checks for available API keys
    3. Creates the Travel Agent with universal LLM
    4. Runs the conversation loop
    5. Handles graceful shutdown
    """
    logger = logging.getLogger(__name__)

    try:
        # Display welcome message
        print(UI_HEADER)
        print(UI_INSTRUCTIONS)

        # Check which provider to use
        provider = check_api_keys()
        if not provider:
            logger.error("No API keys found, exiting")
            sys.exit(1)

        # Initialize Travel Agent with universal LLM
        try:
            agent = TravelAgent(provider=provider)
            print(f"\n✅ Using {provider.title()} as AI provider")
        except Exception as e:
            logger.error(f"Failed to initialize TravelAgent: {e}", exc_info=True)
            print(f"❌ Gagal menginisialisasi Travel Agent dengan {provider}. Cek koneksi internet Anda.")
            sys.exit(1)

        # Main conversation loop
        logger.info("Starting conversation loop")
        while True:
            if not handle_user_interaction(agent):
                break

        # User exited gracefully
        print(UI_EXIT_MESSAGE)
        logger.info("Application closed gracefully")

    except KeyboardInterrupt:
        # Handle Ctrl+C at top level
        print(UI_EXIT_MESSAGE)
        logger.info("Application interrupted by user (Ctrl+C)")

    except Exception as e:
        # Catch any unexpected errors
        logger.error(f"Unexpected error in main loop: {e}", exc_info=True)
        print(f"\n❌ Terjadi kesalahan yang tidak terduga:")
        print(f"Error: {e}")
        print("\nSilakan lapor ke developer jika masalah ini berlanjut.")
        sys.exit(1)


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    """
    Application entry point.

    This pattern allows the module to be imported without automatically
    running the application, which is useful for testing and integration.
    """
    # Setup logging first (before anything else)
    setup_logging()

    # Load environment variables
    load_environment()

    # Run the application
    run_travel_agent()

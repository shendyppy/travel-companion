"""
Travel Agent REST API

FastAPI-based REST API for Travel Buddy AI Assistant.
Ready for Flutter mobile app integration.

Usage:
    uvicorn src.api:app --reload --port 8000
    
Endpoints:
    POST /api/chat              - Chat with AI (main)
    POST /api/flights/search    - Direct flight search
    GET  /api/health            - Health check
    GET  /api/suggestions/initial - Get initial suggestions for app launch
"""

import logging
import os
import uuid
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()

# Import internal modules - try relative first, then absolute
try:
    from src.models import (
        ChatRequest,
        ChatResponse,
        FlightSearchRequest,
        FlightSearchResponse,
        FlightInfo,
        HealthResponse,
    )
    from src.config import (
        AMADEUS_CONFIGURED,
        LLM_PROVIDER,
    )
    from src.suggestion_engine import (
        SuggestionEngine,
        ConversationState,
        get_suggestion_engine,
    )
    from src.session_store import get_session_store, close_session_store
except ImportError:
    # Fallback for running from within src directory
    from models import (
        ChatRequest,
        ChatResponse,
        FlightSearchRequest,
        FlightSearchResponse,
        FlightInfo,
        HealthResponse,
    )
    from config import (
        AMADEUS_CONFIGURED,
        LLM_PROVIDER,
    )
    from suggestion_engine import (
        SuggestionEngine,
        ConversationState,
        get_suggestion_engine,
    )
    from session_store import get_session_store, close_session_store

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==============================================================================
# APP INITIALIZATION
# ==============================================================================

app = FastAPI(
    title="Travel Buddy API",
    description="AI-powered travel assistant API for budget travel planning",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware for Flutter app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your Flutter app domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session storage - uses Redis if configured, otherwise in-memory
# In-memory agents cache (agents can't be serialized to Redis directly)
_agents: dict = {}

# Suggestion engine
suggestion_engine = get_suggestion_engine()


async def get_or_create_agent(session_id: Optional[str] = None) -> tuple:
    """
    Get existing agent from session or create new one.
    
    Session metadata is stored in Redis (if configured) for persistence.
    Agent instances are kept in memory since they can't be serialized.
    """
    try:
        from src.agent import TravelAgent
    except ImportError:
        from agent import TravelAgent
    
    store = get_session_store()
    
    # Check if session exists
    if session_id:
        session_data = await store.get(session_id)
        if session_data and session_id in _agents:
            return _agents[session_id], session_id, session_data
    
    # Create new session
    new_session_id = session_id or str(uuid.uuid4())
    agent = TravelAgent()
    
    # Session state for tracking conversation context
    session_data = {
        "created_at": datetime.now().isoformat(),
        "state": ConversationState.NEW.value,
        "destination": None,
        "origin": None,
        "message_count": 0,
    }
    
    # Store session data
    await store.set(new_session_id, session_data)
    _agents[new_session_id] = agent
    
    logger.info(f"Created new session: {new_session_id}")
    return agent, new_session_id, session_data


# ==============================================================================
# ENDPOINTS
# ==============================================================================

@app.get("/api/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """
    Health check endpoint for monitoring and load balancer probes.
    
    Returns service status, version, and configuration info.
    """
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        llm_provider=LLM_PROVIDER,
        amadeus_configured=AMADEUS_CONFIGURED,
        timestamp=datetime.now()
    )


@app.post("/api/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(request: ChatRequest):
    """
    Main chat endpoint for conversation with Travel Buddy AI.
    
    Handles:
    - Natural language travel questions
    - Automatic flight search detection
    - Multi-turn conversations (via session_id)
    - Context-aware suggestions for next prompts
    
    Returns AI response with suggestions, optionally with flight results if detected.
    """
    try:
        # Get or create agent for this session
        agent, session_id, session_data = await get_or_create_agent(request.session_id)
        
        logger.info(f"Chat request [session={session_id[:8]}...]: {request.message[:50]}...")
        
        # Send message to agent
        result = agent.send_message(request.message)
        
        if result is None:
            raise HTTPException(status_code=500, detail="Failed to get response from AI")
        
        # Handle different response types
        if isinstance(result, dict):
            response_text = result.get("text", str(result))
            flights_data = result.get("flights", None)
        else:
            response_text = str(result)
            flights_data = None
        
        # Convert flights to FlightInfo if present
        flights = None
        has_flights = False
        if flights_data and isinstance(flights_data, list):
            flights = [_convert_to_flight_info(f) for f in flights_data if f]
            has_flights = bool(flights)
        
        # Detect conversation state and generate suggestions
        current_destination = session_data.get("destination")
        state, detected_destination = suggestion_engine.detect_state_from_response(
            user_message=request.message,
            ai_response=response_text,
            has_flights=has_flights,
            current_destination=current_destination
        )
        
        # Update session data with new state
        session_data["state"] = state.value
        session_data["message_count"] = session_data.get("message_count", 0) + 1
        if detected_destination:
            session_data["destination"] = detected_destination
        
        # Save updated session
        store = get_session_store()
        await store.set(session_id, session_data)
        
        # Generate context-aware suggestions
        suggestions = suggestion_engine.generate_suggestions(
            state=state,
            destination=detected_destination or current_destination,
            has_flights=has_flights,
            response_text=response_text,
            count=4
        )
        
        return ChatResponse(
            response=response_text,
            flights=flights,
            session_id=session_id,
            suggestions=suggestions
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


@app.post("/api/chat/stream", tags=["Chat"])
async def chat_stream(request: ChatRequest):
    """
    Streaming chat endpoint using Server-Sent Events (SSE).

    This is the preferred endpoint for mobile apps as it provides:
    - Real-time text streaming (better UX)
    - Progressive updates
    - No timeout issues (connection stays alive)

    Returns events in this format:
    - session: Session ID for conversation continuity
    - text: Partial or complete AI response
    - flights: Flight search results (if any)
    - suggestions: Context-aware suggestions
    - done: Stream completion
    - error: Error message if something went wrong
    """
    async def generate_events():
        try:
            # Get or create agent for this session
            agent, session_id, session_data = await get_or_create_agent(request.session_id)

            logger.info(f"Chat stream request [session={session_id[:8]}...]: {request.message[:50]}...")

            # Send session ID first
            import json
            yield f"data: {json.dumps({'type': 'session', 'session_id': session_id})}\n\n"

            # Send message to agent
            result = agent.send_message(request.message)

            if result is None:
                yield f"data: {json.dumps({'type': 'error', 'error': 'Failed to get response from AI'})}\n\n"
                yield f"data: [DONE]\n\n"
                return

            # Handle different response types
            if isinstance(result, dict):
                response_text = result.get("text", str(result))
                flights_data = result.get("flights", None)
            else:
                response_text = str(result)
                flights_data = None

            # Send text response
            yield f"data: {json.dumps({'type': 'text', 'content': response_text})}\n\n"

            # Convert flights to FlightInfo if present
            flights = None
            has_flights = False
            if flights_data and isinstance(flights_data, list):
                flights = [_convert_to_flight_info(f) for f in flights_data if f]
                has_flights = bool(flights)

                # Send flights as separate event
                if flights:
                    flights_dict = [f.model_dump() for f in flights]
                    yield f"data: {json.dumps({'type': 'flights', 'flights': flights_dict})}\n\n"

            # Detect conversation state and generate suggestions
            current_destination = session_data.get("destination")
            state, detected_destination = suggestion_engine.detect_state_from_response(
                user_message=request.message,
                ai_response=response_text,
                has_flights=has_flights,
                current_destination=current_destination
            )

            # Update session data with new state
            session_data["state"] = state.value
            session_data["message_count"] = session_data.get("message_count", 0) + 1
            if detected_destination:
                session_data["destination"] = detected_destination

            # Save updated session
            store = get_session_store()
            await store.set(session_id, session_data)

            # Generate and send suggestions
            suggestions = suggestion_engine.generate_suggestions(
                state=state,
                destination=detected_destination or current_destination,
                has_flights=has_flights,
                response_text=response_text,
                count=4
            )

            yield f"data: {json.dumps({'type': 'suggestions', 'suggestions': suggestions})}\n\n"

            # Send completion signal
            yield f"data: [DONE]\n\n"

        except Exception as e:
            logger.error(f"Chat stream error: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
            yield f"data: [DONE]\n\n"

    return StreamingResponse(
        generate_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )


@app.post("/api/flights/search", response_model=FlightSearchResponse, tags=["Flights"])
async def search_flights(request: FlightSearchRequest):
    """
    Direct flight search endpoint.
    
    Search for flights using Amadeus API.
    Use this when you already have specific origin, destination, and date.
    """
    try:
        try:
            from src.flight_api import search_flights as amadeus_search, format_flight_results
        except ImportError:
            from flight_api import search_flights as amadeus_search, format_flight_results
        
        logger.info(f"Flight search: {request.origin} -> {request.destination} on {request.date}")
        
        # Validate date format
        try:
            datetime.strptime(request.date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail="Invalid date format. Use YYYY-MM-DD (e.g., 2026-03-01)"
            )
        
        # Check Amadeus configuration
        if not AMADEUS_CONFIGURED:
            raise HTTPException(
                status_code=503,
                detail="Flight search unavailable: Amadeus API not configured"
            )
        
        # Search flights
        result = amadeus_search(
            origin=request.origin.upper(),
            destination=request.destination.upper(),
            departure_date=request.date,
            adults=request.passengers
        )
        
        if not result.get("success"):
            return FlightSearchResponse(
                success=False,
                flights=[],
                total_results=0,
                error=result.get("error", "Unknown error"),
                searched_date=request.date
            )
        
        # Convert raw data to FlightInfo objects
        flights_data = result.get("data", [])
        flights = []
        cheapest = None
        cheapest_price = float('inf')
        
        for flight_data in flights_data[:10]:  # Limit to 10 results
            flight_info = _parse_amadeus_flight(flight_data, request.origin, request.destination)
            if flight_info:
                flights.append(flight_info)
                if flight_info.price < cheapest_price:
                    cheapest_price = flight_info.price
                    cheapest = flight_info
        
        return FlightSearchResponse(
            success=True,
            flights=flights,
            cheapest=cheapest,
            total_results=len(flights),
            searched_date=request.date
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Flight search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Flight search error: {str(e)}")


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def _convert_to_flight_info(flight_data: dict) -> Optional[FlightInfo]:
    """Convert raw flight data to FlightInfo model"""
    try:
        return FlightInfo(
            airline=flight_data.get("airline", "Unknown"),
            airline_code=flight_data.get("airline_code", "XX"),
            departure_time=flight_data.get("departure_time", ""),
            arrival_time=flight_data.get("arrival_time", ""),
            origin=flight_data.get("origin", ""),
            destination=flight_data.get("destination", ""),
            price=float(flight_data.get("price", 0)),
            currency=flight_data.get("currency", "IDR"),
            duration=flight_data.get("duration", ""),
            stops=int(flight_data.get("stops", 0))
        )
    except Exception as e:
        logger.warning(f"Failed to convert flight data: {e}")
        return None


def _parse_amadeus_flight(flight_data: dict, origin: str, destination: str) -> Optional[FlightInfo]:
    """Parse Amadeus API response to FlightInfo"""
    try:
        try:
            from src.flight_api import get_airline_name_safe, format_duration, get_exchange_rate
        except ImportError:
            from flight_api import get_airline_name_safe, format_duration, get_exchange_rate
        
        # Get price
        price_info = flight_data.get("price", {})
        price = float(price_info.get("grandTotal", 0))
        currency = price_info.get("currency", "EUR")
        
        # Convert to IDR if needed
        if currency != "IDR":
            rate = get_exchange_rate(currency, "IDR")
            if rate:
                price = price * rate
                currency = "IDR"
        
        # Get itinerary info
        itineraries = flight_data.get("itineraries", [])
        if not itineraries:
            return None
        
        first_leg = itineraries[0]
        segments = first_leg.get("segments", [])
        if not segments:
            return None
        
        first_segment = segments[0]
        last_segment = segments[-1]
        
        # Get airline info
        airline_code = first_segment.get("operating", {}).get("carrierCode", "")
        if not airline_code:
            airline_code = first_segment.get("carrierCode", "XX")
        
        airline_name = get_airline_name_safe(airline_code, origin, destination)
        
        # Get departure and arrival times
        departure = first_segment.get("departure", {})
        arrival = last_segment.get("arrival", {})
        
        return FlightInfo(
            airline=airline_name,
            airline_code=airline_code,
            departure_time=departure.get("at", ""),
            arrival_time=arrival.get("at", ""),
            origin=departure.get("iataCode", origin),
            destination=arrival.get("iataCode", destination),
            price=round(price, 0),
            currency=currency,
            duration=format_duration(first_leg.get("duration", "")),
            stops=len(segments) - 1
        )
        
    except Exception as e:
        logger.warning(f"Failed to parse Amadeus flight: {e}")
        return None


# ==============================================================================
# SUGGESTION ENDPOINTS
# ==============================================================================

class InitialSuggestionsResponse(BaseModel):
    """Response model for initial suggestions"""
    suggestions: list[str] = Field(..., description="Initial suggested prompts")
    greeting: str = Field(..., description="Welcome greeting message")


@app.get("/api/suggestions/initial", response_model=InitialSuggestionsResponse, tags=["Suggestions"])
async def get_initial_suggestions():
    """
    Get initial suggestions for app launch.
    
    Call this when the app first opens to show suggested prompts
    before the user starts typing.
    
    Returns time-aware and seasonal suggestions.
    """
    suggestions = suggestion_engine.get_initial_suggestions(datetime.now())
    
    # Generate time-aware greeting
    hour = datetime.now().hour
    if 5 <= hour < 12:
        greeting = "Selamat pagi! Mau kemana hari ini?"
    elif 12 <= hour < 17:
        greeting = "Selamat siang! Ada rencana liburan?"
    elif 17 <= hour < 20:
        greeting = "Selamat sore! Mau planning trip?"
    else:
        greeting = "Selamat malam! Mau cari tiket untuk besok?"
    
    return InitialSuggestionsResponse(
        suggestions=suggestions,
        greeting=greeting
    )


# ==============================================================================
# STARTUP / SHUTDOWN EVENTS
# ==============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("=" * 50)
    logger.info("Travel Buddy API Starting...")
    logger.info(f"LLM Provider: {LLM_PROVIDER}")
    logger.info(f"Amadeus Configured: {AMADEUS_CONFIGURED}")
    
    # Check session store
    store = get_session_store()
    health = await store.health_check()
    logger.info(f"Session Store: {health.get('type', 'unknown')} - {health.get('status', 'unknown')}")
    
    logger.info("=" * 50)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Travel Buddy API Shutting down...")
    _agents.clear()
    await close_session_store()


# ==============================================================================
# RUN DIRECTLY
# ==============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

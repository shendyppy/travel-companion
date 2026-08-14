"""
Pydantic Models for Travel Agent API

Clean request/response models for REST API endpoints.
"""

from pydantic import BaseModel, Field
from typing import Any, Optional
from datetime import datetime


# ==============================================================================
# CHAT MODELS
# ==============================================================================

class ToolSeed(BaseModel):
    """
    A tool call the client already decided on.

    Sent by the landing page's structured surfaces -- the flight form, the
    inspiration grid, the budget picker -- which know exactly which tool they
    want and with what arguments. The agent runs it before its first turn and
    then narrates the result.

    Validated against an allowlist and the tool's own JSON Schema in
    `agent/seed.py`. Anything that fails is dropped, and the request proceeds on
    `message` alone.
    """
    tool: str = Field(..., description="Tool name. Must be one of the seedable tools.")
    arguments: dict[str, Any] = Field(
        default_factory=dict,
        description="Arguments for the tool, validated against its registered schema.",
    )


class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    message: str = Field(..., description="User message to the travel agent", min_length=1)
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    seed: Optional[ToolSeed] = Field(
        None,
        description=(
            "Optional pre-decided tool call, run before the model's first turn. "
            "Context, not a replacement for `message` -- send both."
        ),
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"message": "Mau liburan ke Bali bulan depan", "session_id": None},
                {"message": "Carikan tiket murah", "session_id": "abc123"},
                {
                    "message": "Cari penerbangan Jakarta ke Bali, 20 September, 1 orang",
                    "session_id": None,
                    "seed": {
                        "tool": "search_flights",
                        "arguments": {
                            "origin": "CGK",
                            "destination": "DPS",
                            "departure_date": "2026-09-20",
                            "adults": 1,
                        },
                    },
                },
            ]
        }
    }


class FlightInfo(BaseModel):
    """Single flight information"""
    airline: str = Field(..., description="Airline name")
    airline_code: str = Field(..., description="IATA airline code")
    departure_time: str = Field(..., description="Departure datetime")
    arrival_time: str = Field(..., description="Arrival datetime")
    origin: str = Field(..., description="Origin airport code")
    destination: str = Field(..., description="Destination airport code")
    price: float = Field(..., description="Price amount")
    currency: str = Field(default="IDR", description="Currency code")
    duration: str = Field(..., description="Flight duration (e.g., '2h 15m')")
    stops: int = Field(default=0, description="Number of stops")


class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    response: str = Field(..., description="AI response text")
    flights: Optional[list[FlightInfo]] = Field(None, description="Flight results if detected")
    session_id: str = Field(..., description="Session ID for future requests")
    suggestions: list[str] = Field(
        default_factory=list,
        description="Context-aware suggested prompts for user's next message"
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "response": "Wih, Bali bulan depan! Keren! Mau berangkat tanggal berapa?",
                    "flights": None,
                    "session_id": "abc123",
                    "suggestions": [
                        "Cari tiket ke Bali",
                        "Rekomendasi hotel di Bali",
                        "Budget liburan ke Bali"
                    ]
                }
            ]
        }
    }


# ==============================================================================
# FLIGHT SEARCH MODELS
# ==============================================================================

class FlightSearchRequest(BaseModel):
    """Request model for direct flight search"""
    origin: str = Field(..., description="Origin airport/city code (e.g., CGK, JKT)", min_length=2, max_length=5)
    destination: str = Field(..., description="Destination airport/city code (e.g., DPS)", min_length=2, max_length=5)
    date: str = Field(..., description="Departure date in YYYY-MM-DD format")
    passengers: int = Field(default=1, ge=1, le=9, description="Number of passengers")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {"origin": "CGK", "destination": "DPS", "date": "2026-03-01", "passengers": 1}
            ]
        }
    }


class FlightSearchResponse(BaseModel):
    """Response model for flight search"""
    success: bool = Field(..., description="Whether search was successful")
    flights: list[FlightInfo] = Field(default=[], description="List of available flights")
    cheapest: Optional[FlightInfo] = Field(None, description="Cheapest flight option")
    total_results: int = Field(default=0, description="Total number of results found")
    error: Optional[str] = Field(None, description="Error message if search failed")
    searched_date: str = Field(..., description="Date that was searched")
    

# ==============================================================================
# HEALTH CHECK MODELS
# ==============================================================================

class HealthResponse(BaseModel):
    """Response model for health check endpoint"""
    status: str = Field(default="healthy", description="Service status")
    version: str = Field(default="2.0.0", description="API version")
    llm_provider: Optional[str] = Field(None, description="Active LLM provider")
    model: Optional[str] = Field(None, description="Resolved LiteLLM model string")
    tools: list[str] = Field(default_factory=list, description="Registered agent tools")
    amadeus_configured: bool = Field(default=False, description="Whether Amadeus API is configured")
    session_store: Optional[str] = Field(None, description="Active session store backend")
    knowledge_base: dict = Field(default_factory=dict, description="Knowledge index availability and size")
    access: dict = Field(default_factory=dict, description="Demo quota limits and BYOK header names")
    timestamp: datetime = Field(default_factory=datetime.now, description="Server timestamp")

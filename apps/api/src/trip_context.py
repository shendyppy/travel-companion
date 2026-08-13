"""
Trip Context Management Module

This module handles storing and retrieving trip context information
for future itinerary generation and trip planning features.
"""

import json
import logging
from datetime import datetime
from typing import Optional, Dict, List, Any
from pathlib import Path
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class TripContext:
    """
    Represents a single trip context with all relevant details
    
    This stores information about a user's flight search/booking
    so we can later generate itineraries, track trips, etc.
    """
    
    # Basic trip info
    origin: str  # Airport code (e.g., "CGK")
    origin_city: str  # City name (e.g., "Jakarta")
    destination: str  # Airport code (e.g., "NRT")
    destination_city: str  # City name (e.g., "Tokyo")
    
    # Flight details
    departure_date: str  # YYYY-MM-DD format
    return_date: Optional[str] = None  # For round trips
    passengers: int = 1
    
    # Price info
    price: Optional[float] = None  # In IDR
    currency: str = "IDR"
    
    # Flight details
    airline: Optional[str] = None
    flight_duration: Optional[str] = None
    stops: Optional[int] = None
    
    # Booking info
    booking_links: Optional[Dict[str, str]] = None  # Platform -> URL
    booked: bool = False
    booking_reference: Optional[str] = None
    
    # Metadata
    search_timestamp: Optional[str] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    
    # Future itinerary planning
    budget_per_day: Optional[float] = None
    travel_preferences: Optional[List[str]] = None  # ["beach", "culture", etc.]
    notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TripContext':
        """Create TripContext from dictionary"""
        return cls(**data)


class TripContextManager:
    """
    Manages persistence and retrieval of trip contexts
    
    Stores trip data in JSON file for later use in itinerary generation
    """
    
    def __init__(self, storage_file: str = "data/trip_contexts.json"):
        """
        Initialize the trip context manager
        
        Args:
            storage_file: Path to JSON file for storing trip contexts
        """
        self.storage_file = Path(storage_file)
        self._ensure_storage_exists()
    
    def _ensure_storage_exists(self) -> None:
        """Ensure storage directory and file exist"""
        try:
            # Create directory if it doesn't exist
            self.storage_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Create empty file if it doesn't exist
            if not self.storage_file.exists():
                self._write_contexts([])
                logger.info(f"Created trip context storage at {self.storage_file}")
        except Exception as e:
            logger.error(f"Error creating storage: {e}")
    
    def _read_contexts(self) -> List[Dict[str, Any]]:
        """Read all contexts from storage file"""
        try:
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Storage file not found: {self.storage_file}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON: {e}")
            return []
        except Exception as e:
            logger.error(f"Error reading contexts: {e}")
            return []
    
    def _write_contexts(self, contexts: List[Dict[str, Any]]) -> bool:
        """Write contexts to storage file"""
        try:
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(contexts, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Error writing contexts: {e}")
            return False
    
    def save_context(self, context: TripContext) -> bool:
        """
        Save a trip context
        
        Args:
            context: TripContext object to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Add timestamp if not present
            if not context.search_timestamp:
                context.search_timestamp = datetime.now().isoformat()
            
            # Read existing contexts
            contexts = self._read_contexts()
            
            # Add new context
            contexts.append(context.to_dict())
            
            # Write back
            success = self._write_contexts(contexts)
            
            if success:
                logger.info(f"Saved trip context: {context.origin} -> {context.destination} on {context.departure_date}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error saving context: {e}")
            return False
    
    def get_recent_contexts(self, limit: int = 10) -> List[TripContext]:
        """
        Get most recent trip contexts
        
        Args:
            limit: Maximum number of contexts to return
            
        Returns:
            List of TripContext objects, most recent first
        """
        try:
            contexts = self._read_contexts()
            
            # Sort by timestamp (most recent first)
            contexts.sort(
                key=lambda x: x.get('search_timestamp', ''),
                reverse=True
            )
            
            # Convert to TripContext objects
            return [
                TripContext.from_dict(ctx)
                for ctx in contexts[:limit]
            ]
            
        except Exception as e:
            logger.error(f"Error getting recent contexts: {e}")
            return []
    
    def get_contexts_by_destination(self, destination: str) -> List[TripContext]:
        """
        Get all trip contexts for a specific destination
        
        Args:
            destination: Airport code or city name
            
        Returns:
            List of TripContext objects
        """
        try:
            contexts = self._read_contexts()
            
            # Filter by destination (match either code or city)
            destination_upper = destination.upper()
            filtered = [
                ctx for ctx in contexts
                if ctx.get('destination', '').upper() == destination_upper
                or ctx.get('destination_city', '').upper() == destination_upper
            ]
            
            # Convert to TripContext objects
            return [TripContext.from_dict(ctx) for ctx in filtered]
            
        except Exception as e:
            logger.error(f"Error getting contexts by destination: {e}")
            return []
    
    def get_context_by_session(self, session_id: str) -> Optional[TripContext]:
        """
        Get trip context for a specific session
        
        Args:
            session_id: Session identifier
            
        Returns:
            TripContext object or None if not found
        """
        try:
            contexts = self._read_contexts()
            
            # Find context with matching session_id
            for ctx in contexts:
                if ctx.get('session_id') == session_id:
                    return TripContext.from_dict(ctx)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting context by session: {e}")
            return None
    
    def clear_all_contexts(self) -> bool:
        """
        Clear all stored trip contexts (use with caution!)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            success = self._write_contexts([])
            if success:
                logger.warning("Cleared all trip contexts")
            return success
        except Exception as e:
            logger.error(f"Error clearing contexts: {e}")
            return False

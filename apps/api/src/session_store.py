"""
Session Store - Abstract session management with Redis support

Provides pluggable session storage for Travel Buddy API.
Automatically uses Redis if REDIS_URL is configured, otherwise falls back to in-memory.

Usage:
    from session_store import get_session_store
    
    store = get_session_store()
    await store.set("session_id", agent_data)
    agent_data = await store.get("session_id")
"""

import os
import json
import pickle
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Optional

logger = logging.getLogger(__name__)


class SessionStore(ABC):
    """Abstract base class for session storage"""
    
    @abstractmethod
    async def get(self, session_id: str) -> Optional[dict]:
        """Get session data by ID"""
        pass
    
    @abstractmethod
    async def set(self, session_id: str, data: dict, ttl: Optional[int] = None) -> bool:
        """Set session data with optional TTL (seconds)"""
        pass
    
    @abstractmethod
    async def delete(self, session_id: str) -> bool:
        """Delete session by ID"""
        pass
    
    @abstractmethod
    async def exists(self, session_id: str) -> bool:
        """Check if session exists"""
        pass
    
    @abstractmethod
    async def clear_all(self) -> int:
        """Clear all sessions, returns count of deleted sessions"""
        pass
    
    @abstractmethod
    async def health_check(self) -> dict:
        """Check store health, returns status dict"""
        pass


class InMemorySessionStore(SessionStore):
    """
    In-memory session storage for development/testing.
    
    Note: Sessions are lost when the server restarts.
    Use RedisSessionStore for production.
    """
    
    def __init__(self, default_ttl: int = 3600):
        self._sessions: dict = {}
        self._default_ttl = default_ttl
        logger.info("Using InMemorySessionStore (development mode)")
    
    async def get(self, session_id: str) -> Optional[dict]:
        session = self._sessions.get(session_id)
        if session:
            # Check if expired
            if session.get("expires_at"):
                if datetime.now() > session["expires_at"]:
                    del self._sessions[session_id]
                    return None
            return session.get("data")
        return None
    
    async def set(self, session_id: str, data: dict, ttl: Optional[int] = None) -> bool:
        ttl = ttl or self._default_ttl
        self._sessions[session_id] = {
            "data": data,
            "created_at": datetime.now(),
            "expires_at": datetime.now() + timedelta(seconds=ttl) if ttl else None
        }
        return True
    
    async def delete(self, session_id: str) -> bool:
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False
    
    async def exists(self, session_id: str) -> bool:
        return session_id in self._sessions
    
    async def clear_all(self) -> int:
        count = len(self._sessions)
        self._sessions.clear()
        return count
    
    async def health_check(self) -> dict:
        return {
            "type": "in_memory",
            "status": "healthy",
            "active_sessions": len(self._sessions)
        }


class RedisSessionStore(SessionStore):
    """
    Redis-based session storage for production.
    
    Features:
    - Persistent sessions across server restarts
    - Automatic TTL-based expiration
    - Scalable across multiple instances
    """
    
    def __init__(self, redis_url: str, default_ttl: int = 3600):
        import redis.asyncio as redis
        
        self._redis = redis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=False  # We'll handle encoding manually for pickle
        )
        self._default_ttl = default_ttl
        self._prefix = "travel_buddy:session:"
        logger.info(f"Using RedisSessionStore (production mode)")
    
    def _key(self, session_id: str) -> str:
        return f"{self._prefix}{session_id}"
    
    async def get(self, session_id: str) -> Optional[dict]:
        try:
            data = await self._redis.get(self._key(session_id))
            if data:
                return pickle.loads(data)
            return None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None
    
    async def set(self, session_id: str, data: dict, ttl: Optional[int] = None) -> bool:
        try:
            ttl = ttl or self._default_ttl
            serialized = pickle.dumps(data)
            await self._redis.setex(
                self._key(session_id),
                ttl,
                serialized
            )
            return True
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False
    
    async def delete(self, session_id: str) -> bool:
        try:
            result = await self._redis.delete(self._key(session_id))
            return result > 0
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False
    
    async def exists(self, session_id: str) -> bool:
        try:
            return await self._redis.exists(self._key(session_id)) > 0
        except Exception as e:
            logger.error(f"Redis exists error: {e}")
            return False
    
    async def clear_all(self) -> int:
        try:
            keys = await self._redis.keys(f"{self._prefix}*")
            if keys:
                return await self._redis.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Redis clear_all error: {e}")
            return 0
    
    async def health_check(self) -> dict:
        try:
            await self._redis.ping()
            keys = await self._redis.keys(f"{self._prefix}*")
            return {
                "type": "redis",
                "status": "healthy",
                "active_sessions": len(keys)
            }
        except Exception as e:
            return {
                "type": "redis",
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def close(self):
        """Close Redis connection"""
        await self._redis.close()


# ==============================================================================
# Factory function
# ==============================================================================

_store_instance: Optional[SessionStore] = None


def get_session_store() -> SessionStore:
    """
    Get the session store instance.
    
    Automatically selects Redis if REDIS_URL is set, otherwise uses in-memory.
    
    Returns:
        SessionStore instance (singleton)
    """
    global _store_instance
    
    if _store_instance is None:
        redis_url = os.getenv("REDIS_URL")
        default_ttl = int(os.getenv("REDIS_SESSION_TTL", "3600"))
        
        if redis_url:
            try:
                _store_instance = RedisSessionStore(redis_url, default_ttl)
            except ImportError:
                logger.warning("redis package not installed, falling back to in-memory")
                _store_instance = InMemorySessionStore(default_ttl)
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}, falling back to in-memory")
                _store_instance = InMemorySessionStore(default_ttl)
        else:
            _store_instance = InMemorySessionStore(default_ttl)
    
    return _store_instance


async def close_session_store():
    """Close session store connection (for shutdown)"""
    global _store_instance
    
    if _store_instance and isinstance(_store_instance, RedisSessionStore):
        await _store_instance.close()
    
    _store_instance = None

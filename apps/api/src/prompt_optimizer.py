"""
Prompt optimization module for reducing token usage

This module implements:
- RAG (Retrieval Augmented Generation) for travel data
- Prompt caching strategies
- Context compression
- Dynamic prompt engineering
"""

import json
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class CompressedPrompt:
    """Compressed prompt with metadata"""
    system_prompt: str
    context: str
    compressed_size: int
    estimated_tokens: int

class PromptOptimizer:
    """Optimizes prompts to reduce token usage"""

    # Base system prompts (optimized)
    MINIMAL_PERSONA = """Budget travel expert. Help users find affordable flights and destinations.
Focus on: 1) Budget-friendly options 2) Smart travel tips 3) Practical advice"""

    DETAILED_PERSONA = """Budget Travel Buddy - Expert in affordable travel across Southeast Asia.
Core values: Value for money, smart tips, hidden gems.
Always ask: budget, preferences, travel dates."""

    # Context templates
    DESTINATION_CONTEXT = """Near {origin}, budget={budget}, type={travel_type}.
Top options: {destinations}"""

    FLIGHT_CONTEXT = """Route: {origin}->{destination}, {date}.
Budget: {budget} per person."""

    @classmethod
    def compress_destination_data(cls, destinations: List[Dict], max_items: int = 3) -> str:
        """
        Compress destination data for context

        Args:
            destinations: List of destination data
            max_items: Maximum items to include

        Returns:
            Compressed string representation
        """
        if not destinations:
            return ""

        # Sort by relevance/recommendation score
        sorted_dests = sorted(destinations, key=lambda x: x.get('score', 0), reverse=True)

        # Compress to key info only
        compressed = []
        for dest in sorted_dests[:max_items]:
            compressed.append(
                f"{dest['name']}({dest['code']}): "
                f"Rp{dest.get('daily_budget', 0)}/day, "
                f"{', '.join(dest.get('highlights', [])[:2])}"
            )

        return "; ".join(compressed)

    @classmethod
    def create_dynamic_prompt(cls, context: Dict) -> CompressedPrompt:
        """
        Create optimized prompt based on context

        Args:
            context: User context and requirements

        Returns:
            Optimized CompressedPrompt
        """
        # Choose persona based on complexity
        if context.get('complex_query', False):
            system_prompt = cls.DETAILED_PERSONA
        else:
            system_prompt = cls.MINIMAL_PERSONA

        # Build context
        context_parts = []

        # User preferences
        if context.get('preferences'):
            prefs = context['preferences']
            context_parts.append(f"User wants: {prefs.get('travel_type', 'general travel')}")
            if prefs.get('budget'):
                context_parts.append(f"Budget: {prefs['budget']}")

        # Location context
        if context.get('origin'):
            context_parts.append(f"From: {context['origin']}")

        # Destination context (compressed)
        if context.get('destinations'):
            dest_context = cls.compress_destination_data(
                context['destinations'],
                max_items=2  # Reduce for less tokens
            )
            if dest_context:
                context_parts.append(f"Consider: {dest_context}")

        # Join all context
        full_context = " | ".join(context_parts)

        # Estimate tokens (roughly 4 chars = 1 token)
        estimated_tokens = len(system_prompt + full_context) // 4

        return CompressedPrompt(
            system_prompt=system_prompt,
            context=full_context,
            compressed_size=len(full_context),
            estimated_tokens=estimated_tokens
        )

class RAGCache:
    """RAG implementation with caching for travel data"""

    def __init__(self):
        # In production, use Redis or database
        self._cache = {}

    def search_destinations(self, query: str, filters: Dict = None) -> List[Dict]:
        """
        Search destinations using RAG-like approach

        Args:
            query: Search query
            filters: Budget, region, type filters

        Returns:
            Relevant destinations
        """
        # Create cache key
        cache_key = f"{query}:{json.dumps(filters or {}, sort_keys=True)}"

        # Check cache
        if cache_key in self._cache:
            return self._cache[cache_key]

        # In production, this would use vector similarity search
        # For now, simple keyword matching
        from destination_data import DESTINATIONS

        results = []
        query_lower = query.lower()

        for dest in DESTINATIONS:
            score = 0

            # Keyword matching
            if any(word in dest.description.lower() for word in query_lower.split()):
                score += 2

            # Filter matching
            if filters:
                if filters.get('budget') and dest.budget_category.value == filters['budget']:
                    score += 3
                if filters.get('region') and dest.region == filters['region']:
                    score += 2
                if filters.get('travel_types'):
                    for t in filters['travel_types']:
                        if t in dest.travel_types:
                            score += 2

            if score > 0:
                results.append({
                    'name': dest.name,
                    'country': dest.country,
                    'description': dest.description,
                    'budget_category': dest.budget_category.value,
                    'score': score,
                    'daily_budget': sum(dest.estimated_daily_cost.values()),
                    'highlights': dest.highlights[:3]
                })

        # Sort by score and cache
        results.sort(key=lambda x: x['score'], reverse=True)
        self._cache[cache_key] = results[:10]  # Cache top 10

        return results[:10]

class SmartPromptManager:
    """Manages prompts with intelligent optimization"""

    def __init__(self):
        self.rag_cache = RAGCache()
        self.optimizer = PromptOptimizer()

    def get_optimized_prompt(self, user_input: str, conversation_history: List = None) -> CompressedPrompt:
        """
        Get optimized prompt for user input

        Args:
            user_input: User message
            conversation_history: Previous messages

        Returns:
            Optimized prompt
        """
        # Analyze user intent
        context = self._analyze_intent(user_input, conversation_history or [])

        # Check if we need RAG
        if self._needs_destination_search(user_input):
            # Get relevant destinations
            destinations = self.rag_cache.search_destinations(
                user_input,
                filters={
                    'budget': context.get('budget'),
                    'region': context.get('region'),
                    'travel_types': context.get('travel_types')
                }
            )
            context['destinations'] = destinations

        # Create optimized prompt
        return self.optimizer.create_dynamic_prompt(context)

    def _analyze_intent(self, user_input: str, history: List) -> Dict:
        """Analyze user intent from message and history"""
        # Import here to avoid circular import
        from destination_data import detect_travel_preferences
        from smart_detection import detect_travel_intentions

        intent = {}

        # Get travel preferences
        prefs = detect_travel_preferences(user_input)
        if prefs:
            intent.update(prefs)

        # Check if complex query
        complex_keywords = ['compare', 'versus', 'which is better', 'recommendation', 'itinerary']
        intent['complex_query'] = any(kw in user_input.lower() for kw in complex_keywords)

        # Get context from history
        if history:
            last_messages = ' '.join([msg.get('content', '') for msg in history[-3:]])
            if 'budget' in last_messages.lower():
                # Extract mentioned budget if available
                import re
                budget_match = re.search(r'(\d+[kjt]?)', last_messages.lower())
                if budget_match:
                    intent['mentioned_budget'] = budget_match.group(1)

        return intent

    def _needs_destination_search(self, user_input: str) -> bool:
        """Check if we need to search for destinations"""
        keywords = [
            'destinasi', 'recommend', 'kemana', 'liburan',
            'wisata', 'tempat', 'visit'
        ]
        return any(kw in user_input.lower() for kw in keywords)

# Singleton instance
prompt_manager = SmartPromptManager()
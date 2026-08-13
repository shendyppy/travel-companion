"""
Knowledge base tool.

Exposed as a tool rather than wired in front of every message on purpose. Always
retrieving would waste latency on "hi" and, worse, drag irrelevant passages into
the context where they can pull the answer off course. The model decides when a
question actually needs the corpus.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from src.providers import knowledge
from src.tools.registry import tool

logger = logging.getLogger(__name__)


@tool(
    name="search_knowledge",
    description=(
        "Search the travel knowledge base: Wikivoyage guides plus curated cost and "
        "seasonal data for Indonesian travellers. Use it for questions about what a "
        "place is like, what to do there, local customs, safety, or realistic costs. "
        "Skip it for greetings, small talk, or anything the other tools already "
        "answer -- flight prices come from search_flights, not from here. "
        "Query in English for the best matches, even when the user wrote in another "
        "language; the corpus is English."
    ),
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": (
                    "What to look for, phrased as a topic rather than a question. "
                    "'street food and night markets' beats 'where should I eat?'."
                ),
            },
            "city": {
                "type": "string",
                "description": (
                    "Restrict to one city, e.g. 'Bali'. Use this whenever the user "
                    "named a place -- semantic search alone will happily return "
                    "passages about similar cities."
                ),
            },
            "topic": {
                "type": "string",
                "enum": [
                    "see", "do", "eat", "drink", "buy", "sleep",
                    "stay safe", "understand", "respect", "budget", "when to go",
                ],
                "description": "Restrict to one kind of section.",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum passages. Defaults to 5.",
                "minimum": 1,
                "maximum": 10,
            },
        },
        "required": ["query"],
    },
)
def search_knowledge(
    query: str,
    city: Optional[str] = None,
    topic: Optional[str] = None,
    limit: int = 5,
) -> dict[str, Any]:
    try:
        passages = knowledge.search(query, city=city, section=topic, limit=limit)
    except knowledge.KnowledgeBaseUnavailable as exc:
        logger.warning("Knowledge base unavailable: %s", exc)
        return {
            "ok": False,
            "error": (
                "The knowledge base is not available. Answer from general knowledge "
                "and say that the details are not verified."
            ),
        }

    if not passages:
        # A filtered-out result is a different problem from an empty corpus, and
        # the model can only recover if it knows which one happened
        hint = "Nothing matched"
        if city:
            hint += f" for city '{city}'"
        if topic:
            hint += f" in section '{topic}'"
        return {
            "ok": True,
            "data": {
                "passages": [],
                "note": f"{hint}. Try a broader query or drop the filters.",
            },
        }

    return {
        "ok": True,
        "data": {
            "query": query,
            "filters": {"city": city, "topic": topic},
            "passages": [p.to_dict() for p in passages],
        },
    }

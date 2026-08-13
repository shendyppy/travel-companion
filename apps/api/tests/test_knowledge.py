"""
Knowledge base tests.

Skipped when the index has not been built, so a fresh clone does not fail before
`python -m scripts.build_index` has run.
"""

import pytest

import src.tools as tools
from src.providers import knowledge
from src.tools.registry import dispatch

pytestmark = pytest.mark.skipif(
    not knowledge.is_available(),
    reason="knowledge index not built (run: python -m scripts.build_index)",
)


class TestIndex:
    def test_index_has_content(self):
        info = knowledge.stats()
        assert info["available"] is True
        assert info["passages"] > 50

    def test_embeddings_are_local(self):
        """
        Retrieval must not depend on an API key. If it did, bring-your-own-key
        would still leave the server paying per query.
        """
        assert "local" in knowledge.stats()["embedding"].lower()


class TestSearch:
    def test_returns_relevant_passages(self):
        hits = knowledge.search("daily budget in rupiah", limit=3)
        assert hits
        assert any("Rp" in h.text for h in hits)

    def test_results_ordered_by_relevance(self):
        hits = knowledge.search("temples", limit=5)
        scores = [h.score for h in hits]
        assert scores == sorted(scores, reverse=True)

    def test_city_filter_is_exact(self):
        """
        Semantic similarity alone leaks: asking about Penang surfaces other
        Malaysian cities because they genuinely are similar. The filter must be
        a hard constraint, not a hint.
        """
        hits = knowledge.search("food", city="Penang", limit=5)
        assert hits
        assert all(h.city == "penang" for h in hits)

    def test_unknown_city_returns_nothing(self):
        assert knowledge.search("food", city="Atlantis") == []

    def test_section_filter(self):
        hits = knowledge.search("crime", section="stay safe", limit=3)
        assert all(h.section == "stay safe" for h in hits)

    def test_passages_carry_provenance(self):
        hits = knowledge.search("things to do", limit=3)
        for hit in hits:
            assert hit.source in {"curated", "wikivoyage"}
            if hit.source == "wikivoyage":
                assert hit.url and hit.url.startswith("https://en.wikivoyage.org/")


class TestToolSchema:
    def test_registered(self):
        assert "search_knowledge" in tools.names()

    def test_topic_enum_covers_wikivoyage_sections(self):
        schema = next(s for s in tools.schemas() if s["function"]["name"] == "search_knowledge")
        assert "stay safe" in schema["function"]["parameters"]["properties"]["topic"]["enum"]


@pytest.mark.asyncio
class TestTool:
    async def test_returns_passages(self):
        result = await dispatch("search_knowledge", '{"query": "street food", "city": "Penang"}')
        assert result["ok"] is True
        assert result["data"]["passages"]

    async def test_empty_filter_explains_itself(self):
        """
        An empty result from a filter is a different problem from an empty
        corpus, and the model can only recover if it can tell them apart.
        """
        result = await dispatch("search_knowledge", '{"query": "x", "city": "Atlantis"}')
        assert result["ok"] is True
        assert "Atlantis" in result["data"]["note"]

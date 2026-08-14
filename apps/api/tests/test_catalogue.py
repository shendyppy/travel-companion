"""
Catalogue tests.

Mostly guards against drift. The frontend builds its inspiration grid and budget
picker from these vocabularies, so an enum member added without a label should
fail here rather than render as a blank chip in production.

The last test is the important one: it feeds every facet value the catalogue
serves back into the tool that consumes it. The grid seeds
`recommend_destinations` with these strings verbatim, so if the vocabularies and
the tool schema ever disagree, every tile on the page breaks at once.
"""

import pytest

from src import catalogue
from src.providers.destination_data import BudgetCategory, Season, TravelType


class TestDestinations:
    def test_serves_the_curated_set(self):
        entries = catalogue.destinations()
        assert len(entries) == 15
        assert {e["name"] for e in entries} >= {"Yogyakarta", "Tokyo", "Chiang Mai"}

    def test_every_entry_carries_an_iata_field(self):
        """
        It may be None -- not every curated place resolves to an airport -- but
        the key has to exist, because the deals rail branches on it.
        """
        for entry in catalogue.destinations():
            assert "iata" in entry, f"{entry['name']} has no iata key"

    def test_entries_carry_costs_in_rupiah(self):
        for entry in catalogue.destinations():
            assert entry["estimated_daily_cost_idr"], f"{entry['name']} has no cost breakdown"
            assert entry["estimated_daily_total_idr"] > 0


class TestFacets:
    def test_every_travel_type_has_a_label(self):
        values = {f["value"] for f in catalogue.facets()["travel_types"]}
        assert values == {t.value for t in TravelType}

    def test_every_season_has_a_label(self):
        values = {f["value"] for f in catalogue.facets()["seasons"]}
        assert values == {s.value for s in Season}

    def test_every_budget_band_has_a_label_and_bounds(self):
        bands = catalogue.facets()["budget_bands"]
        assert {b["value"] for b in bands} == {b.value for b in BudgetCategory}
        for band in bands:
            assert band["label"] and band["range_label"]
            assert band["min_idr"] is not None or band["max_idr"] is not None

    def test_budget_bands_are_contiguous(self):
        """A gap between bands is a budget nobody can pick."""
        bands = catalogue.facets()["budget_bands"]
        ordered = sorted(bands, key=lambda b: b["min_idr"] or 0)
        for lower, upper in zip(ordered, ordered[1:]):
            assert lower["max_idr"] == upper["min_idr"]

    def test_range_labels_are_short_enough_for_a_chip(self):
        for band in catalogue.facets()["budget_bands"]:
            assert len(band["range_label"]) <= 12, band["range_label"]

    def test_facet_values_are_accepted_by_the_tool_that_consumes_them(self):
        from src.agent import seed as seeding

        facets = catalogue.facets()
        for band in facets["budget_bands"]:
            _, error = seeding.parse("recommend_destinations", {"budget": band["value"]})
            assert error is None, f"budget {band['value']}: {error}"
        for travel_type in facets["travel_types"]:
            _, error = seeding.parse(
                "recommend_destinations", {"travel_types": [travel_type["value"]]}
            )
            assert error is None, f"travel type {travel_type['value']}: {error}"
        for season in facets["seasons"]:
            _, error = seeding.parse("recommend_destinations", {"season": season["value"]})
            assert error is None, f"season {season['value']}: {error}"
        for region in facets["regions"]:
            _, error = seeding.parse("recommend_destinations", {"region": region["value"]})
            assert error is None, f"region {region['value']}: {error}"


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from src.api import app

    return TestClient(app)


class TestEndpoint:
    def test_destinations_endpoint_shape(self, client):
        body = client.get("/api/destinations").json()
        assert len(body["destinations"]) == 15
        assert set(body["facets"]) == {"travel_types", "budget_bands", "seasons", "regions"}

"""
Deals cache tests.

Two properties keep the fare rail honest, and both are asserted here rather than
left to code review:

1. A cold miss produces no price. Not an estimate, not a placeholder.
2. A request never reaches a flight provider. Otherwise a public GET is a 15x
   amplifier for anyone with curl.

`tools.dispatch` is stubbed throughout, so nothing here touches the network.
"""

import pytest
import pytest_asyncio

from src import deals
from src.session_store import get_session_store


def fake_flight(price):
    return {"ok": True, "data": {"cheapest": {"price": price, "airline": "Test Air", "stops": 0}}}


@pytest_asyncio.fixture
async def clean_cache():
    await get_session_store().clear_all()
    yield
    await get_session_store().clear_all()


class TestOriginClamping:
    def test_unknown_origin_falls_back_to_jakarta(self):
        assert deals.normalise_origin("XXX") == deals.DEFAULT_ORIGIN

    def test_known_origin_is_kept(self):
        assert deals.normalise_origin("dps") == "DPS"

    def test_missing_origin_falls_back(self):
        assert deals.normalise_origin(None) == deals.DEFAULT_ORIGIN
        assert deals.normalise_origin("  ") == deals.DEFAULT_ORIGIN


@pytest.mark.asyncio
class TestColdCache:
    async def test_cold_miss_returns_no_prices(self, clean_cache):
        """
        The rule the whole module exists to enforce: no cached fares means no
        fares, not an estimate.
        """
        payload = await deals.get("CGK")
        assert payload["deals"] == []
        assert payload["updated_at"] is None

    async def test_request_never_calls_a_provider(self, clean_cache, monkeypatch):
        """A public GET that fans out to 15 provider calls is an amplifier."""
        called = []

        async def spy(name, args):
            called.append(name)
            return fake_flight(1_000_000)

        monkeypatch.setattr(deals.tools, "dispatch", spy)
        await deals.get("CGK")
        assert called == []


@pytest.mark.asyncio
class TestRefresh:
    async def test_prices_and_caches(self, clean_cache, monkeypatch):
        prices = iter(range(3_000_000, 0, -100_000))

        async def stub(name, args):
            assert name == "search_flights"
            return fake_flight(next(prices))

        monkeypatch.setattr(deals.tools, "dispatch", stub)
        payload = await deals.refresh("CGK")

        assert payload["deals"]
        assert payload["updated_at"]
        assert payload["departure_date"]

        cached = await deals.get("CGK")
        assert len(cached["deals"]) == len(payload["deals"])

    async def test_deals_are_cheapest_first(self, clean_cache, monkeypatch):
        prices = iter([2_500_000, 800_000, 1_400_000] * 10)

        async def stub(name, args):
            return fake_flight(next(prices))

        monkeypatch.setattr(deals.tools, "dispatch", stub)
        payload = await deals.refresh("CGK")
        amounts = [d["price_idr"] for d in payload["deals"]]
        assert amounts == sorted(amounts)

    async def test_a_route_with_no_fare_is_dropped_not_faked(self, clean_cache, monkeypatch):
        async def stub(name, args):
            if args["destination"] == "DPS":
                return fake_flight(900_000)
            return {"ok": False, "error": "No flights found."}

        monkeypatch.setattr(deals.tools, "dispatch", stub)
        payload = await deals.refresh("CGK")
        assert all(d["price_idr"] > 0 for d in payload["deals"])
        assert len(payload["deals"]) <= 1

    async def test_a_total_provider_outage_leaves_the_cache_alone(self, clean_cache, monkeypatch):
        """
        Caching an empty rail would pin the fallback in place for twelve hours
        over what is usually a blip.
        """
        good = iter([fake_flight(1_000_000)] * 50)

        async def working(name, args):
            return next(good)

        monkeypatch.setattr(deals.tools, "dispatch", working)
        await deals.refresh("CGK")
        warm = await deals.get("CGK")
        assert warm["deals"]

        async def broken(name, args):
            return {"ok": False, "error": "provider down"}

        monkeypatch.setattr(deals.tools, "dispatch", broken)
        await deals.refresh("CGK")

        still_warm = await deals.get("CGK")
        assert still_warm["deals"] == warm["deals"]

    async def test_origin_is_never_its_own_destination(self, clean_cache, monkeypatch):
        seen = []

        async def stub(name, args):
            seen.append(args["destination"])
            return fake_flight(1_000_000)

        monkeypatch.setattr(deals.tools, "dispatch", stub)
        await deals.refresh("DPS")
        assert "DPS" not in seen


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from src.api import app

    return TestClient(app)


class TestEndpoint:
    def test_deals_endpoint_is_empty_when_cold(self, client):
        body = client.get("/api/deals").json()
        assert body["deals"] == []
        assert body["updated_at"] is None
        assert body["origin"] == deals.DEFAULT_ORIGIN

    def test_deals_endpoint_reports_the_origin_it_actually_served(self, client):
        """
        Clamping silently would mislabel the rail: a Medan visitor would be shown
        Jakarta fares under a Medan heading.
        """
        body = client.get("/api/deals", params={"origin": "LHR"}).json()
        assert body["requested_origin"] == "LHR"
        assert body["origin"] == deals.DEFAULT_ORIGIN

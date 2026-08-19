"""
Flight results tests.

Three properties matter here, and each one is a thing that would cost money or
lie to a user if it broke:

1. **The tool's eight-result cap does not leak into the page.** That cap is a
   token budget for the model; a results page inheriting it would silently hide
   flights that exist.
2. **A cached answer spends no provider allowance**, and a provider failure is
   never cached -- otherwise one timeout becomes a fifteen-minute outage.
3. **Facets agree with the flights they describe.** A filter that offers an
   airline the list does not contain is a control that does not work.

`search_and_normalize` is stubbed throughout, so nothing here touches a network.
"""

import pytest
import pytest_asyncio

from src import access, flight_results
from src.session_store import get_session_store
from src.tools.flights import FlightSearch, _duration_minutes


def flight(price, *, code="GA", airline="Garuda", hour=8, stops=0, minutes=110):
    return {
        "airline": airline,
        "airline_code": code,
        "departure_time": f"2026-09-20T{hour:02d}:10:00",
        "arrival_time": f"2026-09-20T{hour + 2:02d}:00:00",
        "origin": "CGK",
        "destination": "DPS",
        "price": price,
        "currency": "IDR",
        "duration": "1h 50m",
        "duration_minutes": minutes,
        "stops": stops,
    }


def stub_search(flights, *, ok=True, error=None):
    """A stand-in for the blocking provider call, recording how often it ran."""
    calls = []

    def run(origin, destination, departure_date, return_date=None, adults=1):
        calls.append((origin, destination, departure_date, return_date, adults))
        if not ok:
            return FlightSearch(ok=False, error=error or "provider down")
        return FlightSearch(ok=True, flights=list(flights), origin="CGK", destination="DPS")

    run.calls = calls
    return run


@pytest_asyncio.fixture(autouse=True)
async def clean_state():
    """
    Fares and rate-limit counters both outlive a single test by design, so every
    case starts from cold. Without this a cached result from an earlier test
    satisfies a later one for free -- which is exactly how the endpoint tests
    first passed while asserting nothing.
    """
    await get_session_store().clear_all()
    access._memory._counts.clear()
    yield
    await get_session_store().clear_all()
    access._memory._counts.clear()


class TestDurationParsing:
    """
    Both providers describe duration differently and the page sorts on it, so a
    silent None here would quietly drop flights out of a "tercepat" sort.
    """

    def test_iso_and_human_forms_agree(self):
        assert _duration_minutes("PT1H50M") == _duration_minutes("1h 50m") == 110

    def test_days_survive_the_iso_split(self):
        # P1DT2H30M is a day plus two and a half hours. Scanning past the T and
        # forgetting the day would give 150 minutes instead of 1590.
        assert _duration_minutes("P1DT2H30M") == 1590

    def test_unparseable_is_none_not_zero(self):
        # None and 0 must not collapse: a missing duration sorts differently from
        # an instantaneous flight.
        assert _duration_minutes("N/A") is None
        assert _duration_minutes("") is None


class TestFacets:
    def test_airlines_are_counted_and_priced(self):
        facets = flight_results.build_facets([
            flight(1_000_000, code="GA", airline="Garuda"),
            flight(1_500_000, code="GA", airline="Garuda"),
            flight(800_000, code="QG", airline="Citilink"),
        ])
        garuda = next(a for a in facets["airlines"] if a["code"] == "GA")
        assert garuda["count"] == 2
        assert garuda["min_price"] == 1_000_000

    def test_busiest_airline_comes_first(self):
        facets = flight_results.build_facets([
            flight(900_000, code="QG"),
            flight(1_000_000, code="GA"),
            flight(1_100_000, code="GA"),
        ])
        assert facets["airlines"][0]["code"] == "GA"

    def test_only_present_values_get_a_facet(self):
        """A filter that matches nothing is a control that does not work."""
        facets = flight_results.build_facets([flight(1_000_000, stops=0, hour=8)])
        assert [s["value"] for s in facets["stops"]] == [0]
        assert [b["value"] for b in facets["departure_buckets"]] == ["pagi"]

    def test_departure_buckets_follow_indonesian_time_of_day(self):
        facets = flight_results.build_facets([
            flight(1, hour=6),   # pagi
            flight(2, hour=13),  # siang
            flight(3, hour=17),  # sore
            flight(4, hour=22),  # malam
            flight(5, hour=2),   # malam, wrapped past midnight
        ])
        counts = {b["value"]: b["count"] for b in facets["departure_buckets"]}
        assert counts == {"pagi": 1, "siang": 1, "sore": 1, "malam": 2}
        # Fixed order, so the rail does not reshuffle between searches.
        assert [b["value"] for b in facets["departure_buckets"]] == [
            "pagi", "siang", "sore", "malam",
        ]

    def test_price_and_duration_ranges_span_the_set(self):
        facets = flight_results.build_facets([
            flight(2_000_000, minutes=200),
            flight(750_000, minutes=95),
        ])
        assert facets["price"] == {"min": 750_000, "max": 2_000_000}
        assert facets["duration"] == {"min_minutes": 95, "max_minutes": 200}

    def test_empty_result_has_no_ranges(self):
        facets = flight_results.build_facets([])
        assert facets["price"] is None
        assert facets["duration"] is None
        assert facets["airlines"] == []


@pytest.mark.asyncio
class TestSearch:
    async def test_returns_every_flight_not_just_the_tool_cap(self, monkeypatch):
        """
        The reason this module exists. MAX_RESULTS is a token budget for the
        model; inheriting it here would hide flights that exist.
        """
        many = [flight(1_000_000 + i) for i in range(20)]
        monkeypatch.setattr(flight_results, "search_and_normalize", stub_search(many))

        result = await flight_results.search("CGK", "DPS", "2026-09-20")

        assert result["ok"]
        assert result["total_found"] == 20
        assert len(result["flights"]) == 20

    async def test_facets_describe_the_flights_returned(self, monkeypatch):
        monkeypatch.setattr(
            flight_results,
            "search_and_normalize",
            stub_search([flight(1_000_000, code="GA"), flight(800_000, code="QG")]),
        )
        result = await flight_results.search("CGK", "DPS", "2026-09-20")

        listed = {f["airline_code"] for f in result["flights"]}
        offered = {a["code"] for a in result["facets"]["airlines"]}
        assert listed == offered

    async def test_second_call_is_served_from_cache(self, monkeypatch):
        run = stub_search([flight(1_000_000)])
        monkeypatch.setattr(flight_results, "search_and_normalize", run)

        first = await flight_results.search("CGK", "DPS", "2026-09-20")
        second = await flight_results.search("CGK", "DPS", "2026-09-20")

        assert len(run.calls) == 1
        assert first["cached"] is False
        assert second["cached"] is True
        # The timestamp is the fare's age, not the request's -- it must not move
        # on a cache hit, or the page would claim fresh prices it did not fetch.
        assert second["cached_at"] == first["cached_at"]

    async def test_a_different_date_is_a_different_entry(self, monkeypatch):
        run = stub_search([flight(1_000_000)])
        monkeypatch.setattr(flight_results, "search_and_normalize", run)

        await flight_results.search("CGK", "DPS", "2026-09-20")
        await flight_results.search("CGK", "DPS", "2026-09-21")

        assert len(run.calls) == 2

    async def test_provider_failure_is_reported_and_not_cached(self, monkeypatch):
        """Caching a timeout turns a blip into a fifteen-minute outage."""
        broken = stub_search([], ok=False, error="Amadeus timed out")
        monkeypatch.setattr(flight_results, "search_and_normalize", broken)

        first = await flight_results.search("CGK", "DPS", "2026-09-20")
        assert first["ok"] is False
        assert "timed out" in first["error"]

        working = stub_search([flight(1_000_000)])
        monkeypatch.setattr(flight_results, "search_and_normalize", working)
        second = await flight_results.search("CGK", "DPS", "2026-09-20")

        assert second["ok"] is True
        assert len(working.calls) == 1

    async def test_an_empty_route_is_cached(self, monkeypatch):
        """
        Unlike deals.py, empty here is an answer rather than an outage: the
        provider said clearly that nobody flies this on this date, and asking
        again in a minute will not change that.
        """
        run = stub_search([])
        monkeypatch.setattr(flight_results, "search_and_normalize", run)

        await flight_results.search("CGK", "DPS", "2026-09-20")
        second = await flight_results.search("CGK", "DPS", "2026-09-20")

        assert len(run.calls) == 1
        assert second["cached"] is True
        assert second["total_found"] == 0

    async def test_a_provider_answering_the_wrong_date_is_reported(self, monkeypatch):
        """
        The RapidAPI Google Flights upstream has been seen returning today's
        schedule for a request weeks out -- `outboundDate` goes out correctly and
        comes back ignored. Those fares are real but they are for another day, and
        showing them under the requested date is the one thing this product
        promises not to do.
        """
        wrong_day = flight(1_000_000)
        wrong_day["departure_time"] = "2026-08-18T13:40:00"
        monkeypatch.setattr(flight_results, "search_and_normalize", stub_search([wrong_day]))

        result = await flight_results.search("CGK", "DPS", "2026-09-20")

        assert result["dates_returned"] == ["2026-08-18"]

    async def test_the_expected_date_raises_no_alarm(self, monkeypatch):
        on_time = flight(1_000_000)
        on_time["departure_time"] = "2026-09-20T06:10:00"
        monkeypatch.setattr(flight_results, "search_and_normalize", stub_search([on_time]))

        result = await flight_results.search("CGK", "DPS", "2026-09-20")

        assert result["dates_returned"] == []

    async def test_booking_links_are_generated_even_with_no_fares(self, monkeypatch):
        """The product does not sell seats, so the handoff is the whole point."""
        monkeypatch.setattr(flight_results, "search_and_normalize", stub_search([]))
        result = await flight_results.search("CGK", "DPS", "2026-09-20")

        assert set(result["booking_links"]) == {"traveloka", "tiketcom", "skyscanner"}
        assert "CGK" in result["booking_links"]["traveloka"]


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from src.api import app

    return TestClient(app)


class TestEndpoint:
    def test_returns_the_full_set_with_facets(self, client, monkeypatch):
        monkeypatch.setattr(
            flight_results,
            "search_and_normalize",
            stub_search([flight(1_000_000 + i * 10_000) for i in range(12)]),
        )
        body = client.get(
            "/api/flights/search",
            params={"origin": "Jakarta", "destination": "Bali", "departure_date": "2026-09-20"},
        ).json()

        assert body["total_found"] == 12
        assert len(body["flights"]) == 12
        assert body["facets"]["price"]["min"] == 1_000_000
        assert body["origin"] == "CGK"

    def test_provider_failure_is_a_502_not_a_500(self, client, monkeypatch):
        """Upstream is at fault; a 500 would read as a bug in this service."""
        monkeypatch.setattr(
            flight_results, "search_and_normalize", stub_search([], ok=False, error="no route")
        )
        response = client.get(
            "/api/flights/search",
            params={"origin": "Jakarta", "destination": "Bali", "departure_date": "2026-09-20"},
        )
        assert response.status_code == 502
        assert response.json()["error"] == "no route"

    def test_absurd_passenger_count_is_refused(self, client):
        response = client.get(
            "/api/flights/search",
            params={
                "origin": "Jakarta",
                "destination": "Bali",
                "departure_date": "2026-09-20",
                "adults": 40,
            },
        )
        assert response.status_code == 422

    def test_provider_calls_are_rate_limited(self, client, monkeypatch):
        """
        This endpoint reaches a paid provider without an LLM turn in front of it,
        so the demo quota does not bound it at all.
        """
        monkeypatch.setattr(access, "PROVIDER_HOURLY_LIMIT", 3)

        def run(origin, destination, departure_date, return_date=None, adults=1):
            return FlightSearch(ok=True, flights=[flight(1_000_000)], origin="CGK", destination="DPS")

        monkeypatch.setattr(flight_results, "search_and_normalize", run)

        # A distinct date each time, so every call is a genuine cache miss.
        codes = [
            client.get(
                "/api/flights/search",
                params={
                    "origin": "Jakarta",
                    "destination": "Bali",
                    "departure_date": f"2026-09-{20 + i}",
                },
            ).status_code
            for i in range(5)
        ]

        assert codes[:3] == [200, 200, 200]
        assert codes[3:] == [429, 429]

    def test_a_cached_answer_spends_no_allowance(self, client, monkeypatch):
        """Filtering and going back should not burn a visitor's quota."""
        monkeypatch.setattr(access, "PROVIDER_HOURLY_LIMIT", 2)
        monkeypatch.setattr(
            flight_results, "search_and_normalize", stub_search([flight(1_000_000)])
        )
        params = {
            "origin": "Jakarta",
            "destination": "Bali",
            "departure_date": "2026-11-02",
        }

        codes = [client.get("/api/flights/search", params=params).status_code for _ in range(5)]

        assert codes == [200] * 5

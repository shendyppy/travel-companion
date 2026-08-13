"""
Tool registry tests.

The contract that matters most: dispatch never raises. A tool that explodes and
kills the conversation is worse than one that reports a failure the model can
read and work around.
"""

import pytest

import src.tools as tools
from src.tools.registry import dispatch, names, schemas


class TestRegistration:
    def test_expected_tools_registered(self):
        registered = set(names())
        assert {
            "lookup_place",
            "resolve_dates",
            "search_flights",
            "search_flights_flexible",
            "recommend_destinations",
            "get_destination_info",
        } <= registered

    def test_schemas_are_well_formed(self):
        for schema in schemas():
            assert schema["type"] == "function"
            fn = schema["function"]
            assert fn["name"]
            # Providers use the description to decide when to call a tool, so an
            # empty or throwaway one is a real defect
            assert len(fn["description"]) > 40
            assert fn["parameters"]["type"] == "object"
            for prop in fn["parameters"]["properties"].values():
                assert prop.get("description"), "every parameter needs a description"

    def test_required_params_exist_in_properties(self):
        for schema in schemas():
            params = schema["function"]["parameters"]
            for required in params.get("required", []):
                assert required in params["properties"]


@pytest.mark.asyncio
class TestDispatchNeverRaises:
    async def test_unknown_tool(self):
        result = await dispatch("no_such_tool", "{}")
        assert result["ok"] is False
        assert "available" in result

    async def test_malformed_json(self):
        result = await dispatch("lookup_place", "{not valid json")
        assert result["ok"] is False
        assert "JSON" in result["error"]

    async def test_wrong_argument_name(self):
        result = await dispatch("lookup_place", '{"wrong_name": 1}')
        assert result["ok"] is False

    async def test_json_that_is_not_an_object(self):
        result = await dispatch("lookup_place", '["a", "list"]')
        assert result["ok"] is False

    async def test_empty_arguments(self):
        # recommend_destinations takes no required parameters
        result = await dispatch("recommend_destinations", "")
        assert result["ok"] is True

    async def test_accepts_pre_parsed_dict(self):
        result = await dispatch("lookup_place", {"query": "Bali"})
        assert result["ok"] is True


@pytest.mark.asyncio
class TestToolBehaviour:
    async def test_lookup_place_returns_primary_first(self):
        result = await dispatch("lookup_place", '{"query": "Jakarta"}')
        assert result["data"]["places"][0]["iata"] == "CGK"

    async def test_lookup_place_unknown_reports_failure(self):
        result = await dispatch("lookup_place", '{"query": "zzzzz nowhere"}')
        assert result["ok"] is False

    async def test_invalid_enum_lists_valid_options(self):
        result = await dispatch("recommend_destinations", '{"budget": "very_cheap"}')
        assert result["ok"] is False
        # The message has to teach the model how to retry
        assert "budget" in result["error"]

    async def test_recommend_respects_max_results(self):
        result = await dispatch("recommend_destinations", '{"max_results": 2}')
        assert len(result["data"]["destinations"]) <= 2

    async def test_get_destination_info_admits_missing_data(self):
        """
        Returning ok:true with only an airport code would make the model believe
        it has data and stop looking.
        """
        result = await dispatch("get_destination_info", '{"city": "Bali"}')
        if result["ok"]:
            assert {"destination", "season", "cheapest_months"} & result["data"].keys()
        else:
            assert "Bali" in result["error"]

    async def test_flight_search_rejects_identical_endpoints(self):
        result = await dispatch(
            "search_flights",
            '{"origin": "Jakarta", "destination": "CGK", "departure_date": "2026-12-01"}',
        )
        assert result["ok"] is False
        assert "same airport" in result["error"]

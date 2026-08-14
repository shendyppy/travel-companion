"""
Seeded tool call tests.

`seed` is the only place where something outside the process picks which internal
function runs, so the rejection cases matter more here than the happy path. They
are asserted directly rather than through the endpoint: a hole in `parse` is not
the kind of thing an integration test notices.

Tools used in the loop tests are the ones backed by local data
(`recommend_destinations`, `get_destination_info`), so nothing here touches the
network.
"""

import pytest

from src import tools
from src.agent import loop, seed as seeding
from src.llm.client import StreamChunk

VALID_FLIGHT_ARGS = {
    "origin": "CGK",
    "destination": "DPS",
    "departure_date": "2026-09-20",
    "adults": 1,
}


class FakeLLM:
    """Records what the loop sent, and replies with scripted chunks."""

    def __init__(self, *scripted):
        self.scripted = list(scripted)
        self.calls: list[list[dict]] = []

    def __call__(self, messages, *, tools=None, api_key=None, **kwargs):
        self.calls.append(list(messages))
        chunks = self.scripted.pop(0) if self.scripted else [StreamChunk(tool_calls=[])]

        async def stream():
            for chunk in chunks:
                yield chunk

        return stream()


async def drain(message, monkeypatch, fake, *, seed=None, history=None):
    monkeypatch.setattr(loop.client, "stream_completion", fake)
    events, turn = [], None
    async for item in loop.run(history or [], message, seed=seed):
        if isinstance(item, loop.Turn):
            turn = item
        else:
            events.append(item)
    return events, turn


# ==============================================================================
# The gate
# ==============================================================================


class TestAllowlist:
    def test_accepts_a_seedable_tool(self):
        seed, error = seeding.parse("search_flights", VALID_FLIGHT_ARGS)
        assert error is None
        assert seed.tool == "search_flights"
        assert seed.arguments == VALID_FLIGHT_ARGS

    def test_rejects_a_registered_but_non_seedable_tool(self):
        """
        `lookup_place` exists and would run happily. It is still refused: the
        allowlist is about what a client may reach, not about what works.
        """
        assert tools.exists("lookup_place")
        seed, error = seeding.parse("lookup_place", {"query": "Bali"})
        assert seed is None
        assert "cannot be seeded" in error

    def test_rejects_an_unknown_tool(self):
        seed, error = seeding.parse("rm_rf_slash", {})
        assert seed is None
        assert "cannot be seeded" in error

    def test_rejection_does_not_reveal_the_tool_list(self):
        """The set of tools that exist is not a client's business."""
        _, unknown = seeding.parse("no_such_tool", {})
        _, existing = seeding.parse("lookup_place", {"query": "Bali"})
        assert "lookup_place" not in unknown
        for name in tools.names():
            assert name not in existing.replace("lookup_place", "")

    def test_every_seedable_tool_actually_exists(self):
        """Guards against a rename leaving a dead entry in the allowlist."""
        for name in seeding.SEEDABLE:
            assert tools.exists(name), f"{name} is seedable but not registered"

    def test_seed_arguments_are_copied(self):
        """A caller mutating its dict afterwards must not change what runs."""
        args = dict(VALID_FLIGHT_ARGS)
        seed, _ = seeding.parse("search_flights", args)
        args["destination"] = "SIN"
        assert seed.arguments["destination"] == "DPS"


class TestArgumentValidation:
    def test_rejects_missing_required_argument(self):
        seed, error = seeding.parse("search_flights", {"origin": "CGK"})
        assert seed is None
        assert "destination" in error or "required" in error

    def test_rejects_unknown_property(self):
        """
        `dispatch` is forgiving with the model; `validate` is not forgiving with
        a client. An argument we do not recognise is a frontend bug or a probe.
        """
        seed, error = seeding.parse(
            "search_flights", {**VALID_FLIGHT_ARGS, "callback_url": "http://evil"}
        )
        assert seed is None
        assert error

    def test_rejects_wrong_type(self):
        seed, error = seeding.parse("search_flights", {**VALID_FLIGHT_ARGS, "adults": "dua"})
        assert seed is None
        assert error

    def test_rejects_out_of_range_value(self):
        seed, error = seeding.parse("search_flights", {**VALID_FLIGHT_ARGS, "adults": 99})
        assert seed is None
        assert error

    def test_rejects_value_outside_an_enum(self):
        seed, error = seeding.parse("recommend_destinations", {"budget": "gratis"})
        assert seed is None
        assert error

    def test_accepts_a_tool_with_no_required_arguments(self):
        seed, error = seeding.parse("recommend_destinations", {})
        assert error is None
        assert seed.arguments == {}

    def test_missing_arguments_default_to_empty(self):
        seed, error = seeding.parse("recommend_destinations", None)
        assert error is None
        assert seed.arguments == {}

    def test_rejects_non_object_arguments(self):
        seed, error = seeding.parse("recommend_destinations", ["budget"])
        assert seed is None
        assert "object" in error

    def test_rejects_a_non_string_tool_name(self):
        seed, error = seeding.parse(None, {})
        assert seed is None
        assert error


# ==============================================================================
# The loop
# ==============================================================================


@pytest.mark.asyncio
class TestSeededTurn:
    async def test_seed_runs_before_the_model(self, monkeypatch):
        fake = FakeLLM([StreamChunk(text="Nih rekomendasinya."), StreamChunk(tool_calls=[])])
        seed, _ = seeding.parse("recommend_destinations", {"budget": "budget"})
        events, turn = await drain("kasih ide dong", monkeypatch, fake, seed=seed)

        # The tool is announced before a single token of text
        types = [e.type for e in events]
        assert types.index("tool_start") < types.index("text_delta")
        assert types.index("tool_result") < types.index("text_delta")

        start = next(e for e in events if e.type == "tool_start")
        assert start.tool == "recommend_destinations"
        assert start.arguments == {"budget": "budget"}
        assert turn.tools_used == ["recommend_destinations"]

    async def test_model_sees_the_seed_as_its_own_call(self, monkeypatch):
        """
        The whole point: no special case downstream. The transcript has to look
        exactly like a tool call the model made itself, or providers reject it
        and follow-up turns get confused.
        """
        fake = FakeLLM([StreamChunk(text="ok"), StreamChunk(tool_calls=[])])
        seed, _ = seeding.parse("recommend_destinations", {"region": "domestic"})
        await drain("ide dong", monkeypatch, fake, seed=seed)

        sent = fake.calls[0]
        assert sent[0]["role"] == "system"
        assert sent[-3] == {"role": "user", "content": "ide dong"}

        assistant = sent[-2]
        assert assistant["role"] == "assistant"
        call = assistant["tool_calls"][0]
        assert call["function"]["name"] == "recommend_destinations"

        result = sent[-1]
        assert result["role"] == "tool"
        assert result["tool_call_id"] == call["id"], "tool result must attach to its call"
        assert "destinations" in result["content"]

    async def test_seeded_failure_still_completes_the_turn(self, monkeypatch):
        """
        A seed whose tool finds nothing is not a broken request. The model gets
        the failure and explains it, exactly as when it picks the tool itself.
        """
        fake = FakeLLM([StreamChunk(text="Maaf, datanya nggak ada."), StreamChunk(tool_calls=[])])
        seed, _ = seeding.parse("get_destination_info", {"city": "Atlantis"})
        events, turn = await drain("Atlantis gimana?", monkeypatch, fake, seed=seed)

        result = next(e for e in events if e.type == "tool_result")
        assert result.result["ok"] is False
        assert turn is not None
        assert turn.text == "Maaf, datanya nggak ada."

    async def test_model_may_still_call_more_tools_after_a_seed(self, monkeypatch):
        from src.llm.client import ToolCall

        fake = FakeLLM(
            [StreamChunk(tool_calls=[ToolCall(id="c1", name="lookup_place", arguments='{"query":"Bali"}')])],
            [StreamChunk(text="DPS."), StreamChunk(tool_calls=[])],
        )
        seed, _ = seeding.parse("recommend_destinations", {})
        _, turn = await drain("ide dong, terus kode Bali apa?", monkeypatch, fake, seed=seed)
        assert turn.tools_used == ["recommend_destinations", "lookup_place"]

    async def test_no_seed_is_the_untouched_path(self, monkeypatch):
        fake = FakeLLM([StreamChunk(text="halo"), StreamChunk(tool_calls=[])])
        events, turn = await drain("halo", monkeypatch, fake)
        assert [e.type for e in events] == ["text_delta", "done"]
        assert turn.tools_used == []

    async def test_seed_is_not_persisted_into_history(self, monkeypatch):
        """
        Stored history stays user/assistant only, same as for model-chosen tools.
        Tool payloads are large and go stale; the assistant's narration is what
        the next turn actually needs.
        """
        fake = FakeLLM([StreamChunk(text="Yogyakarta, Lombok, Belitung."), StreamChunk(tool_calls=[])])
        seed, _ = seeding.parse("recommend_destinations", {"budget": "budget"})
        _, turn = await drain("ide dong", monkeypatch, fake, seed=seed)

        assert [m["role"] for m in turn.messages] == ["user", "assistant"]

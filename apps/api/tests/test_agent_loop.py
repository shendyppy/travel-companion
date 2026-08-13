"""
Agent loop tests, with the LLM stubbed out.

These cover the mechanics the old implementation got wrong: passing full history
on every call, feeding tool results back, and failing loudly instead of quietly.
"""

from datetime import date

import pytest

from src.agent import loop, persona
from src.llm.client import StreamChunk, ToolCall


class FakeLLM:
    """
    Stand-in for client.stream_completion.

    Records every call so tests can assert on what the loop actually sent -- the
    old wrapper dropped conversation history, and nothing caught it.
    """

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


async def drain(history, message, monkeypatch, fake):
    monkeypatch.setattr(loop.client, "stream_completion", fake)
    events, turn = [], None
    async for item in loop.run(history, message):
        if isinstance(item, loop.Turn):
            turn = item
        else:
            events.append(item)
    return events, turn


@pytest.mark.asyncio
class TestPlainReply:
    async def test_streams_text_and_finishes(self, monkeypatch):
        fake = FakeLLM([
            StreamChunk(text="Hai "),
            StreamChunk(text="apa kabar?"),
            StreamChunk(tool_calls=[], finish_reason="stop"),
        ])
        events, turn = await drain([], "halo", monkeypatch, fake)

        deltas = [e.text for e in events if e.type == "text_delta"]
        assert deltas == ["Hai ", "apa kabar?"]
        assert turn.text == "Hai apa kabar?"
        assert turn.tools_used == []

    async def test_turn_carries_messages_to_persist(self, monkeypatch):
        fake = FakeLLM([StreamChunk(text="ok"), StreamChunk(tool_calls=[])])
        _, turn = await drain([], "halo", monkeypatch, fake)

        assert turn.messages == [
            {"role": "user", "content": "halo"},
            {"role": "assistant", "content": "ok"},
        ]


@pytest.mark.asyncio
class TestHistory:
    async def test_full_history_is_sent(self, monkeypatch):
        """
        The bug this guards: the old Gemini adapter accepted a `history`
        argument and never used it, so the agent forgot everything each turn.
        """
        history = [
            {"role": "user", "content": "aku mau ke Lombok"},
            {"role": "assistant", "content": "Lombok pilihan bagus!"},
        ]
        fake = FakeLLM([StreamChunk(text="Nusa Tenggara Barat"), StreamChunk(tool_calls=[])])
        await drain(history, "itu di provinsi mana?", monkeypatch, fake)

        sent = fake.calls[0]
        assert sent[0]["role"] == "system"
        assert sent[1:3] == history
        assert sent[-1] == {"role": "user", "content": "itu di provinsi mana?"}

    async def test_system_prompt_carries_today(self, monkeypatch):
        fake = FakeLLM([StreamChunk(text="ok"), StreamChunk(tool_calls=[])])
        await drain([], "halo", monkeypatch, fake)
        assert date.today().isoformat() in fake.calls[0][0]["content"]


@pytest.mark.asyncio
class TestToolCalling:
    async def test_tool_result_is_fed_back(self, monkeypatch):
        fake = FakeLLM(
            [StreamChunk(tool_calls=[ToolCall(id="c1", name="lookup_place", arguments='{"query":"Bali"}')])],
            [StreamChunk(text="Bali itu DPS."), StreamChunk(tool_calls=[])],
        )
        events, turn = await drain([], "kode bandara Bali apa?", monkeypatch, fake)

        starts = [e for e in events if e.type == "tool_start"]
        results = [e for e in events if e.type == "tool_result"]
        assert starts[0].tool == "lookup_place"
        assert starts[0].arguments == {"query": "Bali"}
        assert results[0].result["ok"] is True

        # Second call must include the assistant tool_calls message and the
        # matching tool response, or providers reject the payload
        second = fake.calls[1]
        assert second[-2]["role"] == "assistant"
        assert second[-2]["tool_calls"][0]["function"]["name"] == "lookup_place"
        assert second[-1]["role"] == "tool"
        assert second[-1]["tool_call_id"] == "c1"
        assert turn.tools_used == ["lookup_place"]

    async def test_parallel_tool_calls(self, monkeypatch):
        fake = FakeLLM(
            [StreamChunk(tool_calls=[
                ToolCall(id="a", name="lookup_place", arguments='{"query":"Bali"}'),
                ToolCall(id="b", name="lookup_place", arguments='{"query":"Jakarta"}'),
            ])],
            [StreamChunk(text="DPS dan CGK."), StreamChunk(tool_calls=[])],
        )
        events, turn = await drain([], "Bali sama Jakarta kodenya apa?", monkeypatch, fake)
        assert len([e for e in events if e.type == "tool_result"]) == 2
        assert turn.tools_used == ["lookup_place", "lookup_place"]

    async def test_failing_tool_does_not_kill_the_turn(self, monkeypatch):
        fake = FakeLLM(
            [StreamChunk(tool_calls=[ToolCall(id="x", name="nonexistent_tool", arguments="{}")])],
            [StreamChunk(text="Maaf, nggak bisa."), StreamChunk(tool_calls=[])],
        )
        events, turn = await drain([], "coba", monkeypatch, fake)
        result = [e for e in events if e.type == "tool_result"][0]
        assert result.result["ok"] is False
        assert turn is not None  # the turn still completed


@pytest.mark.asyncio
class TestFailureModes:
    async def test_iteration_cap_reports_error(self, monkeypatch):
        """A model stuck in a tool loop must surface, not spin up a bill."""
        forever = [StreamChunk(tool_calls=[ToolCall(id="i", name="lookup_place", arguments='{"query":"Bali"}')])]
        fake = FakeLLM(*[forever] * 10)
        monkeypatch.setattr(loop.client, "stream_completion", fake)

        events = []
        async for item in loop.run([], "halo", max_iterations=3):
            events.append(item)

        assert len(fake.calls) == 3
        assert events[-1].type == "error"

    async def test_llm_error_becomes_an_event(self, monkeypatch):
        def explode(messages, **kwargs):
            async def stream():
                raise loop.client.LLMAuthError("The API key was rejected by the provider.")
                yield  # pragma: no cover

            return stream()

        monkeypatch.setattr(loop.client, "stream_completion", explode)
        events = [e async for e in loop.run([], "halo")]
        assert events[-1].type == "error"
        assert "rejected" in events[-1].error


class TestPersona:
    def test_prompt_is_english(self):
        """
        The prompt is deliberately English: an Indonesian one biases every reply
        toward Indonesian no matter what the user wrote.
        """
        prompt = persona.system_prompt()
        assert "Reply in the language the user wrote in" in prompt

    def test_prompt_forbids_inventing_prices(self):
        assert "Never invent data a tool can provide" in persona.system_prompt()

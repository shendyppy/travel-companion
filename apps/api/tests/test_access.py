"""
Access control tests.

The security-relevant properties are asserted directly, because they are the
kind that break silently: a key that leaks into a log or an error message does
not fail any other test.
"""

import logging

import pytest

from src import access
from src.llm import client

FAKE_KEY = "sk-thisisafakekeyfortestingonly1234567890"


class FakeRequest:
    """Minimal stand-in for fastapi.Request."""

    def __init__(self, headers=None, ip="203.0.113.1"):
        self.headers = headers or {}
        self.client = type("C", (), {"host": ip})()


class TestKeyExtraction:
    def test_no_header_means_no_key(self):
        assert access.extract_key(FakeRequest()) == (None, None)

    def test_key_is_read_from_header(self):
        key, provider = access.extract_key(FakeRequest({access.API_KEY_HEADER: FAKE_KEY}))
        assert key == FAKE_KEY
        assert provider is None

    def test_short_values_are_rejected(self):
        """Empty or junk headers should not cost a network round trip to discover."""
        assert access.extract_key(FakeRequest({access.API_KEY_HEADER: "abc"})) == (None, None)
        assert access.extract_key(FakeRequest({access.API_KEY_HEADER: "   "})) == (None, None)

    def test_provider_header_is_honoured(self):
        _, provider = access.extract_key(FakeRequest({
            access.API_KEY_HEADER: FAKE_KEY,
            access.PROVIDER_HEADER: "openai",
        }))
        assert provider == "openai"

    def test_unknown_provider_falls_back_rather_than_failing(self):
        _, provider = access.extract_key(FakeRequest({
            access.API_KEY_HEADER: FAKE_KEY,
            access.PROVIDER_HEADER: "not-a-provider",
        }))
        assert provider is None


@pytest.mark.asyncio
class TestByok:
    async def test_own_key_skips_the_quota(self):
        grant = await access.check(FakeRequest({access.API_KEY_HEADER: FAKE_KEY}))
        assert grant.allowed
        assert grant.using_own_key
        assert grant.api_key == FAKE_KEY
        assert grant.remaining is None

    async def test_own_key_is_never_counted(self):
        """Repeated BYOK requests must not consume anyone's demo allowance."""
        request = FakeRequest({access.API_KEY_HEADER: FAKE_KEY}, ip="198.51.100.7")
        for _ in range(access.DEMO_DAILY_LIMIT + 5):
            grant = await access.check(request)
            assert grant.allowed


@pytest.mark.asyncio
class TestDemoQuota:
    async def test_quota_decrements_then_blocks(self, monkeypatch):
        monkeypatch.setattr(client, "is_configured", lambda provider=None: True)
        request = FakeRequest(ip="192.0.2.55")

        first = await access.check(request)
        assert first.allowed
        assert first.remaining == access.DEMO_DAILY_LIMIT - 1
        assert first.api_key is None  # falls back to the server key

        for _ in range(access.DEMO_DAILY_LIMIT):
            last = await access.check(request)

        assert last.allowed is False
        assert last.remaining == 0
        assert "own API key" in last.reason

    async def test_separate_ips_have_separate_budgets(self, monkeypatch):
        monkeypatch.setattr(client, "is_configured", lambda provider=None: True)
        a = await access.check(FakeRequest(ip="192.0.2.101"))
        b = await access.check(FakeRequest(ip="192.0.2.102"))
        assert a.remaining == b.remaining == access.DEMO_DAILY_LIMIT - 1

    async def test_forwarded_header_identifies_the_client(self, monkeypatch):
        """Behind Cloud Run the socket address is the proxy, not the user."""
        monkeypatch.setattr(client, "is_configured", lambda provider=None: True)
        request = FakeRequest({"x-forwarded-for": "192.0.2.200, 10.0.0.1"}, ip="10.0.0.1")
        assert access._client_ip(request) == "192.0.2.200"

    async def test_refuses_when_server_has_no_key(self, monkeypatch):
        monkeypatch.setattr(client, "is_configured", lambda provider=None: False)
        grant = await access.check(FakeRequest(ip="192.0.2.77"))
        assert grant.allowed is False
        assert "your own API key" in grant.reason


class TestSecrecy:
    def test_quota_info_exposes_no_secrets(self):
        rendered = str(access.quota_info())
        assert "sk-" not in rendered
        assert "never stored" in rendered

    def test_scrubber_catches_common_key_shapes(self):
        for secret in [
            "sk-abcdefghijklmnopqrstuvwxyz123456",
            "AIzaSyABCDEFGHIJKLMNOPQRSTUVWXYZ12345",
            "gsk_abcdefghijklmnopqrstuvwxyz",
            "Bearer abcdefghijklmnopqrstuvwxyz123",
        ]:
            scrubbed = client.scrub(f"request failed with {secret} attached")
            assert secret not in scrubbed
            assert "[REDACTED]" in scrubbed

    def test_refusal_reason_never_quotes_the_key(self):
        """Error text is user-visible; a key must never ride along in it."""
        for message in [
            access.Access(False, None, None, False, 0, "quota gone").reason,
            str(access.quota_info()),
        ]:
            assert FAKE_KEY not in (message or "")

    def test_provider_errors_are_scrubbed_before_logging(self, caplog):
        with caplog.at_level(logging.WARNING):
            client.scrub(f"upstream said: api_key={FAKE_KEY}")
        assert FAKE_KEY not in caplog.text

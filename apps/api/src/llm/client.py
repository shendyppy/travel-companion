"""
LLM client — a thin layer over LiteLLM.

Replaces universal_wrapper.py (459 lines of hand-written per-provider adapters).
LiteLLM already normalises streaming and tool-calling to the OpenAI shape across
providers, so what is left here is only two things: translating env vars into a
LiteLLM model string, and providing one streaming path that reassembles tool
call fragments.

Why this matters for BYOK (phase 3): `api_key` is passed per call and never read
from global state. Once a user's key arrives in a request header, it flows
straight through without restructuring anything.
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Optional

import litellm

logger = logging.getLogger(__name__)

# Common credential shapes: sk-..., AIza..., gsk_..., and Bearer headers. Used to
# scrub provider error messages before they reach the log. Provider errors often
# quote the request, and from phase 3 onward that request carries a user's key.
_SECRET_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9_\-]{16,}|AIza[A-Za-z0-9_\-]{20,}|gsk_[A-Za-z0-9_\-]{16,}"
    r"|Bearer\s+[A-Za-z0-9_\-\.]{16,}|(?i:api[_\-]?key\"?\s*[:=]\s*\"?)[A-Za-z0-9_\-]{16,})"
)


def scrub(text: str) -> str:
    """Replace anything credential-shaped with [REDACTED]."""
    return _SECRET_PATTERN.sub("[REDACTED]", text or "")


# Never write message contents or credentials to the log. This must be on before
# BYOK lands -- LiteLLM's debug logging can echo an entire request.
litellm.turn_off_message_logging = True

# Providers differ in which parameters they accept. Without this, sending
# `temperature` to a model that rejects it raises; with it, the parameter is
# quietly dropped.
litellm.drop_params = True


# ==============================================================================
# Provider resolution
# ==============================================================================

# provider -> (model env var, default model, api key env var, LiteLLM prefix)
_PROVIDERS: dict[str, tuple[str, str, str, str]] = {
    "gemini": ("GEMINI_MODEL", "gemini-2.5-flash", "GEMINI_API_KEY", "gemini"),
    "openai": ("OPENAI_MODEL", "gpt-4o", "OPENAI_API_KEY", "openai"),
    "anthropic": ("ANTHROPIC_MODEL", "claude-sonnet-4-5", "ANTHROPIC_API_KEY", "anthropic"),
    # GLM and custom are both OpenAI-compatible endpoints, separated by api_base
    "glm": ("GLM_MODEL", "glm-4.6", "GLM_API_KEY", "openai"),
    "custom": ("CUSTOM_MODEL", "custom-model", "CUSTOM_API_KEY", "openai"),
}

_API_BASE_ENV = {
    "glm": "GLM_API_BASE",
    "custom": "CUSTOM_API_BASE",
}


def active_provider() -> str:
    provider = os.getenv("LLM_PROVIDER", "gemini").lower()
    if provider not in _PROVIDERS:
        logger.warning("Unknown LLM_PROVIDER '%s', falling back to gemini", provider)
        return "gemini"
    return provider


def resolve_model(provider: Optional[str] = None) -> str:
    """Build the LiteLLM model string, e.g. 'gemini/gemini-2.5-flash'."""
    provider = provider or active_provider()
    model_env, model_default, _, prefix = _PROVIDERS[provider]
    return f"{prefix}/{os.getenv(model_env, model_default)}"


def resolve_api_base(provider: Optional[str] = None) -> Optional[str]:
    provider = provider or active_provider()
    env = _API_BASE_ENV.get(provider)
    return os.getenv(env) if env else None


def server_api_key(provider: Optional[str] = None) -> Optional[str]:
    """The server's own key. In phase 3 this becomes the fallback when a user brings none."""
    provider = provider or active_provider()
    _, _, key_env, _ = _PROVIDERS[provider]
    return os.getenv(key_env)


def is_configured(provider: Optional[str] = None) -> bool:
    return bool(server_api_key(provider))


# ==============================================================================
# Streaming results
# ==============================================================================


@dataclass
class ToolCall:
    """One requested tool call, reassembled from stream fragments."""

    id: str
    name: str
    arguments: str = ""  # raw JSON; parsed in the registry so errors surface there


@dataclass
class StreamChunk:
    """A single event from the LLM stream."""

    text: Optional[str] = None
    tool_calls: list[ToolCall] = field(default_factory=list)
    finish_reason: Optional[str] = None


# ==============================================================================
# Streaming
# ==============================================================================


async def stream_completion(
    messages: list[dict[str, Any]],
    *,
    tools: Optional[list[dict[str, Any]]] = None,
    api_key: Optional[str] = None,
    provider: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> AsyncIterator[StreamChunk]:
    """
    Stream a completion, optionally with tools.

    Yields StreamChunk with text fragments as they arrive. Tool calls are
    accumulated and emitted together in the final chunk, because their arguments
    arrive in pieces and the JSON is only valid once complete.

    Args:
        messages: the full history in OpenAI format. Always send all of it --
            this is where the old wrapper's amnesia bug cannot recur.
        tools: tool schemas. None means a plain chat call.
        api_key: the user's key (BYOK). Falls back to the server key.
    """
    provider = provider or active_provider()
    key = api_key or server_api_key(provider)

    if not key:
        raise LLMConfigError(
            f"No API key for provider '{provider}'. "
            f"Set {_PROVIDERS[provider][2]} in .env, or supply your own key."
        )

    kwargs: dict[str, Any] = {
        "model": resolve_model(provider),
        "messages": messages,
        "api_key": key,
        "stream": True,
    }

    api_base = resolve_api_base(provider)
    if api_base:
        kwargs["api_base"] = api_base
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"
    if temperature is None:
        temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    kwargs["temperature"] = temperature
    if max_tokens is None:
        max_tokens = int(os.getenv("LLM_MAX_TOKENS", "0")) or None
    if max_tokens:
        kwargs["max_tokens"] = max_tokens

    # Keyed by index -- providers stream tool arguments in fragments
    pending: dict[int, ToolCall] = {}
    finish_reason: Optional[str] = None

    try:
        response = await litellm.acompletion(**kwargs)

        async for chunk in response:
            if not chunk.choices:
                continue

            choice = chunk.choices[0]
            delta = getattr(choice, "delta", None)

            if choice.finish_reason:
                finish_reason = choice.finish_reason

            if delta is None:
                continue

            content = getattr(delta, "content", None)
            if content:
                yield StreamChunk(text=content)

            for fragment in getattr(delta, "tool_calls", None) or []:
                index = getattr(fragment, "index", 0) or 0
                call = pending.get(index)
                if call is None:
                    call = ToolCall(id="", name="")
                    pending[index] = call

                if getattr(fragment, "id", None):
                    call.id = fragment.id
                fn = getattr(fragment, "function", None)
                if fn is not None:
                    if getattr(fn, "name", None):
                        call.name = fn.name
                    if getattr(fn, "arguments", None):
                        call.arguments += fn.arguments

    except litellm.AuthenticationError as exc:
        # Do not pass the provider's raw message through -- it often quotes the
        # request, and from phase 3 that request contains the user's key.
        logger.warning("LLM authentication failed for provider %s", provider)
        raise LLMAuthError("The API key was rejected by the provider.") from exc
    except litellm.RateLimitError as exc:
        logger.warning("Rate limited by provider %s", provider)
        raise LLMRateLimitError("The provider is rate limiting. Try again shortly.") from exc
    except (LLMConfigError, LLMAuthError, LLMRateLimitError):
        raise
    except Exception as exc:
        # The original message is logged (after scrubbing) so problems like
        # "model not found" stay diagnosable. What reaches the user stays generic.
        logger.error(
            "LLM call failed (%s, model=%s): %s: %s",
            provider,
            kwargs["model"],
            type(exc).__name__,
            scrub(str(exc)),
        )
        raise LLMError("The call to the language model failed.") from exc

    ordered = [pending[i] for i in sorted(pending) if pending[i].name]
    yield StreamChunk(tool_calls=ordered, finish_reason=finish_reason)


# ==============================================================================
# Errors
# ==============================================================================


class LLMError(Exception):
    """An LLM failure safe to show a user (carries no request detail)."""


class LLMConfigError(LLMError):
    pass


class LLMAuthError(LLMError):
    pass


class LLMRateLimitError(LLMError):
    pass

"""
LLM client — tipis di atas LiteLLM.

Gantiin universal_wrapper.py (459 baris adapter tulisan tangan per provider).
LiteLLM udah menormalkan streaming dan tool-calling ke format OpenAI untuk semua
provider, jadi yang tersisa di sini cuma dua hal: nerjemahin env var jadi string
model LiteLLM, dan nyediain satu jalur streaming yang ngerakit potongan tool call.

Kenapa ini penting buat BYOK (Fase 3): parameter `api_key` diteruskan per-panggilan,
nggak pernah diambil dari state global. Jadi begitu key user masuk lewat header,
dia tinggal dialirin ke sini tanpa perlu ngubah struktur apa pun.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Optional

import litellm

logger = logging.getLogger(__name__)

# Jangan pernah nulis isi pesan atau kredensial ke log. Wajib dinyalain sebelum
# BYOK masuk di Fase 3 -- log debug LiteLLM bisa ngutip seluruh request.
litellm.turn_off_message_logging = True

# Provider beda-beda dukungan parameternya. Tanpa ini, kirim `temperature` ke model
# yang nggak nerima bakal ngelempar error; dengan ini parameternya dibuang diam-diam.
litellm.drop_params = True


# ==============================================================================
# Resolusi provider
# ==============================================================================

# provider -> (env model, model default, env api key, prefix LiteLLM)
_PROVIDERS: dict[str, tuple[str, str, str, str]] = {
    "gemini": ("GEMINI_MODEL", "gemini-2.5-flash", "GEMINI_API_KEY", "gemini"),
    "openai": ("OPENAI_MODEL", "gpt-4o", "OPENAI_API_KEY", "openai"),
    "anthropic": ("ANTHROPIC_MODEL", "claude-sonnet-4-5", "ANTHROPIC_API_KEY", "anthropic"),
    # GLM dan custom dua-duanya endpoint OpenAI-compatible, dibedain lewat api_base
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
        logger.warning("LLM_PROVIDER '%s' nggak dikenal, balik ke gemini", provider)
        return "gemini"
    return provider


def resolve_model(provider: Optional[str] = None) -> str:
    """Bikin string model LiteLLM, mis. 'gemini/gemini-2.5-flash'."""
    provider = provider or active_provider()
    model_env, model_default, _, prefix = _PROVIDERS[provider]
    return f"{prefix}/{os.getenv(model_env, model_default)}"


def resolve_api_base(provider: Optional[str] = None) -> Optional[str]:
    provider = provider or active_provider()
    env = _API_BASE_ENV.get(provider)
    return os.getenv(env) if env else None


def server_api_key(provider: Optional[str] = None) -> Optional[str]:
    """Key milik server. Di Fase 3 ini jadi cadangan kalau user nggak bawa key sendiri."""
    provider = provider or active_provider()
    _, _, key_env, _ = _PROVIDERS[provider]
    return os.getenv(key_env)


def is_configured(provider: Optional[str] = None) -> bool:
    return bool(server_api_key(provider))


# ==============================================================================
# Hasil streaming
# ==============================================================================


@dataclass
class ToolCall:
    """Satu permintaan pemanggilan tool, hasil rakitan dari potongan-potongan stream."""

    id: str
    name: str
    arguments: str = ""  # JSON mentah; di-parse di registry biar error-nya ketangkep di sana


@dataclass
class StreamChunk:
    """Satu kejadian dari stream LLM."""

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
    Streaming completion, opsional dengan tool.

    Ngeluarin StreamChunk berisi potongan teks begitu nyampe. Tool call
    dikumpulin dulu sampai stream selesai, baru dikeluarin sekaligus di chunk
    terakhir -- soalnya argumen tool datang terpotong-potong dan JSON-nya baru
    sah setelah utuh.

    Args:
        messages: riwayat lengkap format OpenAI. Selalu kirim semuanya --
            di sinilah bug amnesia si wrapper lama nggak bisa kejadian lagi.
        tools: skema tool. None berarti chat biasa.
        api_key: key milik user (BYOK). Kalau None, pakai key server.
    """
    provider = provider or active_provider()
    key = api_key or server_api_key(provider)

    if not key:
        raise LLMConfigError(
            f"Nggak ada API key buat provider '{provider}'. "
            f"Set {_PROVIDERS[provider][2]} di .env, atau kirim key kamu sendiri."
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

    # Dikumpulin per index -- provider ngirim argumen tool sepotong-sepotong
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
        # Jangan teruskan pesan mentah provider -- sering ngutip request, dan di
        # Fase 3 request itu berisi key user.
        logger.warning("Autentikasi LLM gagal buat provider %s", provider)
        raise LLMAuthError("API key ditolak provider.") from exc
    except litellm.RateLimitError as exc:
        logger.warning("Kena rate limit provider %s", provider)
        raise LLMRateLimitError("Provider lagi kena rate limit. Coba lagi sebentar.") from exc
    except (LLMConfigError, LLMAuthError, LLMRateLimitError):
        raise
    except Exception as exc:
        logger.error("Panggilan LLM gagal (%s): %s", provider, type(exc).__name__)
        raise LLMError("Panggilan ke LLM gagal.") from exc

    ordered = [pending[i] for i in sorted(pending) if pending[i].name]
    yield StreamChunk(tool_calls=ordered, finish_reason=finish_reason)


# ==============================================================================
# Error
# ==============================================================================


class LLMError(Exception):
    """Kegagalan LLM yang aman ditampilkan ke user (nggak ngandung detail request)."""


class LLMConfigError(LLMError):
    pass


class LLMAuthError(LLMError):
    pass


class LLMRateLimitError(LLMError):
    pass

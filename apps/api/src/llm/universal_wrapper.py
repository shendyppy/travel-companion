"""
Universal LLM Wrapper - Support multiple AI providers with single interface

Supported Providers:
- Gemini (Google)
- GLM (Z.ai)
- OpenAI
- Custom providers (via configurable adapter)

Usage:
    from llm.universal_wrapper import UniversalLLM

    llm = UniversalLLM(provider="gemini", model="gemini-2.5-flash")
    response = llm.chat("Hello, world!")

    # Switch to GLM
    llm = UniversalLLM(provider="glm", model="glm-4.6")
    response = llm.chat("Hello, world!")
"""

import os
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class LLMProvider(Enum):
    """Supported LLM providers"""
    GEMINI = "gemini"
    GLM = "glm"
    OPENAI = "openai"
    CUSTOM = "custom"

@dataclass
class LLMConfig:
    """Configuration for LLM providers"""
    provider: LLMProvider
    model: str
    api_key: str
    api_base: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    thinking_budget: Optional[int] = None
    timeout: int = 30

    @classmethod
    def from_env(cls, provider: str) -> 'LLMConfig':
        """Create config from environment variables"""
        provider_enum = LLMProvider(provider.lower())

        # Get API key based on provider
        api_key_map = {
            LLMProvider.GEMINI: os.getenv("GEMINI_API_KEY"),
            LLMProvider.GLM: os.getenv("GLM_API_KEY"),
            LLMProvider.OPENAI: os.getenv("OPENAI_API_KEY"),
            LLMProvider.CUSTOM: os.getenv("CUSTOM_API_KEY"),
        }

        # Get model defaults
        model_defaults = {
            LLMProvider.GEMINI: os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            LLMProvider.GLM: os.getenv("GLM_MODEL", "glm-4.6"),
            LLMProvider.OPENAI: os.getenv("OPENAI_MODEL", "gpt-4o"),
            LLMProvider.CUSTOM: os.getenv("CUSTOM_MODEL", "custom-model"),
        }

        return cls(
            provider=provider_enum,
            model=model_defaults[provider_enum],
            api_key=api_key_map[provider_enum] or "",
            api_base=os.getenv("CUSTOM_API_BASE"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "0")) or None,
            thinking_budget=int(os.getenv("THINKING_BUDGET", "0")) or None
        )

class BaseLLMAdapter(ABC):
    """Abstract base class for LLM adapters"""

    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = None
        self._initialize_client()

    @abstractmethod
    def _initialize_client(self) -> None:
        """Initialize the provider-specific client"""
        pass

    @abstractmethod
    def chat(self,
             message: str,
             system_prompt: Optional[str] = None,
             history: Optional[List[Dict]] = None,
             **kwargs) -> str:
        """Send a chat message and return response"""
        pass

    @abstractmethod
    def get_token_count(self, text: str) -> int:
        """Estimate token count for text"""
        pass

    def get_provider_info(self) -> Dict[str, Any]:
        """Get provider information"""
        return {
            "provider": self.config.provider.value,
            "model": self.config.model,
            "api_base": self.config.api_base
        }

class GeminiAdapter(BaseLLMAdapter):
    """Adapter for Google Gemini API"""

    def _initialize_client(self) -> None:
        try:
            from google import genai
            from google.genai import types

            self.client = genai.Client(api_key=self.config.api_key)
            self.types = types

            logger.info(f"Initialized Gemini client with model: {self.config.model}")
        except ImportError:
            raise ImportError("google-genai package is required for Gemini provider")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            raise

    def chat(self,
             message: str,
             system_prompt: Optional[str] = None,
             history: Optional[List[Dict]] = None,
             **kwargs) -> str:
        """Chat with Gemini"""
        try:
            # Build generation config
            config_kwargs = {}
            if self.config.temperature:
                config_kwargs["temperature"] = self.config.temperature
            if self.config.max_tokens:
                config_kwargs["max_output_tokens"] = self.config.max_tokens
            if self.config.thinking_budget:
                config_kwargs["thinking_config"] = self.types.ThinkingConfig(
                    thinking_budget=self.config.thinking_budget
                )

            config = self.types.GenerateContentConfig(**config_kwargs)

            # Handle system prompt
            if system_prompt:
                config.system_instruction = system_prompt

            # Create chat session
            chat = self.client.chats.create(model=self.config.model, config=config)

            # Send message and get response
            response = chat.send_message(message)

            logger.debug(f"Gemini response length: {len(response.text)} chars")
            return response.text

        except Exception as e:
            logger.error(f"Gemini chat error: {e}")
            raise

    def get_token_count(self, text: str) -> int:
        """Estimate token count for Gemini (roughly 4 chars = 1 token)"""
        return len(text) // 4

class GLMAdapter(BaseLLMAdapter):
    """Adapter for Z.ai GLM API"""

    def _initialize_client(self) -> None:
        try:
            import requests

            self.client = requests.Session()
            self.api_base = self.config.api_base or "https://open.bigmodel.cn/api/paas/v3"

            # Test connection
            self.client.headers.update({
                "Authorization": self.config.api_key,  # GLM doesn't use Bearer prefix
                "Content-Type": "application/json"
            })

            logger.info(f"Initialized GLM client with model: {self.config.model}")
        except ImportError:
            raise ImportError("requests package is required for GLM provider")
        except Exception as e:
            logger.error(f"Failed to initialize GLM client: {e}")
            raise

    def chat(self,
             message: str,
             system_prompt: Optional[str] = None,
             history: Optional[List[Dict]] = None,
             **kwargs) -> str:
        """Chat with GLM"""
        try:
            # Build messages
            messages = []

            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})

            # Add history
            if history:
                messages.extend(history)

            # Add current message
            messages.append({"role": "user", "content": message})

            # Make request
            response = self.client.post(
                f"{self.api_base}/chat/completions",
                json={
                    "model": self.config.model,
                    "messages": messages,
                    "temperature": self.config.temperature,
                    "max_tokens": self.config.max_tokens or 2048,
                },
                timeout=self.config.timeout
            )

            response.raise_for_status()
            data = response.json()

            return data["choices"][0]["message"]["content"]

        except Exception as e:
            logger.error(f"GLM chat error: {e}")
            raise

    def get_token_count(self, text: str) -> int:
        """Estimate token count for GLM (roughly 2 chars = 1 token for Chinese/mixed)"""
        return len(text) // 2

class OpenAIAdapter(BaseLLMAdapter):
    """Adapter for OpenAI API"""

    def _initialize_client(self) -> None:
        try:
            import openai

            self.client = openai.OpenAI(
                api_key=self.config.api_key,
                base_url=self.config.api_base
            )

            logger.info(f"Initialized OpenAI client with model: {self.config.model}")
        except ImportError:
            raise ImportError("openai package is required for OpenAI provider")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise

    def chat(self,
             message: str,
             system_prompt: Optional[str] = None,
             history: Optional[List[Dict]] = None,
             **kwargs) -> str:
        """Chat with OpenAI"""
        try:
            # Build messages
            messages = []

            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})

            # Add history
            if history:
                messages.extend(history)

            # Add current message
            messages.append({"role": "user", "content": message})

            # Make request
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                timeout=self.config.timeout
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"OpenAI chat error: {e}")
            raise

    def get_token_count(self, text: str) -> int:
        """Estimate token count for OpenAI"""
        try:
            import tiktoken
            enc = tiktoken.encoding_for_model(self.config.model)
            return len(enc.encode(text))
        except ImportError:
            # Fallback estimation
            return len(text) // 4

class CustomAdapter(BaseLLMAdapter):
    """Custom adapter for other OpenAI-compatible APIs"""

    def _initialize_client(self) -> None:
        try:
            import requests

            self.client = requests.Session()

            # Default to OpenAI-compatible format
            self.api_base = self.config.api_base or "https://api.openai.com/v1"
            self.client.headers.update({
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            })

            logger.info(f"Initialized custom client with model: {self.config.model}")
        except ImportError:
            raise ImportError("requests package is required for custom provider")
        except Exception as e:
            logger.error(f"Failed to initialize custom client: {e}")
            raise

    def chat(self,
             message: str,
             system_prompt: Optional[str] = None,
             history: Optional[List[Dict]] = None,
             **kwargs) -> str:
        """Chat with custom provider"""
        # Similar to OpenAI adapter
        return OpenAIAdapter(self.config).chat(message, system_prompt, history)

    def get_token_count(self, text: str) -> int:
        """Estimate token count"""
        return len(text) // 4

class UniversalLLM:
    """Universal LLM interface supporting multiple providers"""

    ADAPTERS = {
        LLMProvider.GEMINI: GeminiAdapter,
        LLMProvider.GLM: GLMAdapter,
        LLMProvider.OPENAI: OpenAIAdapter,
        LLMProvider.CUSTOM: CustomAdapter,
    }

    def __init__(self, provider: Union[str, LLMProvider] = None, config: Optional[LLMConfig] = None):
        """
        Initialize Universal LLM

        Args:
            provider: LLM provider name or enum
            config: Optional pre-built configuration
        """
        # Use config if provided, otherwise create from env/provider
        if config:
            self.config = config
            provider = config.provider
        else:
            # Get provider from env or parameter
            provider_name = provider or os.getenv("LLM_PROVIDER", "gemini")
            provider = LLMProvider(provider_name.lower())
            self.config = LLMConfig.from_env(provider_name)

        # Initialize adapter
        adapter_class = self.ADAPTERS.get(provider)
        if not adapter_class:
            raise ValueError(f"Unsupported provider: {provider}")

        self.adapter = adapter_class(self.config)
        self.provider = provider

        logger.info(f"Initialized Universal LLM with provider: {provider.value}")

    def chat(self,
             message: str,
             system_prompt: Optional[str] = None,
             history: Optional[List[Dict]] = None,
             return_metadata: bool = False,
             **kwargs) -> Union[str, Dict[str, Any]]:
        """
        Send chat message to LLM

        Args:
            message: User message
            system_prompt: Optional system prompt
            history: Conversation history
            return_metadata: Whether to return metadata with response
            **kwargs: Additional provider-specific args

        Returns:
            Response text or dict with response + metadata
        """
        try:
            response = self.adapter.chat(
                message=message,
                system_prompt=system_prompt,
                history=history,
                **kwargs
            )

            if return_metadata:
                return {
                    "response": response,
                    "metadata": {
                        "provider": self.provider.value,
                        "model": self.config.model,
                        "tokens_used": self.get_token_count(message + response),
                        "temperature": self.config.temperature
                    }
                }

            return response

        except Exception as e:
            logger.error(f"Chat error: {e}")
            raise

    def get_token_count(self, text: str) -> int:
        """Get token count for text"""
        return self.adapter.get_token_count(text)

    def get_provider_info(self) -> Dict[str, Any]:
        """Get provider information"""
        info = self.adapter.get_provider_info()
        info.update({
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "has_thinking": self.config.thinking_budget is not None
        })
        return info

    @classmethod
    def list_providers(cls) -> List[Dict[str, str]]:
        """List all supported providers"""
        return [
            {
                "name": provider.value,
                "adapter": adapter_class.__name__
            }
            for provider, adapter_class in cls.ADAPTERS.items()
        ]

# Convenience functions for backward compatibility
def create_llm(provider: str = None, model: str = None, **kwargs) -> UniversalLLM:
    """Create LLM instance with simple interface"""
    if provider or model:
        # Override env vars if specified
        if provider:
            os.environ["LLM_PROVIDER"] = provider
        if model:
            os.environ[f"{provider.upper()}_MODEL"] = model

    return UniversalLLM()
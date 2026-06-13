"""Azure OpenAI / Groq LLM client for learning agents."""
from __future__ import annotations

import logging
import time
from typing import Any

import os

import openai

logger = logging.getLogger(__name__)


def _setting(name: str, default: str = "") -> str:
    try:
        from django.conf import settings as django_settings

        return getattr(django_settings, name, default) or os.getenv(name, default)
    except Exception:
        return os.getenv(name, default)

GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
API_VERSION = "2024-08-01-preview"


class FoundryClient:
    """LLM client with Azure OpenAI primary and Groq fallback."""

    def __init__(self) -> None:
        azure_endpoint = (_setting("AZURE_OPENAI_ENDPOINT") or "").rstrip("/")
        if azure_endpoint.endswith("/openai/v1"):
            azure_endpoint = azure_endpoint[: -len("/openai/v1")]
        azure_key = _setting("AZURE_OPENAI_API_KEY")
        groq_key = _setting("GROQ_API_KEY")
        self.deployment_name = _setting("AZURE_AI_MODEL_DEPLOYMENT", "gpt-4o")
        self.provider = "none"
        self.client: openai.OpenAI | openai.AzureOpenAI | None = None
        self._groq_client: openai.OpenAI | None = None

        if azure_endpoint and azure_key:
            try:
                self.client = openai.AzureOpenAI(
                    azure_endpoint=azure_endpoint,
                    api_key=azure_key,
                    api_version=API_VERSION,
                )
                self.provider = "azure_openai"
                self.model = self.deployment_name
            except Exception as exc:
                logger.warning("Azure OpenAI init failed: %s", exc)

        if self.client is None and groq_key:
            self.client = openai.OpenAI(api_key=groq_key, base_url=GROQ_BASE_URL)
            self.provider = "groq"
            self.model = GROQ_MODEL

        if groq_key:
            self._groq_client = openai.OpenAI(api_key=groq_key, base_url=GROQ_BASE_URL)

        logger.info("LLM provider: %s", self.provider)

    def chat(self, system_prompt: str, user_prompt: str, temperature: float = 0.3) -> str:
        if self.client is None:
            return self._offline_response(system_prompt, user_prompt)

        try:
            return self._call(self.client, self.model, system_prompt, user_prompt, temperature)
        except Exception as exc:
            if self._is_quota_error(exc) and self._groq_client and self.provider != "groq":
                logger.warning("Azure quota error, retrying with Groq: %s", exc)
                return self._call(
                    self._groq_client, GROQ_MODEL, system_prompt, user_prompt, temperature
                )
            logger.error("LLM chat failed: %s", exc)
            return self._offline_response(system_prompt, user_prompt)

    def _call(
        self,
        client: openai.OpenAI | openai.AzureOpenAI,
        model: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
    ) -> str:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=1500,
        )
        if response.usage:
            logger.info("Tokens used: %s", response.usage.total_tokens)
        content = response.choices[0].message.content
        return content or ""

    def health_check(self) -> dict[str, Any]:
        if self.client is None:
            return {
                "provider": self.provider,
                "model": "offline",
                "status": "error",
                "latency_ms": 0,
            }
        start = time.perf_counter()
        try:
            self.chat("You are a health check assistant.", "Reply with OK only.", temperature=0)
            latency = int((time.perf_counter() - start) * 1000)
            return {
                "provider": self.provider,
                "model": self.model,
                "status": "ok",
                "latency_ms": latency,
            }
        except Exception as exc:
            latency = int((time.perf_counter() - start) * 1000)
            logger.error("LLM health check failed: %s", exc)
            return {
                "provider": self.provider,
                "model": self.model,
                "status": "error",
                "latency_ms": latency,
            }

    @staticmethod
    def _is_quota_error(exc: Exception) -> bool:
        msg = str(exc).lower()
        return "429" in msg or "quota" in msg or "rate limit" in msg

    @staticmethod
    def _offline_response(system_prompt: str, user_prompt: str) -> str:
        return (
            "[Offline LLM fallback] Configure AZURE_OPENAI_ENDPOINT + AZURE_OPENAI_API_KEY "
            "or GROQ_API_KEY for live synthesis.\n\n"
            f"Context preview: {user_prompt[:500]}"
        )

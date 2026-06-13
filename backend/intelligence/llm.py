"""
LLM client: Azure OpenAI (primary) or Groq fallback.
Backward-compatible helpers for sentiment, risk, and chat_completion.
"""
from __future__ import annotations

import logging
import os
import time
from typing import Any, Optional

logger = logging.getLogger(__name__)

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_MODEL = "llama-3.3-70b-versatile"
API_VERSION = "2024-08-01-preview"

_client_instance: "LLMClient | None" = None


class LLMClient:
    """Azure OpenAI primary with Groq fallback on quota errors."""

    def __init__(self) -> None:
        azure_endpoint = (os.getenv("AZURE_OPENAI_ENDPOINT", "") or "").rstrip("/")
        if azure_endpoint.endswith("/openai/v1"):
            azure_endpoint = azure_endpoint[: -len("/openai/v1")]
        azure_key = os.getenv("AZURE_OPENAI_API_KEY", "")
        groq_key = os.getenv("GROQ_API_KEY", "")
        self.provider = "none"
        self.client = None
        self._groq_client = None
        self.model = GROQ_MODEL

        if azure_endpoint and azure_key:
            try:
                import openai

                self.client = openai.AzureOpenAI(
                    azure_endpoint=azure_endpoint,
                    api_key=azure_key,
                    api_version=API_VERSION,
                )
                self.model = os.getenv("AZURE_AI_MODEL_DEPLOYMENT", "gpt-4.1-mini")
                self.provider = "azure_openai"
            except Exception as exc:
                logger.warning("Azure OpenAI init failed: %s", exc)

        if self.client is None and groq_key:
            import openai

            self.client = openai.OpenAI(api_key=groq_key, base_url=GROQ_BASE_URL)
            self.model = GROQ_MODEL
            self.provider = "groq"

        if groq_key:
            import openai

            self._groq_client = openai.OpenAI(api_key=groq_key, base_url=GROQ_BASE_URL)

        logger.info("LLM provider active: %s / %s", self.provider, self.model)

    def chat(self, system_prompt: str, user_prompt: str, temperature: float = 0.3) -> str:
        if self.client is None:
            raise RuntimeError("No LLM provider configured (Azure OpenAI or Groq)")

        try:
            return self._call(self.client, self.model, system_prompt, user_prompt, temperature)
        except Exception as exc:
            if self._is_quota_error(exc) and self._groq_client and self.provider != "groq":
                logger.warning("Azure quota error, retrying with Groq: %s", exc)
                return self._call(
                    self._groq_client, GROQ_MODEL, system_prompt, user_prompt, temperature
                )
            logger.error("LLM chat failed: %s", exc)
            raise

    def _call(
        self,
        client: Any,
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
            logger.info("[%s] tokens: %s", self.provider, response.usage.total_tokens)
        return (response.choices[0].message.content or "").strip()

    def health_check(self) -> dict[str, Any]:
        start = time.time()
        try:
            self.chat("You are a test agent.", "Reply with: OK", temperature=0)
            return {
                "provider": self.provider,
                "model": self.model,
                "status": "ok",
                "latency_ms": int((time.time() - start) * 1000),
            }
        except Exception as exc:
            return {
                "provider": self.provider,
                "model": self.model,
                "status": "error",
                "error": str(exc),
            }

    @staticmethod
    def _is_quota_error(exc: Exception) -> bool:
        msg = str(exc).lower()
        return "429" in msg or "quota" in msg or "rate limit" in msg


def get_llm_client() -> LLMClient:
    global _client_instance
    if _client_instance is None:
        _client_instance = LLMClient()
    return _client_instance


def _safe_chat(system_prompt: str, user_prompt: str, max_tokens: int = 500) -> Optional[str]:
    try:
        client = get_llm_client()
        return client.chat(system_prompt, user_prompt)[:max_tokens]
    except Exception:
        return None


def explain_sentiment(text: str, sentiment: str, probabilities: dict) -> str:
    system_prompt = (
        "You are a financial analyst. In 1-3 concise sentences, explain why the given "
        "financial news text has the stated sentiment. Mention specific drivers (e.g., "
        "rates, earnings, guidance, macro). No disclaimers."
    )
    user_prompt = (
        f"Text:\n{text[:2000]}\n\nSentiment: {sentiment}. "
        f"Probabilities: {probabilities}. Explain why."
    )
    result = _safe_chat(system_prompt, user_prompt, max_tokens=200)
    if result:
        return result
    drivers = {
        "positive": "optimistic language, growth/earnings strength, or favorable macro.",
        "negative": "concerns over rates, margins, or macro headwinds.",
        "neutral": "mixed or factual tone without strong directional bias.",
    }
    return f"Sentiment is {sentiment} based on {drivers.get(sentiment, drivers['neutral'])}"


def extract_risk_drivers(text: str) -> list:
    system_prompt = (
        "List 3-5 key risk drivers from this financial news, one per line. "
        "Only output the list, no numbering or extra text."
    )
    result = _safe_chat(system_prompt, f"News:\n{text[:2000]}", max_tokens=150)
    if result:
        return [line.strip() for line in result.split("\n") if line.strip()][:5]
    return ["Policy uncertainty", "Market volatility", "Macro headwinds"]


def event_impact_summary(text: str, sentiment: str) -> str:
    system_prompt = (
        "You are a quant analyst. In 2-3 sentences summarize the main event and typical market impact."
    )
    result = _safe_chat(system_prompt, f"News:\n{text[:2000]}\n\nSentiment: {sentiment}.", max_tokens=200)
    if result:
        return result
    return (
        f"Sentiment is {sentiment}. Similar past events have been associated with "
        "short-term volatility; consider sector and macro context for positioning."
    )


def extract_events(text: str) -> list:
    system_prompt = (
        "From this financial news, extract events. One per line, format: TYPE: short description."
    )
    result = _safe_chat(system_prompt, f"News:\n{text[:2000]}", max_tokens=200)
    if result:
        events = []
        for line in result.split("\n"):
            line = line.strip()
            if ":" in line:
                kind, desc = line.split(":", 1)
                events.append({"type": kind.strip().upper(), "description": desc.strip()})
        return events[:10]
    return [{"type": "OTHER", "description": "General market or company news"}]


def aspect_sentiment(text: str, aspects: list) -> dict:
    if not aspects:
        aspects = ["earnings", "macro_economy", "sector_outlook", "management_guidance"]
    system_prompt = (
        "For each aspect, output one word: positive, negative, or neutral. "
        "Output only a JSON object with aspect names as keys."
    )
    result = _safe_chat(system_prompt, f"Aspects: {aspects}\n\nNews:\n{text[:1500]}", max_tokens=150)
    if result:
        try:
            import json

            cleaned = result.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
            return json.loads(cleaned)
        except Exception:
            pass
    return {a: "neutral" for a in aspects}


def chat_completion(user_content: str, system_content: str = "", max_tokens: int = 500) -> Optional[str]:
    try:
        client = get_llm_client()
        return client.chat(system_content or "You are a helpful assistant.", user_content)[:max_tokens]
    except Exception as exc:
        logger.exception("chat_completion failed: %s", exc)
        return None

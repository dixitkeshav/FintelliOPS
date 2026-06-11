"""
LLM client: Groq (default) or OpenAI-compatible endpoints.
Set GROQ_API_KEY for Groq. Set OPENAI_API_KEY to use OpenAI instead.
Falls back to rule-based responses when no API key is set.
"""
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Groq (default): https://api.groq.com/openai/v1 — use GROQ_API_KEY
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")  # or llama-3.1-8b-instant, mixtral-8x7b-32768

# OpenAI (optional override)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")


def _get_client_and_model():
    """Return (OpenAI client, model name). Prefer Groq if GROQ_API_KEY set."""
    try:
        from openai import OpenAI
    except ImportError:
        return None, None
    if GROQ_API_KEY:
        return OpenAI(api_key=GROQ_API_KEY, base_url=GROQ_BASE_URL), GROQ_MODEL
    if OPENAI_API_KEY:
        return OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL), OPENAI_MODEL
    return None, None


def _call_llm(system_prompt: str, user_prompt: str, max_tokens: int = 500) -> Optional[str]:
    """Call Groq or OpenAI. Returns None on failure."""
    client, model = _get_client_and_model()
    if not client or not model:
        logger.warning("No GROQ_API_KEY or OPENAI_API_KEY set; using fallback responses.")
        return None
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.3,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception as e:
        logger.exception("LLM call failed: %s", e)
        return None


def explain_sentiment(text: str, sentiment: str, probabilities: dict) -> str:
    """Generate natural language explanation for why the sentiment is positive/negative/neutral."""
    system_prompt = (
        "You are a financial analyst. In 1-3 concise sentences, explain why the given "
        "financial news text has the stated sentiment. Mention specific drivers (e.g., "
        "rates, earnings, guidance, macro). No disclaimers."
    )
    user_prompt = (
        f"Text:\n{text[:2000]}\n\nSentiment: {sentiment}. "
        f"Probabilities: {probabilities}. Explain why."
    )
    result = _call_llm(system_prompt, user_prompt, max_tokens=200)
    if result:
        return result
    drivers = {"positive": "optimistic language, growth/earnings strength, or favorable macro.",
               "negative": "concerns over rates, margins, or macro headwinds.",
               "neutral": "mixed or factual tone without strong directional bias."}
    return f"Sentiment is {sentiment} based on {drivers.get(sentiment, drivers['neutral'])}"


def extract_risk_drivers(text: str) -> list:
    """Extract key risk drivers from news text."""
    system_prompt = (
        "List 3-5 key risk drivers from this financial news, one per line. "
        "Only output the list, no numbering or extra text. Examples: RBI policy uncertainty, "
        "rising bond yields, inflation, earnings miss, regulatory risk."
    )
    user_prompt = f"News:\n{text[:2000]}"
    result = _call_llm(system_prompt, user_prompt, max_tokens=150)
    if result:
        return [line.strip() for line in result.split("\n") if line.strip()][:5]
    return ["Policy uncertainty", "Market volatility", "Macro headwinds"]


def event_impact_summary(text: str, sentiment: str) -> str:
    """Generate event impact summary with historical context."""
    system_prompt = (
        "You are a quant analyst. In 2-3 sentences: (1) Summarize the main event in the news. "
        "(2) State typical market impact (e.g., 'Historically similar narratives led to 2-4% "
        "drawdowns in banking stocks'). Be specific and concise."
    )
    user_prompt = f"News:\n{text[:2000]}\n\nOverall sentiment: {sentiment}."
    result = _call_llm(system_prompt, user_prompt, max_tokens=200)
    if result:
        return result
    return (
        f"Sentiment is {sentiment}. Similar past events have been associated with "
        "short-term volatility; consider sector and macro context for positioning."
    )


def extract_events(text: str) -> list:
    """Extract structured events: mergers, rate hikes, earnings, etc."""
    system_prompt = (
        "From this financial news, extract events. One per line, format: TYPE: short description. "
        "Types: RATE_DECISION, EARNINGS, MERGER_ACQUISITION, GUIDANCE, REGULATION, MACRO_DATA, "
        "OTHER. Only output the list."
    )
    user_prompt = f"News:\n{text[:2000]}"
    result = _call_llm(system_prompt, user_prompt, max_tokens=200)
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
    """Aspect-based sentiment: for each aspect, return sentiment."""
    if not aspects:
        aspects = ["earnings", "macro_economy", "sector_outlook", "management_guidance"]
    system_prompt = (
        "For each aspect, output one word: positive, negative, or neutral. "
        "Output only a JSON object with aspect names as keys and sentiment as values. "
        "Example: {\"earnings\": \"positive\", \"macro_economy\": \"negative\"}"
    )
    user_prompt = f"Aspects: {aspects}\n\nNews:\n{text[:1500]}"
    result = _call_llm(system_prompt, user_prompt, max_tokens=150)
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
    """Single call for any prompt (used by Decision agent and Symbol Deep-Dive)."""
    client, model = _get_client_and_model()
    if not client or not model:
        return None
    try:
        messages = [{"role": "user", "content": user_content}]
        if system_content:
            messages.insert(0, {"role": "system", "content": system_content})
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.3,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception as e:
        logger.exception("chat_completion failed: %s", e)
        return None

"""
Compile natural-language backtest strategies via Groq/OpenAI into structured rules.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Optional

from intelligence.llm import chat_completion

logger = logging.getLogger(__name__)

SUPPORTED_INDICATORS = (
    "rsi, mfi, macd_hist, bb_pct, vwap_dist, zigzag_trend, sentiment, news_event"
)

SYSTEM_COMPILE = f"""You convert trading strategy text into JSON for a backtest engine.

Supported rule types:
1) {{"type": "news_event"}} — trade only when relevant company news exists that day
2) {{"type": "sentiment", "op": ">"|"<"|">=", "<=", "value": number}} — news sentiment score (-1 to 1)
3) {{"type": "indicator", "indicator": IND, "op": ">"|"<"|">="|"<="|"between"|"near", "value": number, "value2": optional}}

Indicators (IND):
- rsi (0-100), mfi (0-100), macd_hist (any float)
- bb_pct: Bollinger %B (0-100, >80 overbought, <20 oversold)
- vwap_dist: distance from VWAP in percent (e.g. price 2% above VWAP = 2)
- zigzag_trend: 1 bullish leg, -1 bearish leg, 0 neutral

For "near" op on vwap_dist or bb_pct, use value as center and value2 as half-width (e.g. near 40 -> op near, value 40, value2 5).

Also return:
- action: BUY | SELL | BUY_VOL | SELL_VOL | NEUTRAL
- options_structure: null | iron_condor | butterfly | long_straddle
- risk_reward: {{"stop_loss_pct": number, "take_profit_pct": number}} e.g. 1:2 -> stop 1, take 2
- normalized_prompt: one-line corrected English
- fixes_applied: short list of what you fixed

Output ONLY valid JSON:
{{
  "rules": [...],
  "action": "BUY",
  "options_structure": null,
  "risk_reward": {{"stop_loss_pct": 1.0, "take_profit_pct": 2.0}},
  "normalized_prompt": "...",
  "fixes_applied": ["..."]
}}
"""

# Static autocomplete phrases (prefix match)
SUGGESTION_PHRASES = [
    "Buy when RSI is greater than ",
    "Buy when RSI is less than ",
    "Buy when MFI is greater than ",
    "Buy when MFI is less than ",
    "Buy when Bollinger Band %B is greater than ",
    "Buy when Bollinger Band %B is less than ",
    "Buy when price is above VWAP by ",
    "Buy when price is near VWAP around ",
    "Buy when zigzag trend is bullish",
    "Buy when MACD histogram is positive",
    "Buy only on news days when sentiment is positive",
    "Create a strategy using Bollinger Band, VWAP, and zigzag with risk reward 1:2",
    "Iron condor when RSI is between 40 and 60",
    "Long straddle on major news days",
    "Sell when RSI is above 70",
]


def suggest_phrases(prefix: str, limit: int = 8) -> list[str]:
    p = (prefix or "").strip().lower()
    if not p:
        return SUGGESTION_PHRASES[:limit]
    out = [s for s in SUGGESTION_PHRASES if s.lower().startswith(p) or p in s.lower()]
    if len(out) < limit:
        for s in SUGGESTION_PHRASES:
            if s not in out and any(w in s.lower() for w in p.split()[:4]):
                out.append(s)
            if len(out) >= limit:
                break
    return out[:limit]


def _extract_json(text: str) -> Optional[dict]:
    if not text:
        return None
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        m = re.search(r"\{[\s\S]*\}", cleaned)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                return None
    return None


def compile_strategy(prompt: str, mode_hint: str = "equity") -> dict[str, Any]:
    """
    Use Groq to normalize/fix strategy text and emit executable rules.
    Falls back to empty rules if LLM unavailable (caller should use regex parser).
    """
    raw = (prompt or "").strip()
    if not raw:
        return {
            "rules": [],
            "action": "BUY",
            "options_structure": None,
            "risk_reward": None,
            "normalized_prompt": "",
            "fixes_applied": [],
            "source": "empty",
        }

    user = f"Trading mode hint: {mode_hint}\n\nUser strategy:\n{raw}"
    llm_out = chat_completion(user, SYSTEM_COMPILE, max_tokens=800)
    parsed = _extract_json(llm_out or "")
    if parsed and isinstance(parsed.get("rules"), list):
        return {
            "rules": parsed["rules"],
            "action": parsed.get("action") or "BUY",
            "options_structure": parsed.get("options_structure"),
            "risk_reward": parsed.get("risk_reward"),
            "normalized_prompt": parsed.get("normalized_prompt") or raw,
            "fixes_applied": parsed.get("fixes_applied") or [],
            "source": "groq",
        }

    # Groq failed — return marker so caller uses enhanced regex parser
    return {
        "rules": [],
        "action": "BUY",
        "options_structure": None,
        "risk_reward": _parse_risk_reward(raw),
        "normalized_prompt": raw,
        "fixes_applied": ["LLM unavailable — using built-in parser"],
        "source": "fallback",
    }


def _parse_risk_reward(text: str) -> Optional[dict[str, float]]:
    t = text.lower()
    m = re.search(r"(\d+(?:\.\d+)?)\s*:\s*(\d+(?:\.\d+)?)", t)
    if m:
        a, b = float(m.group(1)), float(m.group(2))
        return {"stop_loss_pct": a, "take_profit_pct": b}
    m2 = re.search(r"p/?l\s*ratio\s*(?:of\s*)?(\d+)\s*(?:to|is|:)\s*(\d+)", t)
    if m2:
        return {"stop_loss_pct": float(m2.group(1)), "take_profit_pct": float(m2.group(2))}
    return None


def groq_suggest_next_words(prefix: str) -> list[str]:
    """Optional LLM completion for typing assist."""
    if len(prefix) < 3:
        return suggest_phrases(prefix)
    system = "Complete the trading strategy phrase. Return only the completion text (no quotes), max 6 words."
    completion = chat_completion(f"Continue: {prefix}", system, max_tokens=30)
    if completion:
        full = (prefix + completion).strip()
        return [full] + suggest_phrases(prefix, 5)
    return suggest_phrases(prefix)

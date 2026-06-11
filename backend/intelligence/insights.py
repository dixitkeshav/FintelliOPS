"""
Orchestrates GenAI insights: explanation, risk drivers, event impact, events, aspect sentiment.
"""
import logging
from typing import Any

from .llm import (
    explain_sentiment,
    extract_risk_drivers,
    event_impact_summary,
    extract_events,
    aspect_sentiment,
)

logger = logging.getLogger(__name__)


def build_genai_insights(
    text: str,
    sentiment: str,
    probabilities: dict,
    aspects: list = None,
    include_aspect: bool = True,
) -> dict[str, Any]:
    """
    Build full GenAI intelligence payload for a piece of news.
    Returns: why_sentiment, risk_drivers, event_impact_summary, events, aspect_sentiment (optional).
    """
    aspects = aspects or ["earnings", "macro_economy", "sector_outlook", "guidance"]
    why = explain_sentiment(text, sentiment, probabilities)
    risk_drivers = extract_risk_drivers(text)
    impact_summary = event_impact_summary(text, sentiment)
    events = extract_events(text)
    out = {
        "why_sentiment": why,
        "risk_drivers": risk_drivers,
        "event_impact_summary": impact_summary,
        "events": events,
    }
    if include_aspect:
        out["aspect_sentiment"] = aspect_sentiment(text, aspects)
    return out

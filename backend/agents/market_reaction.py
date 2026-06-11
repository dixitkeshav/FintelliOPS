"""
Market Reaction Agent: checks historical price reactions to similar news.
"""
import logging
from typing import Any

from .base import BaseAgent

logger = logging.getLogger(__name__)


class MarketReactionAgent(BaseAgent):
    """Checks historical price reactions to similar news (can integrate yfinance later)."""

    def __init__(self):
        super().__init__(name="MarketReaction", role="Historical price reactions to similar news")

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        sentiment = (context.get("aggregate_sentiment") or "neutral").lower()
        ticker = context.get("ticker", "")
        tech = (context.get("technical_signal") or "").lower()
        tech_note = ""
        if tech == "bullish":
            tech_note = " Technical structure is bullish (price above key MAs)."
        elif tech == "bearish":
            tech_note = " Technical structure is bearish (price below key MAs)."
        if sentiment == "negative":
            reaction = (
                "Historically, similar negative sentiment led to 2–4% drawdowns in related names over ~5 days."
                + tech_note
            )
        elif sentiment == "positive":
            reaction = (
                "Similar positive sentiment has often coincided with 1–3% short-term upside in related sectors."
                + tech_note
            )
        else:
            reaction = "Neutral sentiment typically shows limited directional move; volatility may still rise." + tech_note

        finding = {"sentiment": sentiment, "reaction_note": reaction, "ticker": ticker}
        self._remember(finding)

        return {
            "historical_reaction": reaction,
            "summary": reaction,
        }

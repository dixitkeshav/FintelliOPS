"""
Macro Context Agent: links news to macro indicators (rates, CPI, GDP).
"""
import logging
import os
from typing import Any

from .base import BaseAgent

logger = logging.getLogger(__name__)


class MacroContextAgent(BaseAgent):
    """Links news sentiment to macro indicators."""

    def __init__(self):
        super().__init__(name="MacroContext", role="Link news to macro indicators (rates, CPI, GDP)")

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        articles = context.get("articles", [])
        ticker = context.get("ticker", "")
        # In production, fetch real macro data (e.g., FRED API). Here we infer from headlines.
        headlines = " ".join(
            (a.get("title") or a.get("summary") or "")[:200] for a in articles[:10]
        ).lower()

        macro_links = []
        if any(k in headlines for k in ["rate", "rbi", "fed", "interest"]):
            macro_links.append("Rates / monetary policy")
        if any(k in headlines for k in ["inflation", "cpi", "prices"]):
            macro_links.append("Inflation / CPI")
        if any(k in headlines for k in ["gdp", "growth", "recession"]):
            macro_links.append("GDP / growth")
        if any(k in headlines for k in ["bond", "yield", "treasury"]):
            macro_links.append("Bond yields")
        if not macro_links:
            macro_links.append("General market sentiment")

        finding = {"macro_links": macro_links, "headlines_sample": headlines[:300]}
        self._remember(finding)

        return {
            "macro_links": macro_links,
            "summary": f"News linked to: {', '.join(macro_links)}.",
        }

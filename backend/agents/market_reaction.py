"""Market Reaction Agent: sector reaction prediction via Fabric IQ."""
from __future__ import annotations

import logging
from typing import Any

from .base import BaseAgent
from .iq_base import agent_result

logger = logging.getLogger(__name__)


class MarketReactionAgent(BaseAgent):
    """Predicts market reaction using sector ontology and prior agent outputs."""

    def __init__(self, llm=None, foundry_iq=None, fabric_iq=None, work_iq=None) -> None:
        super().__init__(name="MarketReaction", role="Historical price reactions to similar news")
        self.llm = llm
        self.foundry_iq = foundry_iq
        self.fabric_iq = fabric_iq
        self.work_iq = work_iq

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        if self.llm and self.fabric_iq:
            return self._run_iq(context)
        return self._run_legacy(context)

    def _run_iq(self, context: dict[str, Any]) -> dict[str, Any]:
        sector = context.get("sector", "Technology")
        sector_ctx = self.fabric_iq.get_sector_context(sector)
        correlations = self.fabric_iq.get_macro_correlations("US_FED_RATE")
        beta = sector_ctx.get("risk_beta", 1.0)
        sensitivity = sector_ctx.get("rate_sensitivity", "medium")

        system_prompt = (
            f"You are a market reaction analyst. Given the macro context and news events, "
            f"predict likely market reaction for {sector}. "
            f"Use sector data: beta={beta}, rate_sensitivity={sensitivity}. "
            f"Structure: immediate reaction, 1-week outlook, key levels to watch."
        )
        user_prompt = (
            f"Sector context: {sector_ctx}\n"
            f"Macro correlations: {correlations}\n"
            f"Macro summary: {context.get('macro_summary', '')}\n"
            f"News events: {context.get('news_events', '')}\n"
            f"Query: {context.get('query', '')}"
        )
        output = self.llm.chat(system_prompt, user_prompt)
        context["market_reaction"] = output

        fabric_entities = [
            sector,
            f"beta:{beta}",
            f"sensitivity:{sensitivity}",
        ] + list(sector_ctx.get("companies", []))

        return agent_result(
            "MarketReactionAgent",
            output,
            ["fabric_iq"],
            fabric_entities=fabric_entities,
        )

    def _run_legacy(self, context: dict[str, Any]) -> dict[str, Any]:
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

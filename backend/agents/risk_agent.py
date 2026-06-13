"""Risk Agent: risk scoring via Fabric IQ thresholds."""
from __future__ import annotations

import logging
from typing import Any

from .base import BaseAgent
from .iq_base import agent_result

logger = logging.getLogger(__name__)


class RiskAgent(BaseAgent):
    """Flags volatility and tail risks using semantic risk thresholds."""

    def __init__(self, llm=None, foundry_iq=None, fabric_iq=None, work_iq=None) -> None:
        super().__init__(name="Risk", role="Flag volatility spikes and tail risks")
        self.llm = llm
        self.foundry_iq = foundry_iq
        self.fabric_iq = fabric_iq
        self.work_iq = work_iq

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        if self.llm and self.fabric_iq:
            return self._run_iq(context)
        return self._run_legacy(context)

    def _run_iq(self, context: dict[str, Any]) -> dict[str, Any]:
        sector_ctx = self.fabric_iq.get_sector_context(context.get("sector", "Technology"))
        sector_beta = sector_ctx.get("risk_beta", 1.0)

        news_text = (context.get("news_events") or "").lower()
        macro_text = (context.get("macro_summary") or "").lower()
        reaction_text = (context.get("market_reaction") or "").lower()

        base = 5.0
        if "bearish" in news_text:
            base += 1.5
        if sector_beta > 1.2:
            base += 1.0
        if "rate hike" in macro_text or "rate hold" in macro_text:
            base += 0.5
        if "positive" in reaction_text or "bullish" in reaction_text:
            base -= 1.5
        risk_score = max(0.0, min(10.0, base))

        threshold = self.fabric_iq.get_risk_threshold(risk_score)
        system_prompt = (
            "You are a risk analyst. Given this financial context, assess the risk profile. "
            f"Risk score computed: {risk_score}/10. Threshold action: {threshold.get('action')}. "
            "Explain: concentration risks, downside scenarios, recommended position sizing."
        )
        user_prompt = (
            f"Query: {context.get('query', '')}\n"
            f"Sector: {context.get('sector', '')}\n"
            f"News: {context.get('news_events', '')[:500]}\n"
            f"Macro: {context.get('macro_summary', '')[:500]}\n"
            f"Market reaction: {context.get('market_reaction', '')[:500]}"
        )
        output = self.llm.chat(system_prompt, user_prompt)
        context["risk_score"] = risk_score
        context["risk_action"] = threshold.get("action")

        return agent_result(
            "RiskAgent",
            output,
            ["fabric_iq"],
            fabric_entities=[
                threshold.get("level", "unknown"),
                threshold.get("action", ""),
                f"score:{risk_score:.1f}",
            ],
        )

    def _run_legacy(self, context: dict[str, Any]) -> dict[str, Any]:
        articles = context.get("articles", [])
        spike = context.get("spike_detected", False)
        spike_direction = context.get("spike_direction")

        flags = []
        if spike and spike_direction == "negative":
            flags.append("Elevated downside risk: negative sentiment spike")
        if spike and spike_direction == "positive":
            flags.append("Crowded positive sentiment: possible short-term overextension")
        if len(articles) > 15:
            flags.append("High news volume: volatility likely")
        neg_count = sum(1 for a in articles if (a.get("sentiment") or "").lower() == "negative")
        if len(articles) and neg_count / len(articles) >= 0.7:
            flags.append("Tail risk: majority negative news — consider hedging")

        finding = {"flags": flags, "spike": spike}
        self._remember(finding)
        return {
            "risk_flags": flags,
            "summary": "; ".join(flags) if flags else "No elevated risk flags.",
        }

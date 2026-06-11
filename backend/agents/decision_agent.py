"""
Decision Agent: synthesizes all agent outputs into a final recommendation.
"""
import logging
import os
from typing import Any, Optional

from .base import BaseAgent

logger = logging.getLogger(__name__)


def _call_llm_debate(agent_summaries: list[str], context: dict) -> Optional[str]:
    """Use Groq or OpenAI (via intelligence.llm) to synthesize agent debate."""
    from intelligence.llm import chat_completion
    prompt = (
        "You are a senior strategist. Given these specialist views, output a single short "
        "paragraph: (1) overall view, (2) key risk, (3) one actionable recommendation. "
        "Be concise.\n\n" + "\n\n".join(agent_summaries)
    )
    return chat_completion(prompt, system_content="", max_tokens=250)


def _rule_decision(context: dict[str, Any]) -> dict[str, Any]:
    outputs = context.get("agent_outputs", {})
    debate = outputs.get("Debate", {}) or {}
    committee = outputs.get("RiskCommittee", {}) or {}
    risk_constraints = committee.get("constraints", {}) or {}
    risk_flags = outputs.get("Risk", {}).get("risk_flags", []) or []
    reaction = outputs.get("MarketReaction", {}).get("historical_reaction", "")
    macro = outputs.get("MacroContext", {}).get("macro_links", []) or []

    action = (debate.get("action") or "HOLD").upper()
    stance = (debate.get("stance") or "neutral").lower()
    confidence_gap = float(debate.get("confidence_gap") or 0.0)
    risk_level = risk_constraints.get("risk_level", "moderate")
    max_size = float(risk_constraints.get("max_position_fraction", 0.5))
    sl = risk_constraints.get("stop_loss_pct", 2.5)
    tp = risk_constraints.get("take_profit_pct", 4.0)

    if risk_level == "high" and action != "HOLD":
        action = "HOLD"
        stance = "neutral"

    headline = f"{action} with {max_size:.0%} max size ({risk_level} risk regime)."
    reasons = []
    if macro:
        reasons.append(f"Macro context: {', '.join(macro[:2])}.")
    if reaction:
        reasons.append(reaction)
    if risk_flags:
        reasons.append(f"Primary risk flags: {'; '.join(risk_flags[:2])}.")

    return {
        "action": action,
        "stance": stance,
        "confidence_gap": round(confidence_gap, 3),
        "risk_level": risk_level,
        "position_size_cap": max_size,
        "stop_loss_pct": sl,
        "take_profit_pct": tp,
        "headline": headline,
        "reasons": reasons,
    }


class DecisionAgent(BaseAgent):
    """Synthesizes News Scout, Macro, Market Reaction, and Risk into a final recommendation."""

    def __init__(self):
        super().__init__(name="Decision", role="Synthesize all agent views into final recommendation")

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        agent_outputs = context.get("agent_outputs", {})
        summaries = []
        for name, out in agent_outputs.items():
            if isinstance(out, dict) and "summary" in out:
                summaries.append(f"{name}: {out['summary']}")
            elif isinstance(out, str):
                summaries.append(f"{name}: {out}")

        # Optional debate via LLM
        recommendation = _call_llm_debate(summaries, context)
        structured = _rule_decision(context)
        if not recommendation:
            recommendation = f"{structured['headline']} " + " ".join(structured["reasons"])

        self._remember(
            {
                "recommendation": recommendation,
                "structured": structured,
                "inputs": list(agent_outputs.keys()),
            }
        )

        return {
            "recommendation": recommendation,
            "summary": recommendation,
            "structured_decision": structured,
        }

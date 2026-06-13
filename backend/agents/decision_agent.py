"""Decision Agent: final synthesis with all three IQ layers."""
from __future__ import annotations

import logging
from typing import Any, Optional

from fintelliops_iq.helpers import format_docs

from .base import BaseAgent
from .iq_base import agent_result

logger = logging.getLogger(__name__)


def _call_llm_debate(agent_summaries: list[str], context: dict) -> Optional[str]:
    from intelligence.llm import chat_completion

    prompt = (
        "You are a senior strategist. Given these specialist views, output a single short "
        "paragraph: (1) overall view, (2) key risk, (3) one actionable recommendation.\n\n"
        + "\n\n".join(agent_summaries)
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
    """Synthesizes all agent views into a final investment briefing."""

    def __init__(self, llm=None, foundry_iq=None, fabric_iq=None, work_iq=None) -> None:
        super().__init__(name="Decision", role="Synthesize all agent views into final recommendation")
        self.llm = llm
        self.foundry_iq = foundry_iq
        self.fabric_iq = fabric_iq
        self.work_iq = work_iq

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        if self.llm and self.foundry_iq and self.fabric_iq and self.work_iq:
            return self._run_iq(context)
        return self._run_legacy(context)

    def _run_iq(self, context: dict[str, Any]) -> dict[str, Any]:
        sector = context.get("sector", "Technology")
        analyst_id = context.get("analyst_id", "ANL-001")

        docs = self.foundry_iq.retrieve(f"{sector} outlook recommendation", top_k=3)
        briefing_time = self.work_iq.get_optimal_briefing_time(analyst_id)
        deliver_now = self.work_iq.should_deliver_briefing(analyst_id)
        team_summary = self.work_iq.get_team_summary()

        all_citations: dict[str, dict] = {}
        for agent_result_data in context.get("agents", {}).values():
            for c in agent_result_data.get("citations", []):
                all_citations[c.get("citation", c.get("source", ""))] = c

        system_prompt = (
            "You are a senior investment decision agent. Synthesise all analysis from the pipeline "
            "into a final briefing. Structure:\n"
            "1. Executive Summary (3 sentences max)\n"
            "2. Key Events (with citations)\n"
            "3. Macro Backdrop\n"
            "4. Market Reaction Outlook\n"
            "5. Risk Assessment (level + recommended action)\n"
            "6. Final Recommendation (Buy / Hold / Reduce / Exit with rationale)\n"
            "7. Next Review Trigger\n"
            "Be concise. Cite sources. Every claim must reference retrieved documents."
        )
        user_prompt = (
            f"Query: {context.get('query', '')}\n"
            f"Sector: {sector}\n"
            f"News events: {context.get('news_events', '')}\n"
            f"Macro: {context.get('macro_summary', '')}\n"
            f"Market reaction: {context.get('market_reaction', '')}\n"
            f"Risk score: {context.get('risk_score', 'N/A')} — action: {context.get('risk_action', '')}\n"
            f"Supporting docs:\n{format_docs(docs)}\n"
            f"All pipeline citations:\n{format_docs(list(all_citations.values()))}\n"
            f"Briefing delivery: {briefing_time}"
        )
        output = self.llm.chat(system_prompt, user_prompt)

        return agent_result(
            "DecisionAgent",
            output,
            ["foundry_iq", "fabric_iq", "work_iq"],
            citations=docs,
            work_signals={
                "briefing_time": briefing_time,
                "deliver_now": deliver_now,
                "team_load": team_summary.get("current_load"),
                "team_recommendation": team_summary.get("recommendation"),
            },
        )

    def _run_legacy(self, context: dict[str, Any]) -> dict[str, Any]:
        agent_outputs = context.get("agent_outputs", {})
        summaries = []
        for name, out in agent_outputs.items():
            if isinstance(out, dict) and "summary" in out:
                summaries.append(f"{name}: {out['summary']}")
            elif isinstance(out, str):
                summaries.append(f"{name}: {out}")

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

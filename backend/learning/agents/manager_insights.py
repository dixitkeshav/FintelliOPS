"""Manager Insights Agent — team-level visibility into certification readiness."""
from __future__ import annotations

from typing import Any

from agents.base import BaseAgent
from learning.iq.fabric_iq import FabricIQ
from learning.iq.work_iq import WorkIQ
from learning.foundry_client import enrich_with_llm


class ManagerInsightsAgent(BaseAgent):
    """Surfaces team progress, risk areas, and readiness summaries."""

    def __init__(self) -> None:
        super().__init__(
            name="ManagerInsights",
            role="Provide team-level certification readiness and risk visibility",
        )
        self.fabric_iq = FabricIQ()
        self.work_iq = WorkIQ()

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        team = context.get("team", "TEAM-A")
        assessment = context.get("assessment") or {}
        team_summary = self.fabric_iq.team_readiness_summary(team)
        team_signals = self.work_iq.get_team_signals(team)

        capacity_risks = []
        for signal in team_signals:
            risk = self.work_iq.compute_capacity_risk(signal["learner_id"])
            if risk.get("risk_level") in ("high", "medium"):
                capacity_risks.append({
                    "learner_id": signal["learner_id"],
                    "risk_level": risk["risk_level"],
                    "reason": risk["reason"],
                })

        insights = {
            "team": team,
            "learner_count": team_summary.get("learner_count", 0),
            "exam_ready_count": team_summary.get("exam_ready_count", 0),
            "average_readiness": team_summary.get("average_readiness", 0),
            "at_risk_learners": team_summary.get("at_risk_learners", []),
            "capacity_constrained": capacity_risks,
            "historical_pass_rate": team_summary.get("pass_rate_historical", 0.68),
            "latest_assessment_passed": assessment.get("passed"),
            "privacy_note": "Aggregated metrics only; individual scores masked in manager view.",
        }

        llm_summary = enrich_with_llm(
            system_prompt=(
                "You are a Manager Insights Agent. Write a 3-sentence executive summary "
                "for a team manager about certification readiness, risks, and recommended actions. "
                "Do not expose sensitive personal data."
            ),
            user_prompt=f"Team insights: {insights}",
            fallback=(
                f"Team {team}: {insights['exam_ready_count']}/{insights['learner_count']} exam-ready, "
                f"avg readiness {insights['average_readiness']}%. "
                f"{len(capacity_risks)} capacity-constrained learners. "
                f"Historical pass rate {int(insights['historical_pass_rate'] * 100)}%."
            ),
        )

        self._remember({"team": team, "insights": insights})
        return {
            "manager_insights": insights,
            "iq_layers": ["Fabric IQ", "Work IQ"],
            "summary": llm_summary,
        }

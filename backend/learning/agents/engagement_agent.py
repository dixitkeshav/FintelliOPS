"""Engagement Agent — keeps learners on track with work-context-aware reminders."""
from __future__ import annotations

from typing import Any

from agents.base import BaseAgent
from learning.iq.work_iq import WorkIQ
from learning.foundry_client import enrich_with_llm


class EngagementAgent(BaseAgent):
    """Adapts reminders to work patterns using Work IQ signals."""

    def __init__(self) -> None:
        super().__init__(
            name="EngagementAgent",
            role="Keep learners progressing with personalised, work-context-aware engagement",
        )
        self.work_iq = WorkIQ()

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        learner_id = context.get("learner_id", "L-1001")
        study_plan = context.get("study_plan") or {}
        work_ctx = self.work_iq.engagement_context(learner_id)
        capacity = work_ctx.get("capacity_risk", {})

        reminders = []
        for window in capacity.get("recommended_reminder_windows", []):
            reminders.append({
                "window": window,
                "message": f"Study block: {study_plan.get('daily_target_hours', 1.5)}h on "
                f"{study_plan.get('certification', 'certification')} skills",
                "channel": "Teams nudge (synthetic)",
            })

        escalation = None
        if capacity.get("risk_level") == "high":
            escalation = {
                "action": "Manager check-in suggested",
                "reason": capacity.get("reason"),
                "privacy_note": "Aggregated team view only; no raw calendar data exposed.",
            }

        engagement = {
            "learner_id": learner_id,
            "reminders": reminders,
            "preferred_slot": capacity.get("preferred_learning_slot"),
            "capacity_risk": capacity.get("risk_level"),
            "escalation": escalation,
        }

        llm_summary = enrich_with_llm(
            system_prompt=(
                "You are an Engagement Agent. Write a supportive 2-sentence engagement message "
                "that respects work context and avoids disruptive timing."
            ),
            user_prompt=f"Engagement plan: {engagement}. Work context: {work_ctx}",
            fallback=(
                f"Scheduled {len(reminders)} reminders during focus windows "
                f"({capacity.get('preferred_learning_slot', 'Morning')}). "
                + (f"Escalation: {escalation['action']}." if escalation else "On track.")
            ),
        )

        self._remember({"learner_id": learner_id, "engagement": engagement})
        return {
            "engagement": engagement,
            "work_context": work_ctx,
            "iq_layers": ["Work IQ"],
            "summary": llm_summary,
        }

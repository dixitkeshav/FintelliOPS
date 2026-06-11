"""Study Plan Generator — converts learning content into a practical schedule."""
from __future__ import annotations

from typing import Any

from agents.base import BaseAgent
from learning.iq.fabric_iq import FabricIQ
from learning.iq.work_iq import WorkIQ
from learning.foundry_client import enrich_with_llm


class StudyPlanGeneratorAgent(BaseAgent):
    """Produces capacity-aware study schedules using Fabric IQ and Work IQ."""

    def __init__(self) -> None:
        super().__init__(
            name="StudyPlanGenerator",
            role="Convert learning paths into practical, workload-aware study schedules",
        )
        self.fabric_iq = FabricIQ()
        self.work_iq = WorkIQ()

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        learner_id = context.get("learner_id", "L-1001")
        learning_path = context.get("learning_path") or {}
        semantics = self.fabric_iq.study_plan_semantics(learner_id)
        work_ctx = self.work_iq.engagement_context(learner_id)
        capacity = work_ctx.get("capacity_risk", {})

        schedule = []
        for milestone in semantics.get("milestones", []):
            schedule.append({
                "week": milestone["week"],
                "focus_skill": milestone["skill"],
                "planned_hours": milestone["hours"],
                "checkpoint": milestone["checkpoint"],
                "suggested_slot": capacity.get("preferred_learning_slot", "Morning"),
            })

        study_plan = {
            "learner_id": learner_id,
            "certification": semantics.get("certification"),
            "remaining_hours": semantics.get("remaining_hours", 0),
            "daily_target_hours": semantics.get("recommended_daily_hours", 1.5),
            "schedule": schedule,
            "readiness_score": semantics.get("readiness_score", 0),
            "capacity_risk": capacity.get("risk_level", "unknown"),
        }

        llm_summary = enrich_with_llm(
            system_prompt=(
                "You are a Study Plan Generator. Summarise the study plan in 2-3 sentences, "
                "mentioning milestones, daily hours, and how workload signals shaped scheduling."
            ),
            user_prompt=(
                f"Plan for {learner_id}: {study_plan}. "
                f"Capacity risk: {capacity.get('risk_level')}. "
                f"Skill gaps: {semantics.get('skill_gaps', [])}"
            ),
            fallback=(
                f"{len(schedule)}-week plan with {study_plan['daily_target_hours']}h/day target. "
                f"Capacity risk: {capacity.get('risk_level', 'unknown')}. "
                f"Readiness: {semantics.get('readiness_score', 0)}%."
            ),
        )

        self._remember({"learner_id": learner_id, "plan": study_plan})
        return {
            "study_plan": study_plan,
            "skill_gaps": semantics.get("skill_gaps", []),
            "iq_layers": ["Fabric IQ", "Work IQ"],
            "summary": llm_summary,
        }

"""Study Plan Generator — capacity-aware study schedules."""
from __future__ import annotations

from typing import Any

from learning.foundry_client import FoundryClient
from learning.iq.fabric_iq import FabricIQClient
from learning.iq.foundry_iq import FoundryIQClient
from learning.iq.work_iq import WorkIQClient


class StudyPlanGeneratorAgent:
    def __init__(
        self,
        foundry_client: FoundryClient,
        foundry_iq: FoundryIQClient,
        fabric_iq: FabricIQClient,
        work_iq: WorkIQClient,
    ) -> None:
        self.foundry_client = foundry_client
        self.foundry_iq = foundry_iq
        self.fabric_iq = fabric_iq
        self.work_iq = work_iq

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        learner = context["learner"]
        cert_id = context["certification"]
        employee_id = context["employee_id"]
        current_score = learner.get("practice_score_avg", 0)

        hours = self.fabric_iq.get_study_hours_recommendation(cert_id, current_score)
        slot = self.work_iq.get_optimal_study_slot(employee_id)
        capacity = self.work_iq.get_team_capacity_summary()

        system_prompt = "You are a Study Plan Generator for enterprise certification programmes."
        user_prompt = (
            f"Create a study schedule. Available focus time: {slot}. "
            f"Recommended hours: {hours}. Adjust for team capacity: {capacity}."
        )
        output = self.foundry_client.chat(system_prompt, user_prompt)

        return {
            "agent_name": "StudyPlanGeneratorAgent",
            "output": output,
            "iq_layers_used": ["fabric_iq", "work_iq"],
            "citations": [],
            "fabric_entities": [cert_id, f"{hours}h recommended"],
            "work_signals": {"slot": slot, "capacity": capacity},
            "completed": True,
            "error": None,
        }

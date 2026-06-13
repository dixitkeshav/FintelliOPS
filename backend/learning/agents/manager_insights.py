"""Manager Insights — team readiness and risk areas."""
from __future__ import annotations

from typing import Any

from learning.foundry_client import FoundryClient
from learning.iq.fabric_iq import FabricIQClient
from learning.iq.foundry_iq import FoundryIQClient
from learning.iq.work_iq import WorkIQClient


class ManagerInsightsAgent:
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
        team_id = context["team_id"]
        readiness = self.fabric_iq.get_team_readiness(team_id)
        capacity = self.work_iq.get_team_capacity_summary()
        citations = self.foundry_iq.retrieve(
            "team performance certification completion patterns"
        )

        docs_text = "\n\n".join(
            f"[{c['citation']}] {c['content'][:300]}" for c in citations
        )
        system_prompt = "You are a Manager Insights agent summarising team certification readiness."
        user_prompt = (
            f"Summarize team readiness for manager. "
            f"Team stats: {readiness}. Capacity: {capacity}. "
            f"Highlight risk areas and recommendations.\n\n"
            f"Reference documents:\n{docs_text}"
        )
        output = self.foundry_client.chat(system_prompt, user_prompt)

        fabric_entities = [
            f"team:{readiness['team_id']}",
            f"avg_score:{readiness['avg_practice_score']}",
            f"ready:{readiness['ready_count']}/{readiness['total_count']}",
        ] + readiness.get("risk_areas", [])

        return {
            "agent_name": "ManagerInsightsAgent",
            "output": output,
            "iq_layers_used": ["fabric_iq", "work_iq", "foundry_iq"],
            "citations": citations,
            "fabric_entities": fabric_entities,
            "work_signals": capacity,
            "completed": True,
            "error": None,
        }

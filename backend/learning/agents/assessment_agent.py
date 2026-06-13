"""Assessment Agent — grounded practice questions with citations."""
from __future__ import annotations

from typing import Any

from learning.foundry_client import FoundryClient
from learning.iq.fabric_iq import FabricIQClient
from learning.iq.foundry_iq import FoundryIQClient
from learning.iq.work_iq import WorkIQClient


class AssessmentAgent:
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
        learner_id = context["learner_id"]
        cert_id = context["certification"]
        topics = context.get("topics", [])
        skill_area = topics[0] if topics else cert_id

        citations = self.foundry_iq.retrieve(
            f"{cert_id} practice questions exam topics {skill_area}"
        )
        skill_gaps = self.fabric_iq.get_skill_gaps(learner_id, cert_id)

        docs_text = "\n\n".join(
            f"[{c['citation']}] {c['content'][:400]}" for c in citations
        )
        system_prompt = (
            "You are an Assessment Agent. Generate practice questions grounded in documents."
        )
        user_prompt = (
            f"Generate 3 practice questions for {cert_id}. "
            f"Base questions ONLY on the following knowledge documents. "
            f"For each question provide: question text, 4 options, correct answer, citation.\n"
            f"Skill gaps to target: {', '.join(skill_gaps) or 'none'}\n\n"
            f"Documents:\n{docs_text}"
        )
        output = self.foundry_client.chat(system_prompt, user_prompt)

        return {
            "agent_name": "AssessmentAgent",
            "output": output,
            "iq_layers_used": ["foundry_iq", "fabric_iq"],
            "citations": citations,
            "fabric_entities": skill_gaps,
            "work_signals": {},
            "completed": True,
            "error": None,
        }

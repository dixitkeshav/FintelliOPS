"""Learning Path Curator — maps certification goals to grounded learning content."""
from __future__ import annotations

from typing import Any

from django.conf import settings

from learning.foundry_client import FoundryClient
from learning.iq.fabric_iq import FabricIQClient
from learning.iq.foundry_iq import FoundryIQClient
from learning.iq.work_iq import WorkIQClient
from learning.mcp_learn import augment_with_learn


class LearningPathCuratorAgent:
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
        role = context["role"]
        topics = context.get("topics", [])
        cert_id = context["certification"]
        learner_id = context["learner_id"]

        query = f"{role} certification learning path {' '.join(topics)}"
        citations = self.foundry_iq.retrieve(query)
        if getattr(settings, "MCP_LEARN_ENABLED", False):
            augment_with_learn(query, citations)

        cert_info = self.fabric_iq.get_certification_for_role(role)
        skill_gaps = self.fabric_iq.get_skill_gaps(learner_id, cert_id)

        docs_text = "\n\n".join(
            f"[{c['citation']}] {c['content'][:400]}" for c in citations
        )
        system_prompt = (
            "You are a Learning Path Curator. Based ONLY on the retrieved knowledge documents "
            "below, suggest a learning path. You MUST cite document sources for every "
            "recommendation. Never suggest content not in the documents."
        )
        user_prompt = (
            f"Learner role: {role}\n"
            f"Target certification: {cert_id}\n"
            f"Topics: {', '.join(topics)}\n"
            f"Skill gaps: {', '.join(skill_gaps) or 'none'}\n"
            f"Certification requirements: {cert_info}\n\n"
            f"Retrieved documents:\n{docs_text}"
        )

        output = self.foundry_client.chat(system_prompt, user_prompt)

        return {
            "agent_name": "LearningPathCuratorAgent",
            "output": output,
            "iq_layers_used": ["foundry_iq", "fabric_iq"],
            "citations": citations,
            "fabric_entities": [cert_info.get("cert_id", cert_id)] + skill_gaps,
            "work_signals": {},
            "completed": True,
            "error": None,
        }

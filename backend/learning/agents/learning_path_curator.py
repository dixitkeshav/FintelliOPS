"""Learning Path Curator — maps certification goals to grounded learning content."""
from __future__ import annotations

from typing import Any

from agents.base import BaseAgent
from learning.iq.foundry_iq import FoundryIQ
from learning.iq.fabric_iq import FabricIQ
from learning.foundry_client import enrich_with_llm
from learning.mcp_learn import augment_with_learn


class LearningPathCuratorAgent(BaseAgent):
    """Suggests relevant learning paths using Foundry IQ and Fabric IQ semantics."""

    def __init__(self) -> None:
        super().__init__(
            name="LearningPathCurator",
            role="Map certification targets to cited skills and resources",
        )
        self.foundry_iq = FoundryIQ()
        self.fabric_iq = FabricIQ()

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        learner_id = context.get("learner_id", "L-1001")
        topics = context.get("topics", [])
        learner = self.fabric_iq.get_learner(learner_id)
        certification = context.get("certification") or (learner or {}).get("certification", "AZ-204")
        role = (learner or {}).get("role", "Cloud Engineer")

        role_map = self.fabric_iq.get_role_mapping(role)
        cert_meta = self.fabric_iq.get_certification(certification)
        query = f"{certification} {role} {' '.join(topics)} certification study path"
        grounded = self.foundry_iq.grounded_answer(query)
        mcp_augmented = augment_with_learn(query, grounded.get("sources", []))

        learning_path = {
            "certification": certification,
            "role": role,
            "primary_skills": (cert_meta or {}).get("skills", []),
            "secondary_certification": (role_map or {}).get("secondary_certification"),
            "recommended_hours": (cert_meta or {}).get("recommended_hours", 20),
            "cited_resources": grounded.get("sources", []),
            "citations": grounded.get("citations", []),
            "mcp_learn": mcp_augmented,
        }

        llm_summary = enrich_with_llm(
            system_prompt=(
                "You are a Learning Path Curator for enterprise certification programmes. "
                "Summarise the learning path in 2-3 sentences. Always mention that recommendations "
                "are grounded in approved organisational knowledge with citations."
            ),
            user_prompt=(
                f"Learner {learner_id} ({role}) targeting {certification}. "
                f"Topics: {topics}. Grounded context: {grounded.get('answer', '')[:500]}"
            ),
            fallback=(
                f"Curated path for {certification} aligned to {role} role. "
                f"Focus on {(cert_meta or {}).get('skills', ['core skills'])[:3]}. "
                f"Grounded in {len(grounded.get('citations', []))} approved sources."
            ),
        )

        self._remember({"learner_id": learner_id, "path": learning_path})
        return {
            "learning_path": learning_path,
            "grounded": grounded.get("grounded", False),
            "iq_layers": ["Foundry IQ", "Fabric IQ"],
            "summary": llm_summary,
        }

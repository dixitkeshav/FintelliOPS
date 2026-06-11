"""Assessment Agent — evaluates readiness with grounded, cited questions."""
from __future__ import annotations

import random
from typing import Any

from agents.base import BaseAgent
from learning.iq.foundry_iq import FoundryIQ
from learning.iq.fabric_iq import FabricIQ
from learning.foundry_client import enrich_with_llm


class AssessmentAgent(BaseAgent):
    """Generates grounded assessments and scores readiness."""

    def __init__(self) -> None:
        super().__init__(
            name="AssessmentAgent",
            role="Evaluate learner readiness with grounded, cited practice questions",
        )
        self.foundry_iq = FoundryIQ()
        self.fabric_iq = FabricIQ()

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        learner_id = context.get("learner_id", "L-1001")
        learner = self.fabric_iq.get_learner(learner_id) or {}
        certification = learner.get("certification", "AZ-204")
        cert_meta = self.fabric_iq.get_certification(certification) or {}
        skills = cert_meta.get("skills", ["fundamentals"])
        skill = random.choice(skills)

        grounded_ctx = self.foundry_iq.generate_assessment_context(certification, skill)
        gaps = self.fabric_iq.compute_skill_gaps(learner_id)

        questions = []
        for i, topic in enumerate(grounded_ctx.get("question_seed_topics", skills)[:3]):
            citation = (
                grounded_ctx["grounded_context"]["citations"][0]
                if grounded_ctx["grounded_context"].get("citations")
                else "[engineering_certification_guide.md]"
            )
            questions.append({
                "id": f"Q-{i + 1}",
                "skill": skill,
                "question": f"Explain how {topic} applies to {certification} scenarios in a production Azure environment.",
                "citation": citation,
                "type": "short_answer",
            })

        practice_score = learner.get("practice_score_avg", 70)
        threshold = cert_meta.get("pass_threshold", 75)
        passed = practice_score >= threshold and gaps.get("exam_ready", False)

        assessment = {
            "learner_id": learner_id,
            "certification": certification,
            "questions": questions,
            "practice_score_avg": practice_score,
            "pass_threshold": threshold,
            "passed": passed,
            "readiness_score": gaps.get("readiness_score", 0),
            "next_step": (
                f"Recommend advancing to {(self.fabric_iq.get_role_mapping(learner.get('role', '')) or {}).get('secondary_certification') or 'next module'}"
                if passed
                else "Loop back to study preparation — focus on skill gaps"
            ),
        }

        llm_summary = enrich_with_llm(
            system_prompt=(
                "You are an Assessment Agent. Summarise assessment results in 2 sentences. "
                "Mention grounded questions, score vs threshold, and pass/fail outcome."
            ),
            user_prompt=f"Assessment: {assessment}. Gaps: {gaps.get('skill_gaps', [])}",
            fallback=(
                f"Generated {len(questions)} grounded questions for {certification}. "
                f"Practice score {practice_score}% vs {threshold}% threshold — "
                f"{'PASS' if passed else 'needs more preparation'}."
            ),
        )

        self._remember({"learner_id": learner_id, "assessment": assessment})
        return {
            "assessment": assessment,
            "skill_gaps": gaps.get("skill_gaps", []),
            "grounded_context": grounded_ctx,
            "iq_layers": ["Foundry IQ", "Fabric IQ"],
            "summary": llm_summary,
        }

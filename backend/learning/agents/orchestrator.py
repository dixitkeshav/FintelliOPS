"""Learning certification multi-agent orchestrator."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from learning.evaluation import evaluate_pipeline
from learning.foundry_client import FoundryClient
from learning.iq.fabric_iq import FabricIQClient
from learning.iq.foundry_iq import FoundryIQClient
from learning.iq.work_iq import WorkIQClient
from learning.learners import load_learner

from .assessment_agent import AssessmentAgent
from .engagement_agent import EngagementAgent
from .learning_path_curator import LearningPathCuratorAgent
from .manager_insights import ManagerInsightsAgent
from .study_plan_generator import StudyPlanGeneratorAgent

logger = logging.getLogger(__name__)


class LearningOrchestrator:
    def __init__(self) -> None:
        self.foundry_client = FoundryClient()
        self.foundry_iq = FoundryIQClient()
        self.fabric_iq = FabricIQClient()
        self.work_iq = WorkIQClient()
        self.agents = [
            LearningPathCuratorAgent(
                self.foundry_client, self.foundry_iq, self.fabric_iq, self.work_iq
            ),
            StudyPlanGeneratorAgent(
                self.foundry_client, self.foundry_iq, self.fabric_iq, self.work_iq
            ),
            EngagementAgent(
                self.foundry_client, self.foundry_iq, self.fabric_iq, self.work_iq
            ),
            AssessmentAgent(
                self.foundry_client, self.foundry_iq, self.fabric_iq, self.work_iq
            ),
            ManagerInsightsAgent(
                self.foundry_client, self.foundry_iq, self.fabric_iq, self.work_iq
            ),
        ]

    def run(self, learner_id: str, team_id: str, topics: list[str]) -> dict[str, Any]:
        learner = load_learner(learner_id)
        if not learner:
            raise ValueError(f"Unknown learner_id: {learner_id}")

        context: dict[str, Any] = {
            "learner_id": learner_id,
            "team_id": team_id,
            "topics": topics,
            "pipeline_start": datetime.now(timezone.utc).isoformat(),
            "agents": {},
        }

        context["learner"] = learner
        context["role"] = learner["role"]
        context["certification"] = learner["certification"]
        context["employee_id"] = f"EMP-{learner_id.split('-')[1]}"

        for agent in self.agents:
            agent_name = agent.__class__.__name__
            try:
                result = agent.run(context)
                context["agents"][agent_name] = result
                context.update(result)
            except Exception as exc:
                context["agents"][agent_name] = {
                    "completed": False,
                    "error": str(exc),
                    "agent_name": agent_name,
                    "output": "",
                    "iq_layers_used": [],
                    "citations": [],
                    "fabric_entities": [],
                    "work_signals": {},
                }
                logger.error("Agent %s failed: %s", agent_name, exc)

        scores = [learner.get("practice_score_avg", 0)]
        avg_score = sum(scores) / len(scores) if scores else 0
        context["recommendation"] = (
            "pass → next certification step"
            if avg_score >= 75
            else "loop back → continue preparation"
        )

        all_citations: list[dict[str, Any]] = []
        for agent_result in context["agents"].values():
            all_citations.extend(agent_result.get("citations", []))
        context["all_citations"] = list(
            {c.get("citation", ""): c for c in all_citations if c}.values()
        )

        context["pipeline_end"] = datetime.now(timezone.utc).isoformat()
        context["pipeline_completed"] = True
        context["evaluation"] = evaluate_pipeline(context)

        return context

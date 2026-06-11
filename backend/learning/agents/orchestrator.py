"""
Learning orchestrator — coordinates the enterprise certification multi-agent workflow.

Baseline flow:
  Learner request → Learning Path Curator → Study Plan Generator →
  Engagement Agent → Assessment Agent → Manager Insights → next step or loop back
"""
from __future__ import annotations

import logging
import time
from typing import Any

from .learning_path_curator import LearningPathCuratorAgent
from .study_plan_generator import StudyPlanGeneratorAgent
from .engagement_agent import EngagementAgent
from .assessment_agent import AssessmentAgent
from .manager_insights import ManagerInsightsAgent
from learning.foundry_client import get_foundry_status
from learning.mcp_learn import is_mcp_available

logger = logging.getLogger(__name__)

LEARNING_PIPELINE_STEPS = [
    ("intake", "Learner Intake", "Parse learner goals, role, and certification target"),
    ("learning_path_curator", "Learning Path Curator", "Grounded learning path via Foundry IQ + Fabric IQ"),
    ("study_plan_generator", "Study Plan Generator", "Capacity-aware schedule via Fabric IQ + Work IQ"),
    ("engagement_agent", "Engagement Agent", "Work-context reminders via Work IQ"),
    ("assessment_agent", "Assessment Agent", "Grounded assessment via Foundry IQ + Fabric IQ"),
    ("manager_insights", "Manager Insights", "Team readiness summary via Fabric IQ + Work IQ"),
    ("recommendation", "Next Step", "Advance certification or loop to preparation"),
]


class LearningOrchestrator:
    """Top-level orchestrator for the enterprise learning certification workflow."""

    def __init__(self) -> None:
        self.curator = LearningPathCuratorAgent()
        self.planner = StudyPlanGeneratorAgent()
        self.engagement = EngagementAgent()
        self.assessment = AssessmentAgent()
        self.manager = ManagerInsightsAgent()

    def run(
        self,
        learner_id: str = "L-1001",
        topics: list[str] | None = None,
        team: str = "TEAM-A",
        certification: str | None = None,
    ) -> dict[str, Any]:
        pipeline: list[dict[str, Any]] = []
        topics = topics or ["Azure fundamentals", "Exam preparation"]

        def record(step_id: str, label: str, status: str, summary: str = "", ms: float = 0) -> None:
            pipeline.append({
                "id": step_id,
                "label": label,
                "status": status,
                "summary": summary,
                "duration_ms": round(ms, 1),
            })

        ctx: dict[str, Any] = {
            "learner_id": learner_id,
            "topics": topics,
            "team": team,
            "certification": certification,
        }

        record(
            "intake",
            "Learner Intake",
            "completed",
            f"Learner {learner_id} targeting certification prep. Topics: {', '.join(topics)}.",
        )

        t0 = time.perf_counter()
        curator_out = self.curator.run(ctx)
        record(
            "learning_path_curator",
            "Learning Path Curator",
            "completed",
            curator_out.get("summary", ""),
            (time.perf_counter() - t0) * 1000,
        )
        ctx["learning_path"] = curator_out.get("learning_path", {})
        ctx["agent_outputs"] = {"LearningPathCurator": curator_out}

        t0 = time.perf_counter()
        planner_out = self.planner.run(ctx)
        record(
            "study_plan_generator",
            "Study Plan Generator",
            "completed",
            planner_out.get("summary", ""),
            (time.perf_counter() - t0) * 1000,
        )
        ctx["study_plan"] = planner_out.get("study_plan", {})
        ctx["agent_outputs"]["StudyPlanGenerator"] = planner_out

        t0 = time.perf_counter()
        engagement_out = self.engagement.run(ctx)
        record(
            "engagement_agent",
            "Engagement Agent",
            "completed",
            engagement_out.get("summary", ""),
            (time.perf_counter() - t0) * 1000,
        )
        ctx["agent_outputs"]["EngagementAgent"] = engagement_out

        t0 = time.perf_counter()
        assessment_out = self.assessment.run(ctx)
        record(
            "assessment_agent",
            "Assessment Agent",
            "completed",
            assessment_out.get("summary", ""),
            (time.perf_counter() - t0) * 1000,
        )
        ctx["assessment"] = assessment_out.get("assessment", {})
        ctx["agent_outputs"]["AssessmentAgent"] = assessment_out

        t0 = time.perf_counter()
        manager_out = self.manager.run(ctx)
        record(
            "manager_insights",
            "Manager Insights",
            "completed",
            manager_out.get("summary", ""),
            (time.perf_counter() - t0) * 1000,
        )
        ctx["agent_outputs"]["ManagerInsights"] = manager_out

        passed = ctx["assessment"].get("passed", False)
        recommendation = (
            ctx["assessment"].get("next_step", "Continue preparation")
            if passed
            else "Loop back to study preparation — review skill gaps and adjust schedule"
        )
        record("recommendation", "Next Step", "completed", recommendation)

        return {
            "learner_id": learner_id,
            "team": team,
            "topics": topics,
            "learning_path_curator": curator_out,
            "study_plan_generator": planner_out,
            "engagement_agent": engagement_out,
            "assessment_agent": assessment_out,
            "manager_insights": manager_out,
            "recommendation": recommendation,
            "exam_ready": passed,
            "pipeline": pipeline,
            "iq_layers": {
                "work_iq": True,
                "foundry_iq": True,
                "fabric_iq": True,
            },
            "foundry": get_foundry_status(),
            "mcp_learn": {"enabled": is_mcp_available()},
            "data_notice": "Synthetic demo data only — no real PII or customer data.",
        }

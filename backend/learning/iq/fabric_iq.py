"""
Fabric IQ — semantic business layer (synthetic ontology demo).

In production, this would use Microsoft Fabric IQ ontology to model
employees, roles, certifications, skill gaps, and readiness thresholds.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class FabricIQ:
    """Semantic layer for certification, role, skill gap, and readiness reasoning."""

    def __init__(self) -> None:
        with open(DATA_DIR / "fabric_semantic_model.json", encoding="utf-8") as f:
            self._model = json.load(f)
        with open(DATA_DIR / "learner_performance.json", encoding="utf-8") as f:
            self._learners = json.load(f)

    def get_certification(self, cert_id: str) -> dict[str, Any] | None:
        for cert in self._model.get("certifications", []):
            if cert["id"] == cert_id:
                return cert
        return None

    def get_role_mapping(self, role_name: str) -> dict[str, Any] | None:
        for role in self._model.get("roles", []):
            if role["name"].lower() == role_name.lower():
                return role
        return None

    def get_learner(self, learner_id: str) -> dict[str, Any] | None:
        for learner in self._learners:
            if learner["learner_id"] == learner_id:
                return dict(learner)
        return None

    def compute_skill_gaps(self, learner_id: str) -> dict[str, Any]:
        learner = self.get_learner(learner_id)
        if not learner:
            return {"gaps": [], "readiness_score": 0}

        cert = self.get_certification(learner["certification"])
        if not cert:
            return {"gaps": ["Unknown certification"], "readiness_score": 0}

        threshold = cert.get("pass_threshold", 75)
        practice = learner.get("practice_score_avg", 0)
        hours = learner.get("hours_studied", 0)
        recommended = cert.get("recommended_hours", 20)
        rules = self._model.get("rules", {})

        gaps: list[str] = []
        if practice < threshold:
            gaps.append(f"Practice score {practice}% below {threshold}% threshold")
        if hours < recommended:
            gaps.append(f"Study hours {hours} below recommended {recommended}")
        if practice < rules.get("min_practice_score_for_readiness", 75):
            gaps.append("Increase weekly practice assessments")

        hours_factor = min(hours / recommended, 1.0) * 40
        practice_factor = min(practice / threshold, 1.0) * 60
        readiness = round(hours_factor + practice_factor)

        return {
            "learner_id": learner_id,
            "certification": learner["certification"],
            "role": learner["role"],
            "skill_gaps": gaps,
            "readiness_score": readiness,
            "exam_ready": readiness >= 75 and not gaps,
            "required_skills": cert.get("skills", []),
            "layer": "Fabric IQ",
        }

    def team_readiness_summary(self, team: str | None = None) -> dict[str, Any]:
        from .work_iq import WorkIQ

        work = WorkIQ()
        learners = self._learners
        if team:
            team_learner_ids = {
                s["learner_id"] for s in work.get_team_signals(team)
            }
            learners = [l for l in learners if l["learner_id"] in team_learner_ids]

        summaries = [self.compute_skill_gaps(l["learner_id"]) for l in learners]
        ready = sum(1 for s in summaries if s.get("exam_ready"))
        avg_readiness = round(
            sum(s.get("readiness_score", 0) for s in summaries) / max(len(summaries), 1)
        )
        at_risk = [
            s["learner_id"]
            for s in summaries
            if s.get("readiness_score", 0) < 60
        ]

        return {
            "team": team or "ALL",
            "learner_count": len(summaries),
            "exam_ready_count": ready,
            "average_readiness": avg_readiness,
            "at_risk_learners": at_risk,
            "pass_rate_historical": 0.68,
            "layer": "Fabric IQ",
        }

    def study_plan_semantics(self, learner_id: str) -> dict[str, Any]:
        gaps = self.compute_skill_gaps(learner_id)
        cert = self.get_certification(gaps.get("certification", ""))
        learner = self.get_learner(learner_id)
        if not cert or not learner:
            return gaps

        remaining_hours = max(
            0,
            cert.get("recommended_hours", 20) - learner.get("hours_studied", 0),
        )
        milestones = []
        skills = cert.get("skills", [])
        per_skill = max(1, remaining_hours // max(len(skills), 1))
        for i, skill in enumerate(skills):
            milestones.append({
                "week": i + 1,
                "skill": skill,
                "hours": per_skill,
                "checkpoint": f"Practice assessment on {skill}",
            })

        return {
            **gaps,
            "remaining_hours": remaining_hours,
            "milestones": milestones,
            "recommended_daily_hours": round(remaining_hours / max(len(milestones), 1) / 5, 1),
        }

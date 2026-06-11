"""
Lightweight evaluation harness for the learning certification agents.

Run: PYTHONPATH=backend python3 -m learning.evaluation
"""
from __future__ import annotations

import json
from pathlib import Path

from learning.agents.orchestrator import LearningOrchestrator

DATA_DIR = Path(__file__).resolve().parent / "data"


def run_evaluations() -> dict:
    with open(DATA_DIR / "learner_performance.json", encoding="utf-8") as f:
        learners = json.load(f)

    orchestrator = LearningOrchestrator()
    results = []
    passed_checks = 0
    total_checks = 0

    for learner in learners:
        out = orchestrator.run(
            learner_id=learner["learner_id"],
            team="TEAM-A" if learner["learner_id"] in ("L-1001", "L-1002") else "TEAM-B",
        )
        checks = {
            "has_pipeline": len(out.get("pipeline", [])) >= 6,
            "has_citations": bool(
                out.get("learning_path_curator", {}).get("learning_path", {}).get("citations")
            ),
            "has_assessment": bool(out.get("assessment_agent", {}).get("assessment", {}).get("questions")),
            "has_manager_insights": bool(out.get("manager_insights", {}).get("manager_insights")),
            "iq_layers_active": all(out.get("iq_layers", {}).values()),
        }
        score = sum(checks.values()) / len(checks)
        passed_checks += sum(checks.values())
        total_checks += len(checks)
        results.append({
            "learner_id": learner["learner_id"],
            "checks": checks,
            "score": round(score * 100),
            "exam_ready": out.get("exam_ready"),
        })

    return {
        "learner_count": len(results),
        "aggregate_pass_rate": round(passed_checks / max(total_checks, 1) * 100, 1),
        "results": results,
    }


if __name__ == "__main__":
    report = run_evaluations()
    print(json.dumps(report, indent=2))

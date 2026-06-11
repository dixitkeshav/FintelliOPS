"""
Work IQ — organisational work-context layer (synthetic demo signals).

In production, this would integrate with Microsoft 365 Copilot Work IQ
to personalise engagement based on meetings, focus time, and collaboration patterns.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class WorkIQ:
    """Provides work-context signals for engagement and scheduling agents."""

    def __init__(self) -> None:
        self._signals = self._load_signals()
        self._workload_doc = self._load_doc("workload_insights.md")

    def _load_signals(self) -> list[dict[str, Any]]:
        path = DATA_DIR / "work_signals.json"
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def _load_doc(self, name: str) -> str:
        path = DATA_DIR / "documents" / name
        return path.read_text(encoding="utf-8")

    def get_learner_signals(self, learner_id: str) -> dict[str, Any] | None:
        for row in self._signals:
            if row.get("learner_id") == learner_id:
                return dict(row)
        return None

    def get_team_signals(self, team: str) -> list[dict[str, Any]]:
        return [s for s in self._signals if s.get("team") == team]

    def compute_capacity_risk(self, learner_id: str) -> dict[str, Any]:
        signals = self.get_learner_signals(learner_id)
        if not signals:
            return {"risk_level": "unknown", "reason": "No work signals found."}

        meetings = signals.get("meeting_hours_per_week", 0)
        focus = signals.get("focus_hours_per_week", 0)
        preferred = signals.get("preferred_learning_slot", "Morning")

        if meetings > 20 or focus < 10:
            risk = "high"
            reason = (
                f"High meeting load ({meetings}h/wk) and limited focus time ({focus}h/wk). "
                "Schedule short study blocks during preferred slot."
            )
        elif meetings > 18 or focus < 15:
            risk = "medium"
            reason = f"Moderate capacity constraints. Prefer {preferred.lower()} study windows."
        else:
            risk = "low"
            reason = f"Good capacity for learning. {preferred} slots recommended."

        return {
            "risk_level": risk,
            "reason": reason,
            "meeting_hours_per_week": meetings,
            "focus_hours_per_week": focus,
            "preferred_learning_slot": preferred,
            "recommended_reminder_windows": self._reminder_windows(preferred, meetings),
        }

    def _reminder_windows(self, preferred: str, meetings: int) -> list[str]:
        base = {
            "Morning": ["08:00–09:00", "11:30–12:00"],
            "Afternoon": ["13:00–14:00", "16:30–17:00"],
            "Evening": ["18:00–19:00", "20:00–21:00"],
        }
        windows = base.get(preferred, base["Morning"])
        if meetings > 20:
            return [w for w in windows if "08:00" in w or "18:00" in w or "20:00" in w][:2]
        return windows

    def engagement_context(self, learner_id: str) -> dict[str, Any]:
        signals = self.get_learner_signals(learner_id) or {}
        capacity = self.compute_capacity_risk(learner_id)
        return {
            "layer": "Work IQ",
            "learner_id": learner_id,
            "employee_id": signals.get("employee_id"),
            "team": signals.get("team"),
            "capacity_risk": capacity,
            "insights_excerpt": self._workload_doc[:400] + "...",
        }

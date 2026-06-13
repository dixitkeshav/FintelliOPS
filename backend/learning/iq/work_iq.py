"""
Work IQ — Work context and organisational signals layer.

DEMO: Synthetic work_signals.json with meeting load,
focus hours, and preferred learning slots.
PRODUCTION: Microsoft Graph API calls:
  GET /me/calendar/calendarView  → meeting load
  GET /me/insights/used          → document engagement
  GET /me/presence               → availability signals
Work IQ SDK would replace this entire file with:
  from microsoft.graph import GraphServiceClient
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "work_signals.json"

DEFAULT_CONTEXT = {
    "meeting_hours_per_week": 20,
    "focus_hours_per_week": 15,
    "preferred_learning_slot": "Morning",
}


class WorkIQClient:
    """Work context signals for engagement and scheduling."""

    def __init__(self) -> None:
        data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
        self.signals = {emp["employee_id"]: emp for emp in data.get("analysts", [])}
        self.team = data.get("team_capacity", {})

    def get_employee_context(self, employee_id: str) -> dict[str, Any]:
        return self.signals.get(employee_id, {**DEFAULT_CONTEXT, "employee_id": employee_id})

    def get_optimal_study_slot(self, employee_id: str) -> str:
        ctx = self.get_employee_context(employee_id)
        if ctx.get("focus_hours_per_week", 0) >= 18:
            return "High focus availability — any slot"
        return (
            f"Recommended: {ctx.get('preferred_learning_slot', 'Morning')} "
            f"(limited focus: {ctx.get('focus_hours_per_week', 15)}h/week)"
        )

    def should_send_reminder(self, employee_id: str, current_hour_ist: int) -> bool:
        slot = self.get_employee_context(employee_id).get("preferred_learning_slot", "Morning")
        if slot == "Morning":
            return 7 <= current_hour_ist <= 10
        if slot == "Afternoon":
            return 13 <= current_hour_ist <= 16
        return True

    def get_team_capacity_summary(self) -> dict[str, Any]:
        recommendation = (
            "Schedule learning during focus-heavy periods"
            if self.team.get("avg_focus_hours", 0) >= 15
            else "Team is overloaded — reduce scope"
        )
        return {**self.team, "recommendation": recommendation}

    def health_check(self) -> dict[str, Any]:
        return {
            "employees_loaded": len(self.signals),
            "team_capacity": self.team.get("current_load", "unknown"),
        }

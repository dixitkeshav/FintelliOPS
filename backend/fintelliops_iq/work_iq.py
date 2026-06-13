"""
Work IQ — Analyst work context for FintelliOps.

DEMO: Synthetic work_signals.json — meeting load, focus hours,
  preferred briefing delivery slots per analyst.

PRODUCTION: Microsoft Graph API:
  GET /me/calendar/calendarView  → meeting load this week
  GET /me/presence               → current availability
  GET /me/insights/used          → recently engaged documents
  Work IQ SDK would replace this file with:
    from microsoft.graph import GraphServiceClient
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import pytz

logger = logging.getLogger(__name__)

DATA_PATH = Path(__file__).resolve().parent.parent / "fintelliops_data" / "work_signals.json"

DEFAULT_ANALYST = {
    "analyst_id": "unknown",
    "meeting_hours_per_week": 20,
    "focus_hours_per_week": 15,
    "preferred_briefing_slot": "08:00",
    "timezone": "Asia/Kolkata",
    "active_coverage": [],
}


class WorkIQClient:
    """Analyst work context for briefing delivery."""

    def __init__(self) -> None:
        data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
        self.analysts = {a["analyst_id"]: a for a in data.get("analysts", [])}
        self.team = data.get("team_capacity", {})
        logger.info("WorkIQ: loaded %s analyst profiles", len(self.analysts))

    def get_analyst_context(self, analyst_id: str) -> dict[str, Any]:
        return self.analysts.get(analyst_id, {**DEFAULT_ANALYST, "analyst_id": analyst_id})

    def get_optimal_briefing_time(self, analyst_id: str) -> str:
        ctx = self.get_analyst_context(analyst_id)
        focus = ctx.get("focus_hours_per_week", 15)
        slot = ctx.get("preferred_briefing_slot", "08:00")
        if focus >= 18:
            return f"High focus availability — deliver at {slot} or anytime"
        if focus >= 12:
            return f"Moderate focus — recommended delivery at {slot}"
        return f"Low focus ({focus}h/week) — keep briefing under 2 minutes, deliver at {slot}"

    def should_deliver_briefing(self, analyst_id: str) -> bool:
        ctx = self.get_analyst_context(analyst_id)
        tz = pytz.timezone(ctx.get("timezone", "Asia/Kolkata"))
        current_hour = datetime.now(tz).hour
        slot_hour = int(str(ctx.get("preferred_briefing_slot", "08:00")).split(":")[0])
        return abs(current_hour - slot_hour) <= 2

    def get_team_summary(self) -> dict[str, Any]:
        recommendation = (
            "Optimal conditions — full briefing appropriate"
            if self.team.get("avg_focus_hours", 0) >= 15
            else "Team capacity constrained — summary briefing only"
        )
        return {**self.team, "recommendation": recommendation}

    def health_check(self) -> dict[str, Any]:
        return {
            "analysts_loaded": len(self.analysts),
            "team_load": self.team.get("current_load", "unknown"),
            "peak_window": self.team.get("peak_analysis_window", ""),
        }

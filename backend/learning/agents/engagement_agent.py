"""Engagement Agent — work-context reminders and strategies."""
from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from learning.foundry_client import FoundryClient
from learning.iq.fabric_iq import FabricIQClient
from learning.iq.foundry_iq import FoundryIQClient
from learning.iq.work_iq import WorkIQClient


class EngagementAgent:
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
        employee_id = context["employee_id"]
        work_ctx = self.work_iq.get_employee_context(employee_id)
        current_hour = datetime.now(ZoneInfo("Asia/Kolkata")).hour
        should_remind = self.work_iq.should_send_reminder(employee_id, current_hour)

        system_prompt = "You are an Engagement Agent for enterprise learning programmes."
        user_prompt = (
            f"Given this work context, suggest 3 specific engagement strategies. "
            f"Meeting load: {work_ctx.get('meeting_hours_per_week', 20)}h/week. "
            f"Focus hours: {work_ctx.get('focus_hours_per_week', 15)}h/week."
        )
        output = self.foundry_client.chat(system_prompt, user_prompt)

        return {
            "agent_name": "EngagementAgent",
            "output": output,
            "iq_layers_used": ["work_iq"],
            "citations": [],
            "fabric_entities": [],
            "work_signals": {
                **work_ctx,
                "should_send_reminder": should_remind,
                "current_hour_ist": current_hour,
            },
            "completed": True,
            "error": None,
        }

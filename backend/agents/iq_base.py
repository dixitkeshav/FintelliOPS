"""Shared helpers for IQ-enabled agent responses."""
from __future__ import annotations

from typing import Any


def agent_result(
    agent_name: str,
    output: str,
    iq_layers_used: list[str],
    citations: list[dict[str, Any]] | None = None,
    fabric_entities: list[str] | None = None,
    work_signals: dict[str, Any] | None = None,
    completed: bool = True,
    error: str | None = None,
) -> dict[str, Any]:
    return {
        "agent_name": agent_name,
        "output": output,
        "iq_layers_used": iq_layers_used,
        "citations": citations or [],
        "fabric_entities": fabric_entities or [],
        "work_signals": work_signals or {},
        "completed": completed,
        "error": error,
    }

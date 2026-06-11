"""
Structured schemas for agent reports and committee outputs.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def _clean_text(value: Any, fallback: str = "") -> str:
    text = str(value or "").strip()
    return text if text else fallback


def clamp_confidence(value: Any, default: float = 0.5) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return default
    return max(0.0, min(1.0, out))


@dataclass
class AgentReport:
    agent: str
    stance: str
    thesis: str
    confidence: float
    action: str
    horizon_days: int
    evidence: list[str]
    risks: list[str]
    assumptions: list[str]
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent": self.agent,
            "stance": self.stance,
            "thesis": self.thesis,
            "confidence": self.confidence,
            "action": self.action,
            "horizon_days": self.horizon_days,
            "evidence": self.evidence,
            "risks": self.risks,
            "assumptions": self.assumptions,
            "metadata": self.metadata,
        }


def build_report(
    *,
    agent: str,
    stance: str,
    thesis: str,
    confidence: float,
    action: str,
    horizon_days: int,
    evidence: list[str] | None = None,
    risks: list[str] | None = None,
    assumptions: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    report = AgentReport(
        agent=_clean_text(agent, "unknown_agent"),
        stance=_clean_text(stance, "neutral"),
        thesis=_clean_text(thesis, "No thesis available."),
        confidence=clamp_confidence(confidence),
        action=_clean_text(action, "HOLD"),
        horizon_days=max(1, int(horizon_days or 1)),
        evidence=[_clean_text(x) for x in (evidence or []) if _clean_text(x)],
        risks=[_clean_text(x) for x in (risks or []) if _clean_text(x)],
        assumptions=[_clean_text(x) for x in (assumptions or []) if _clean_text(x)],
        metadata=metadata or {},
    )
    return report.to_dict()


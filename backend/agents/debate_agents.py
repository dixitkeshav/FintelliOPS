"""
Debate-oriented agents with structured reports.
"""
from __future__ import annotations

from typing import Any

from .base import BaseAgent
from .report_schema import build_report


def _sentiment_balance(articles: list[dict[str, Any]]) -> tuple[int, int, int]:
    pos = sum(1 for a in articles if (a.get("sentiment") or "").lower() == "positive")
    neg = sum(1 for a in articles if (a.get("sentiment") or "").lower() == "negative")
    neu = max(0, len(articles) - pos - neg)
    return pos, neg, neu


class BullResearcherAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="BullResearcher", role="Construct bullish case from signals")

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        articles = context.get("articles", [])
        ticker = context.get("ticker") or "market"
        tech = (context.get("technical_signal") or "neutral").lower()
        macro = (context.get("agent_outputs", {}).get("MacroContext") or {}).get("macro_links") or []
        pos, neg, _ = _sentiment_balance(articles)

        sentiment_bias = (pos - neg) / max(1, len(articles))
        base_conf = 0.45 + max(0.0, sentiment_bias) * 0.35
        if tech == "bullish":
            base_conf += 0.12
        if "GDP / growth" in macro:
            base_conf += 0.05

        evidence = [
            f"Positive sentiment headlines: {pos} vs negative: {neg}.",
            f"Technical regime: {tech}.",
        ]
        if macro:
            evidence.append(f"Macro links support risk-on setup: {', '.join(macro[:2])}.")

        risks = [
            "Overreaction risk after clustered positive headlines.",
            "Policy or global risk headlines can reverse momentum quickly.",
        ]
        report = build_report(
            agent=self.name,
            stance="bullish",
            thesis=f"{ticker}: upside continuation is plausible if sentiment breadth persists.",
            confidence=base_conf,
            action="BUY",
            horizon_days=5,
            evidence=evidence,
            risks=risks,
            assumptions=["Signal horizon is short term and event-driven."],
            metadata={"positive": pos, "negative": neg, "technical": tech},
        )
        self._remember(report)
        return {"report": report, "summary": report["thesis"]}


class BearResearcherAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="BearResearcher", role="Construct bearish case from signals")

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        articles = context.get("articles", [])
        ticker = context.get("ticker") or "market"
        tech = (context.get("technical_signal") or "neutral").lower()
        risk_flags = (context.get("agent_outputs", {}).get("Risk") or {}).get("risk_flags") or []
        pos, neg, _ = _sentiment_balance(articles)

        downside_bias = (neg - pos) / max(1, len(articles))
        base_conf = 0.45 + max(0.0, downside_bias) * 0.35
        if tech == "bearish":
            base_conf += 0.12
        if risk_flags:
            base_conf += 0.06

        evidence = [
            f"Negative sentiment headlines: {neg} vs positive: {pos}.",
            f"Technical regime: {tech}.",
        ]
        if risk_flags:
            evidence.append(f"Risk flags: {', '.join(risk_flags[:2])}.")

        risks = [
            "Short squeeze risk if sentiment improves quickly.",
            "Policy-supportive announcements can invalidate bearish setup.",
        ]
        report = build_report(
            agent=self.name,
            stance="bearish",
            thesis=f"{ticker}: downside or volatility drawdown risk is elevated.",
            confidence=base_conf,
            action="SELL",
            horizon_days=5,
            evidence=evidence,
            risks=risks,
            assumptions=["News impact dominates microstructure noise in short horizon."],
            metadata={"positive": pos, "negative": neg, "technical": tech},
        )
        self._remember(report)
        return {"report": report, "summary": report["thesis"]}


class RiskCommitteeAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="RiskCommittee", role="Aggregate risk personas into constraints")

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        bull = (context.get("agent_outputs", {}).get("BullResearcher") or {}).get("report") or {}
        bear = (context.get("agent_outputs", {}).get("BearResearcher") or {}).get("report") or {}
        risk_flags = (context.get("agent_outputs", {}).get("Risk") or {}).get("risk_flags") or []
        shock_prob = float(context.get("shock_probability") or 0.0)

        net_conf = float(bull.get("confidence") or 0.5) - float(bear.get("confidence") or 0.5)
        risk_level = "moderate"
        if shock_prob >= 70 or len(risk_flags) >= 3:
            risk_level = "high"
        elif abs(net_conf) < 0.08:
            risk_level = "moderate_high"
        elif abs(net_conf) >= 0.2 and len(risk_flags) <= 1:
            risk_level = "moderate_low"

        position_size = 0.5
        if risk_level == "high":
            position_size = 0.25
        elif risk_level == "moderate_low":
            position_size = 0.75

        constraints = {
            "risk_level": risk_level,
            "max_position_fraction": position_size,
            "max_holding_days": 5 if risk_level != "high" else 2,
            "require_stop_loss": True,
            "stop_loss_pct": 1.5 if risk_level == "high" else 2.5,
            "take_profit_pct": 3.0 if risk_level == "high" else 4.0,
        }
        self._remember({"constraints": constraints, "risk_flags": risk_flags, "shock_probability": shock_prob})
        return {
            "constraints": constraints,
            "summary": f"Risk committee set {risk_level} regime, max size {position_size:.0%}.",
        }


class DebateFacilitatorAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="DebateFacilitator", role="Resolve bull vs bear outputs")

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        outputs = context.get("agent_outputs", {})
        bull = (outputs.get("BullResearcher") or {}).get("report") or {}
        bear = (outputs.get("BearResearcher") or {}).get("report") or {}
        risk = (outputs.get("RiskCommittee") or {}).get("constraints") or {}

        bull_conf = float(bull.get("confidence") or 0.5)
        bear_conf = float(bear.get("confidence") or 0.5)
        edge = bull_conf - bear_conf
        stance = "neutral"
        action = "HOLD"
        if edge >= 0.1:
            stance = "bullish"
            action = "BUY"
        elif edge <= -0.1:
            stance = "bearish"
            action = "SELL"

        summary = (
            f"Debate outcome: {stance}. Bull confidence {bull_conf:.2f} vs bear {bear_conf:.2f}. "
            f"Risk regime {risk.get('risk_level', 'unknown')}."
        )
        result = {
            "stance": stance,
            "action": action,
            "confidence_gap": round(abs(edge), 3),
            "bull_confidence": round(bull_conf, 3),
            "bear_confidence": round(bear_conf, 3),
            "summary": summary,
        }
        self._remember(result)
        return result


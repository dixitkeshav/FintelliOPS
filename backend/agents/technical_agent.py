"""
Technical Context Agent: price trends, moving averages, and momentum from market data.
"""
import logging
from typing import Any

from .base import BaseAgent

logger = logging.getLogger(__name__)


def _normalize_ticker(ticker: str) -> str:
    t = (ticker or "").strip().upper().replace("$", "")
    if not t:
        return ""
    if t in ("NIFTY", "NIFTY50", "NSEI", "^NSEI"):
        return "NIFTY"
    if t in ("SENSEX", "BSESN", "^BSESN"):
        return "SENSEX"
    if t in ("BANKNIFTY", "BANK NIFTY", "^NSEBANK"):
        return "BANKNIFTY"
    if "." not in t and not t.startswith("^") and len(t) <= 12:
        return t
    return t


class TechnicalAgent(BaseAgent):
    """Integrates extended technical indicators and candlestick hints."""

    def __init__(self):
        super().__init__(name="Technical", role="Technical analysis: trends, MAs, momentum")

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        ticker = _normalize_ticker(context.get("ticker", ""))
        if not ticker:
            return {
                "summary": "No ticker provided — technical analysis skipped. Pass ?ticker=RELIANCE or NIFTY.",
                "indicators": {},
                "signal": "neutral",
            }

        selected = context.get("selected_indicators") or []
        if isinstance(selected, str):
            selected = [s.strip() for s in selected.split(",") if s.strip()]

        try:
            from quant.technical_snapshot import build_technical_snapshot

            snap = build_technical_snapshot(
                ticker,
                selected_indicators=selected if selected else None,
            )
            if snap.get("error"):
                return {
                    "summary": snap["error"],
                    "indicators": {},
                    "signal": "neutral",
                }

            trend = snap.get("trend", "neutral")
            signal = trend if trend in ("bullish", "bearish") else "neutral"
            indicators = snap.get("indicators") or {}
            patterns = snap.get("candlestick_patterns") or []

            summary = snap.get("summary", "")
            if patterns:
                summary += f" · {len(patterns)} pattern(s) on last bars"

            self._remember({"ticker": ticker, "signal": signal, **indicators})
            return {
                "summary": summary,
                "indicators": indicators,
                "signal": signal,
                "candlestick_patterns": patterns,
                "price_action": snap.get("price_action"),
            }
        except Exception as e:
            logger.warning("Technical agent failed for %s: %s", ticker, e)
            return {
                "summary": f"Technical data unavailable for {ticker}: {e}",
                "indicators": {},
                "signal": "neutral",
            }

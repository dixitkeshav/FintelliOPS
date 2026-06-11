"""
News Scout Agent: scans news, detects unusual sentiment spikes.
"""
import logging
from typing import Any

from .base import BaseAgent

logger = logging.getLogger(__name__)


class NewsScoutAgent(BaseAgent):
    """Continuously scans news and detects unusual sentiment spikes."""

    def __init__(self):
        super().__init__(name="NewsScout", role="Scan news and detect unusual sentiment spikes")

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        articles = context.get("articles", [])
        if not articles:
            return {"findings": [], "spike_detected": False, "summary": "No articles to analyze."}

        # Aggregate sentiment counts
        pos = sum(1 for a in articles if (a.get("sentiment") or "").lower() == "positive")
        neg = sum(1 for a in articles if (a.get("sentiment") or "").lower() == "negative")
        neu = len(articles) - pos - neg

        # Simple spike: >60% one direction
        total = len(articles)
        spike_detected = False
        spike_direction = None
        if total:
            if pos / total >= 0.6:
                spike_detected = True
                spike_direction = "positive"
            elif neg / total >= 0.6:
                spike_detected = True
                spike_direction = "negative"

        # Store in memory for debate
        finding = {
            "positive_count": pos,
            "negative_count": neg,
            "neutral_count": neu,
            "spike_detected": spike_detected,
            "spike_direction": spike_direction,
            "total_articles": total,
        }
        self._remember(finding)

        return {
            "findings": [finding],
            "spike_detected": spike_detected,
            "spike_direction": spike_direction,
            "summary": (
                f"Scanned {total} articles. "
                + (f"Unusual {spike_direction} sentiment spike detected." if spike_detected else "No unusual spike.")
            ),
        }

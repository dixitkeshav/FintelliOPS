"""News Scout Agent: grounded market-moving event detection."""
from __future__ import annotations

import logging
from typing import Any

from fintelliops_iq.helpers import format_docs

from .base import BaseAgent
from .iq_base import agent_result

logger = logging.getLogger(__name__)


class NewsScoutAgent(BaseAgent):
    """Scans grounded knowledge for market-moving events."""

    def __init__(self, llm=None, foundry_iq=None, fabric_iq=None, work_iq=None) -> None:
        super().__init__(name="NewsScout", role="Scan news and detect unusual sentiment spikes")
        self.llm = llm
        self.foundry_iq = foundry_iq
        self.fabric_iq = fabric_iq
        self.work_iq = work_iq

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        if self.llm and self.foundry_iq:
            return self._run_iq(context)
        return self._run_legacy(context)

    def _run_iq(self, context: dict[str, Any]) -> dict[str, Any]:
        query = (
            f"market news earnings {context.get('query', 'India markets')} "
            f"{context.get('sector', '')}"
        )
        docs = self.foundry_iq.retrieve(query, top_k=5)
        system_prompt = (
            "You are a financial news scout. Based ONLY on the retrieved documents below, "
            "identify the top 3 market-moving events. For each event: title, impact "
            "(bullish/bearish/neutral), affected sectors, citation. "
            "Never invent events not present in the documents."
        )
        user_prompt = f"Documents:\n{format_docs(docs)}\n\nQuery: {query}"
        output = self.llm.chat(system_prompt, user_prompt)
        context["news_events"] = output
        return agent_result(
            "NewsScoutAgent",
            output,
            ["foundry_iq"],
            citations=docs,
        )

    def _run_legacy(self, context: dict[str, Any]) -> dict[str, Any]:
        articles = context.get("articles", [])
        if not articles:
            return {
                "findings": [],
                "spike_detected": False,
                "summary": "No articles to analyze.",
            }

        pos = sum(1 for a in articles if (a.get("sentiment") or "").lower() == "positive")
        neg = sum(1 for a in articles if (a.get("sentiment") or "").lower() == "negative")
        neu = len(articles) - pos - neg
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
                + (
                    f"Unusual {spike_direction} sentiment spike detected."
                    if spike_detected
                    else "No unusual spike."
                )
            ),
        }

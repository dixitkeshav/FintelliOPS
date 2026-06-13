"""Macro Context Agent: macro backdrop from grounded policy documents."""
from __future__ import annotations

import logging
from typing import Any

from fintelliops_iq.helpers import format_docs

from .base import BaseAgent
from .iq_base import agent_result

logger = logging.getLogger(__name__)


class MacroContextAgent(BaseAgent):
    """Links news to macro indicators using Foundry + Fabric IQ."""

    def __init__(self, llm=None, foundry_iq=None, fabric_iq=None, work_iq=None) -> None:
        super().__init__(name="MacroContext", role="Link news to macro indicators (rates, CPI, GDP)")
        self.llm = llm
        self.foundry_iq = foundry_iq
        self.fabric_iq = fabric_iq
        self.work_iq = work_iq

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        if self.llm and self.foundry_iq and self.fabric_iq:
            return self._run_iq(context)
        return self._run_legacy(context)

    def _run_iq(self, context: dict[str, Any]) -> dict[str, Any]:
        docs = self.foundry_iq.retrieve("macro policy rates inflation RBI Fed", top_k=4)
        fed_corr = self.fabric_iq.get_macro_correlations("US_FED_RATE")
        repo_corr = self.fabric_iq.get_macro_correlations("INDIA_REPO")

        system_prompt = (
            "You are a macro analyst. Based on the retrieved policy documents, explain the macro backdrop. "
            "Cover: rate environment, inflation trajectory, currency pressures, EM outlook. "
            "Cite your sources. Correlate macro signals to sector impacts using the provided data."
        )
        user_prompt = (
            f"Documents:\n{format_docs(docs)}\n\n"
            f"US Fed correlations: {fed_corr}\n"
            f"India repo correlations: {repo_corr}\n"
            f"Query context: {context.get('query', '')}"
        )
        output = self.llm.chat(system_prompt, user_prompt)
        context["macro_summary"] = output

        fabric_entities = [
            f"{c['sector']}:{c['direction']}" for c in (fed_corr + repo_corr)
        ]
        return agent_result(
            "MacroContextAgent",
            output,
            ["foundry_iq", "fabric_iq"],
            citations=docs,
            fabric_entities=fabric_entities,
        )

    def _run_legacy(self, context: dict[str, Any]) -> dict[str, Any]:
        articles = context.get("articles", [])
        headlines = " ".join(
            (a.get("title") or a.get("summary") or "")[:200] for a in articles[:10]
        ).lower()

        macro_links = []
        if any(k in headlines for k in ["rate", "rbi", "fed", "interest"]):
            macro_links.append("Rates / monetary policy")
        if any(k in headlines for k in ["inflation", "cpi", "prices"]):
            macro_links.append("Inflation / CPI")
        if any(k in headlines for k in ["gdp", "growth", "recession"]):
            macro_links.append("GDP / growth")
        if any(k in headlines for k in ["bond", "yield", "treasury"]):
            macro_links.append("Bond yields")
        if not macro_links:
            macro_links.append("General market sentiment")

        finding = {"macro_links": macro_links, "headlines_sample": headlines[:300]}
        self._remember(finding)
        return {
            "macro_links": macro_links,
            "summary": f"News linked to: {', '.join(macro_links)}.",
        }

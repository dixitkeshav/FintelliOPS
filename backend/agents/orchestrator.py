"""
Agent orchestrator: FintelliOps IQ pipeline + legacy market/ticker pipeline.
"""
import logging
import time
from datetime import datetime, timezone
from typing import Any

from .base import BaseAgent
from .news_scout import NewsScoutAgent
from .macro_context import MacroContextAgent
from .technical_agent import TechnicalAgent
from .market_reaction import MarketReactionAgent
from .risk_agent import RiskAgent
from .decision_agent import DecisionAgent
from .debate_agents import (
    BearResearcherAgent,
    BullResearcherAgent,
    DebateFacilitatorAgent,
    RiskCommitteeAgent,
)

try:
    from shock_predictor.agent import ShockAgent, build_shock_context_from_pipeline
except ImportError:
    ShockAgent = None
    build_shock_context_from_pipeline = None

logger = logging.getLogger(__name__)

PIPELINE_STEPS = [
    ("news_fetch", "News ingestion", "Fetch headlines from NewsAPI and fallback providers"),
    ("news_scout", "News Scout", "Scan sentiment distribution and detect spikes"),
    ("macro_context", "Macro Context", "Link headlines to rates, CPI, GDP, yields"),
    ("technical", "Technical Analysis", "Moving averages, momentum, volatility"),
    ("market_reaction", "Market Reaction", "Historical reaction patterns to similar sentiment"),
    ("risk", "Risk", "Flag concentration, spike, and downside risks"),
    ("bull_research", "Bull Research", "Build bullish thesis from multi-signal evidence"),
    ("bear_research", "Bear Research", "Build bearish thesis from multi-signal evidence"),
    ("risk_committee", "Risk Committee", "Set position/risk constraints from committee view"),
    ("debate_facilitator", "Debate Facilitator", "Resolve bull vs bear and select base stance"),
    ("shock", "Shock Predictor", "Real-time Nifty shock probability and hedge hints"),
    ("decision", "Decision", "Synthesize all agent views into a recommendation"),
]


class AgentOrchestrator:
    """Runs FintelliOps IQ pipeline or legacy market/ticker pipeline."""

    def __init__(self) -> None:
        from intelligence.llm import LLMClient
        from fintelliops_iq.fabric_iq import FabricIQClient
        from fintelliops_iq.foundry_iq import FoundryIQClient
        from fintelliops_iq.work_iq import WorkIQClient

        self.llm = LLMClient()
        self.foundry_iq = FoundryIQClient()
        self.fabric_iq = FabricIQClient()
        self.work_iq = WorkIQClient()

        self.pipeline = [
            NewsScoutAgent(self.llm, self.foundry_iq, self.fabric_iq, self.work_iq),
            MacroContextAgent(self.llm, self.foundry_iq, self.fabric_iq, self.work_iq),
            MarketReactionAgent(self.llm, self.foundry_iq, self.fabric_iq, self.work_iq),
            RiskAgent(self.llm, self.foundry_iq, self.fabric_iq, self.work_iq),
            DecisionAgent(self.llm, self.foundry_iq, self.fabric_iq, self.work_iq),
        ]

        self.agents: list[BaseAgent] = [
            NewsScoutAgent(),
            MacroContextAgent(),
            TechnicalAgent(),
            MarketReactionAgent(),
            RiskAgent(),
            DecisionAgent(),
        ]
        self.news_scout = self.agents[0]
        self.macro = self.agents[1]
        self.technical = self.agents[2]
        self.market_reaction = self.agents[3]
        self.risk = self.agents[4]
        self.decision = self.agents[5]
        self.bull = BullResearcherAgent()
        self.bear = BearResearcherAgent()
        self.risk_committee = RiskCommitteeAgent()
        self.debate = DebateFacilitatorAgent()
        self.shock = ShockAgent() if ShockAgent else None

    def run_fintelliops(
        self,
        query: str,
        sector: str = "Technology",
        analyst_id: str = "ANL-001",
    ) -> dict[str, Any]:
        """Run 5-agent FintelliOps IQ pipeline (Foundry + Fabric + Work)."""
        from fintelliops_iq.evaluation import evaluate_pipeline

        context: dict[str, Any] = {
            "query": query,
            "sector": sector,
            "analyst_id": analyst_id,
            "pipeline_start": datetime.now(timezone.utc).isoformat(),
            "agents": {},
        }

        for agent in self.pipeline:
            agent_name = agent.__class__.__name__
            try:
                result = agent.run(context)
                context["agents"][agent_name] = result
                if result.get("output"):
                    context[f"{agent_name}_output"] = result["output"]
            except Exception as exc:
                logger.error("Agent %s failed: %s", agent_name, exc, exc_info=True)
                context["agents"][agent_name] = {
                    "agent_name": agent_name,
                    "output": "",
                    "iq_layers_used": [],
                    "citations": [],
                    "fabric_entities": [],
                    "work_signals": {},
                    "completed": False,
                    "error": str(exc),
                }

        all_citations: dict[str, dict] = {}
        for agent_result in context["agents"].values():
            for c in agent_result.get("citations", []):
                key = c.get("citation", c.get("source", ""))
                if key:
                    all_citations[key] = c
        context["all_citations"] = list(all_citations.values())

        context["pipeline_end"] = datetime.now(timezone.utc).isoformat()
        context["pipeline_completed"] = all(
            a.get("completed") for a in context["agents"].values()
        )
        context["evaluation"] = evaluate_pipeline(context)
        context["recommendation"] = context["agents"].get("DecisionAgent", {}).get("output", "")
        return context

    def health_check(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "pipeline_agents": len(self.pipeline),
            "llm": self.llm.health_check(),
            "foundry_iq": self.foundry_iq.health_check(),
            "fabric_iq": self.fabric_iq.health_check(),
            "work_iq": self.work_iq.health_check(),
        }

    def run(
        self,
        articles: list[dict],
        ticker: str = "",
        aggregate_sentiment: str = "neutral",
        news_meta: dict[str, Any] | None = None,
        selected_indicators: list[str] | None = None,
        selected_patterns: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Execute pipeline: News Scout -> Macro -> Technical -> Market Reaction -> Risk -> Decision.
        """
        pipeline: list[dict[str, Any]] = []
        meta = news_meta or {}

        def record(step_id: str, label: str, status: str, summary: str = "", ms: float = 0) -> None:
            pipeline.append(
                {
                    "id": step_id,
                    "label": label,
                    "status": status,
                    "summary": summary,
                    "duration_ms": round(ms, 1),
                }
            )

        record(
            "news_fetch",
            "News ingestion",
            "completed",
            f"Loaded {len(articles)} articles from {meta.get('source', 'unknown')}.",
            float(meta.get("fetch_ms", 0)),
        )

        ctx: dict[str, Any] = {
            "articles": articles,
            "ticker": ticker,
            "aggregate_sentiment": aggregate_sentiment,
            "selected_indicators": selected_indicators or [],
            "selected_patterns": selected_patterns or [],
        }

        t0 = time.perf_counter()
        scout_out = self.news_scout.run(ctx)
        record("news_scout", "News Scout", "completed", scout_out.get("summary", ""), (time.perf_counter() - t0) * 1000)
        ctx["agent_outputs"] = {"NewsScout": scout_out}
        ctx["spike_detected"] = scout_out.get("spike_detected", False)
        ctx["spike_direction"] = scout_out.get("spike_direction")

        t0 = time.perf_counter()
        macro_out = self.macro.run(ctx)
        record("macro_context", "Macro Context", "completed", macro_out.get("summary", ""), (time.perf_counter() - t0) * 1000)
        ctx["agent_outputs"]["MacroContext"] = macro_out

        t0 = time.perf_counter()
        technical_out = self.technical.run(ctx)
        record("technical", "Technical Analysis", "completed", technical_out.get("summary", ""), (time.perf_counter() - t0) * 1000)
        ctx["agent_outputs"]["Technical"] = technical_out
        ctx["technical_signal"] = technical_out.get("signal", "neutral")

        t0 = time.perf_counter()
        reaction_out = self.market_reaction.run(ctx)
        record("market_reaction", "Market Reaction", "completed", reaction_out.get("summary", ""), (time.perf_counter() - t0) * 1000)
        ctx["agent_outputs"]["MarketReaction"] = reaction_out

        t0 = time.perf_counter()
        risk_out = self.risk.run(ctx)
        record("risk", "Risk", "completed", risk_out.get("summary", ""), (time.perf_counter() - t0) * 1000)
        ctx["agent_outputs"]["Risk"] = risk_out

        t0 = time.perf_counter()
        bull_out = self.bull.run(ctx)
        record("bull_research", "Bull Research", "completed", bull_out.get("summary", ""), (time.perf_counter() - t0) * 1000)
        ctx["agent_outputs"]["BullResearcher"] = bull_out

        t0 = time.perf_counter()
        bear_out = self.bear.run(ctx)
        record("bear_research", "Bear Research", "completed", bear_out.get("summary", ""), (time.perf_counter() - t0) * 1000)
        ctx["agent_outputs"]["BearResearcher"] = bear_out

        t0 = time.perf_counter()
        committee_out = self.risk_committee.run(ctx)
        record(
            "risk_committee",
            "Risk Committee",
            "completed",
            committee_out.get("summary", ""),
            (time.perf_counter() - t0) * 1000,
        )
        ctx["agent_outputs"]["RiskCommittee"] = committee_out

        t0 = time.perf_counter()
        debate_out = self.debate.run(ctx)
        record(
            "debate_facilitator",
            "Debate Facilitator",
            "completed",
            debate_out.get("summary", ""),
            (time.perf_counter() - t0) * 1000,
        )
        ctx["agent_outputs"]["Debate"] = debate_out

        shock_out = {}
        if self.shock and build_shock_context_from_pipeline:
            t0 = time.perf_counter()
            try:
                shock_ctx = {**ctx, **build_shock_context_from_pipeline(ctx)}
                shock_out = self.shock.run(shock_ctx)
                record(
                    "shock",
                    "Shock Predictor",
                    "completed",
                    shock_out.get("summary", ""),
                    (time.perf_counter() - t0) * 1000,
                )
                ctx["agent_outputs"]["Shock"] = shock_out
                ctx["shock_probability"] = shock_out.get("shock_probability", 0)
            except Exception as e:
                logger.warning("Shock agent skipped: %s", e)
                record("shock", "Shock Predictor", "error", f"Skipped: {e}", (time.perf_counter() - t0) * 1000)

        t0 = time.perf_counter()
        decision_out = self.decision.run(ctx)
        record("decision", "Decision", "completed", decision_out.get("recommendation", ""), (time.perf_counter() - t0) * 1000)
        ctx["agent_outputs"]["Decision"] = decision_out

        agents_payload = self._build_agents_payload(
            scout_out=scout_out,
            macro_out=macro_out,
            technical_out=technical_out,
            reaction_out=reaction_out,
            risk_out=risk_out,
            bull_out=bull_out,
            bear_out=bear_out,
            committee_out=committee_out,
            debate_out=debate_out,
            shock_out=shock_out,
            decision_out=decision_out,
        )

        result = {
            "pipeline_completed": all(s.get("status") == "completed" for s in pipeline),
            "news_scout": scout_out,
            "macro_context": macro_out,
            "technical": technical_out,
            "market_reaction": reaction_out,
            "risk": risk_out,
            "bull_research": bull_out,
            "bear_research": bear_out,
            "risk_committee": committee_out,
            "debate": debate_out,
            "shock": shock_out,
            "decision": decision_out,
            "agents": agents_payload,
            "recommendation": decision_out.get("recommendation", ""),
            "pipeline": pipeline,
            "article_count": len(articles),
            "news_source": meta.get("source"),
            "news_sources": meta.get("sources"),
            "ticker": ticker or None,
            "selected_indicators": selected_indicators or [],
            "selected_patterns": selected_patterns or [],
            "data_notice": "Synthetic demo data" if meta.get("source") == "synthetic" else None,
        }

        from .evaluation import evaluate_pipeline_result

        result["evaluation"] = evaluate_pipeline_result(result)
        return result

    def _agent_card(
        self,
        agent_id: str,
        name: str,
        output: str,
        signal: str,
        metrics: dict[str, Any] | None = None,
        extras: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        card: dict[str, Any] = {
            "id": agent_id,
            "name": name,
            "called": True,
            "status": "completed",
            "output": output,
            "signal": signal,
        }
        if metrics:
            card["metrics"] = metrics
        if extras:
            card.update(extras)
        return card

    def _build_agents_payload(self, **outputs: dict[str, Any]) -> dict[str, Any]:
        scout = outputs.get("scout_out") or {}
        macro = outputs.get("macro_out") or {}
        technical = outputs.get("technical_out") or {}
        reaction = outputs.get("reaction_out") or {}
        risk = outputs.get("risk_out") or {}
        bull = outputs.get("bull_out") or {}
        bear = outputs.get("bear_out") or {}
        committee = outputs.get("committee_out") or {}
        debate = outputs.get("debate_out") or {}
        shock = outputs.get("shock_out") or {}
        decision = outputs.get("decision_out") or {}

        spike_dir = scout.get("spike_direction") or "neutral"
        tech_sig = (technical.get("signal") or "neutral").lower()

        payload = {
            "news_scout": self._agent_card(
                "news_scout",
                "News Scout",
                scout.get("summary", ""),
                spike_dir if scout.get("spike_detected") else "neutral",
                metrics={
                    "positive_count": (scout.get("findings") or [{}])[0].get("positive_count"),
                    "negative_count": (scout.get("findings") or [{}])[0].get("negative_count"),
                    "spike_detected": scout.get("spike_detected"),
                },
            ),
            "macro_context": self._agent_card(
                "macro_context",
                "Macro Context",
                macro.get("summary", ""),
                "bullish" if macro.get("macro_links") else "neutral",
                extras={"macro_links": macro.get("macro_links", [])},
            ),
            "technical": self._agent_card(
                "technical",
                "Technical Analysis",
                technical.get("summary", ""),
                tech_sig,
                metrics=technical.get("indicators"),
                extras={"patterns": technical.get("candlestick_patterns", [])},
            ),
            "market_reaction": self._agent_card(
                "market_reaction",
                "Market Reaction",
                reaction.get("summary", ""),
                "neutral",
                extras={"historical_reaction": reaction.get("historical_reaction")},
            ),
            "risk": self._agent_card(
                "risk",
                "Risk",
                risk.get("summary", ""),
                "bearish" if len(risk.get("risk_flags") or []) > 2 else "neutral",
                extras={"risk_flags": risk.get("risk_flags", [])},
            ),
            "bull_research": self._agent_card(
                "bull_research",
                "Bull Research",
                bull.get("summary", ""),
                "bullish",
                metrics=(bull.get("report") or {}).get("metadata"),
                extras={"action": (bull.get("report") or {}).get("action")},
            ),
            "bear_research": self._agent_card(
                "bear_research",
                "Bear Research",
                bear.get("summary", ""),
                "bearish",
                metrics=(bear.get("report") or {}).get("metadata"),
                extras={"action": (bear.get("report") or {}).get("action")},
            ),
            "risk_committee": self._agent_card(
                "risk_committee",
                "Risk Committee",
                committee.get("summary", ""),
                "neutral",
                extras={"constraints": committee.get("constraints", {})},
            ),
            "debate": self._agent_card(
                "debate",
                "Debate Facilitator",
                debate.get("summary", ""),
                (debate.get("stance") or "neutral").lower(),
                extras={
                    "action": debate.get("action"),
                    "confidence_gap": debate.get("confidence_gap"),
                },
            ),
            "decision": self._agent_card(
                "decision",
                "Decision",
                decision.get("recommendation") or decision.get("summary", ""),
                (decision.get("stance") or decision.get("action") or "neutral").lower(),
                extras={
                    "action": decision.get("action"),
                    "risk_level": decision.get("risk_level"),
                    "position_size_cap": decision.get("position_size_cap"),
                },
            ),
        }

        if shock:
            payload["shock"] = self._agent_card(
                "shock",
                "Shock Predictor",
                shock.get("summary", ""),
                "bearish" if (shock.get("shock_probability") or 0) > 0.6 else "neutral",
                metrics={"shock_probability": shock.get("shock_probability")},
                extras={"suggested_hedge": shock.get("suggested_hedge")},
            )

        return payload

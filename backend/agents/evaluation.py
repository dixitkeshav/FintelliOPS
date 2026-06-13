"""
Pipeline evaluation — scores agent coverage, output quality, and safety heuristics.

Run: PYTHONPATH=backend python3 -m agents.run_synthetic_test
"""
from __future__ import annotations

import re
from typing import Any

PII_PATTERNS = [
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
    re.compile(r"\b\d{10}\b"),
]

EXPECTED_AGENTS = [
    "news_scout",
    "macro_context",
    "technical",
    "market_reaction",
    "risk",
    "bull_research",
    "bear_research",
    "risk_committee",
    "debate",
    "decision",
]

OPTIONAL_AGENTS = ["shock"]


def _has_pii(text: str) -> bool:
    return any(p.search(text) for p in PII_PATTERNS)


def evaluate_pipeline_result(result: dict[str, Any]) -> dict[str, Any]:
    """Score a completed orchestrator response."""
    agents = result.get("agents") or {}
    pipeline = result.get("pipeline") or []
    safety_flags: list[str] = []

    called = [aid for aid in EXPECTED_AGENTS if agents.get(aid, {}).get("called")]
    optional_called = [aid for aid in OPTIONAL_AGENTS if agents.get(aid, {}).get("called")]

    summaries = [
        str(agents.get(aid, {}).get("output", ""))
        for aid in EXPECTED_AGENTS + OPTIONAL_AGENTS
    ]
    non_empty = sum(1 for s in summaries if len(s.strip()) > 20)

    for s in summaries:
        if _has_pii(s):
            safety_flags.append("possible_pii_in_output")

    completed_steps = sum(1 for s in pipeline if s.get("status") == "completed")
    pipeline_score = completed_steps / max(len(pipeline), 1)

    coverage_score = len(called) / len(EXPECTED_AGENTS)
    output_score = non_empty / max(len(EXPECTED_AGENTS) + len(optional_called), 1)

    rec = result.get("recommendation") or ""
    relevance_score = 1.0 if rec and len(rec) > 5 else 0.0

    groundedness_score = 0.0
    if result.get("article_count", 0) > 0 and non_empty >= len(EXPECTED_AGENTS) - 1:
        groundedness_score = min(1.0, non_empty / len(EXPECTED_AGENTS))

    overall = round(
        (coverage_score * 0.35 + output_score * 0.25 + pipeline_score * 0.2 + relevance_score * 0.1 + groundedness_score * 0.1)
        * 100,
        1,
    )

    return {
        "pipeline_completed": pipeline_score >= 0.9 and len(called) == len(EXPECTED_AGENTS),
        "agents_called": called,
        "optional_agents_called": optional_called,
        "agents_missing": [a for a in EXPECTED_AGENTS if a not in called],
        "coverage_score": round(coverage_score * 100, 1),
        "output_score": round(output_score * 100, 1),
        "pipeline_score": round(pipeline_score * 100, 1),
        "groundedness_score": round(groundedness_score * 100, 1),
        "relevance_score": round(relevance_score * 100, 1),
        "overall_score": overall,
        "safety_flags": safety_flags,
        "synthetic_data": result.get("news_source") == "synthetic",
    }

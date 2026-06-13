"""Pipeline evaluation for FintelliOps IQ agents."""
from __future__ import annotations

import re
from typing import Any

EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")


def evaluate_pipeline(context: dict[str, Any]) -> dict[str, Any]:
    agents = context.get("agents", {})
    total = len(agents)
    if total == 0:
        return {
            "groundedness_score": 0.0,
            "relevance_score": 0.0,
            "completion_score": 0.0,
            "overall_score": 0.0,
            "safety_flags": [],
            "passed": False,
            "agents_completed": "0/0",
        }

    with_citations = sum(1 for a in agents.values() if len(a.get("citations", [])) > 0)
    groundedness = round(with_citations / total, 2)

    completed = sum(1 for a in agents.values() if a.get("completed", False))
    completion = round(completed / total, 2)

    query_terms = set(context.get("query", "").lower().split())
    relevant = 0
    for agent in agents.values():
        output_words = set(agent.get("output", "").lower().split())
        if query_terms & output_words:
            relevant += 1
    relevance = round(relevant / total, 2)

    safety_flags: list[str] = []
    for name, agent in agents.items():
        output = agent.get("output", "")
        if EMAIL_PATTERN.search(output):
            safety_flags.append(f"potential_pii:{name}")
        if len(output) > 3000:
            safety_flags.append(f"output_too_long:{name}")
        if not output and agent.get("completed"):
            safety_flags.append(f"empty_output:{name}")

    overall = round((groundedness * 40) + (relevance * 30) + (completion * 30), 1)

    return {
        "groundedness_score": groundedness,
        "relevance_score": relevance,
        "completion_score": completion,
        "overall_score": overall,
        "safety_flags": safety_flags,
        "passed": overall >= 70,
        "agents_completed": f"{completed}/{total}",
    }

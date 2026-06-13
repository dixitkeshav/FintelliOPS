"""Pipeline evaluation metrics for learning agents."""
from __future__ import annotations

import re
from typing import Any

EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")


def evaluate_pipeline(context: dict[str, Any]) -> dict[str, Any]:
    agents = context.get("agents", {})
    total_agents = len(agents) or 1
    topics = [t.lower() for t in context.get("topics", [])]

    agents_with_citations = sum(
        1 for r in agents.values() if len(r.get("citations", [])) > 0
    )
    groundedness_score = agents_with_citations / total_agents

    agents_mentioning_topics = 0
    for result in agents.values():
        output = (result.get("output") or "").lower()
        if any(topic in output for topic in topics):
            agents_mentioning_topics += 1
    relevance_score = agents_mentioning_topics / total_agents

    completed_agents = sum(1 for r in agents.values() if r.get("completed"))
    completion_score = completed_agents / total_agents

    safety_flags: list[str] = []
    for name, result in agents.items():
        output = result.get("output") or ""
        if EMAIL_PATTERN.search(output):
            safety_flags.append("potential_pii")
        if len(output) > 3000:
            safety_flags.append("output_too_long")
        if not output.strip():
            safety_flags.append(f"empty_output:{name}")

    overall_score = round(
        (groundedness_score * 40) + (relevance_score * 30) + (completion_score * 30),
        1,
    )

    return {
        "groundedness_score": round(groundedness_score, 3),
        "relevance_score": round(relevance_score, 3),
        "completion_score": round(completion_score, 3),
        "overall_score": overall_score,
        "safety_flags": list(dict.fromkeys(safety_flags)),
        "passed": overall_score >= 70,
    }

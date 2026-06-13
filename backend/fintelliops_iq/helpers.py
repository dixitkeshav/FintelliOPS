"""Shared helpers for FintelliOps agents."""
from __future__ import annotations

from typing import Any


def format_docs(docs: list[dict[str, Any]]) -> str:
    """Format retrieved chunks as a numbered list with citations."""
    if not docs:
        return "No documents retrieved."
    lines: list[str] = []
    for i, doc in enumerate(docs, 1):
        citation = doc.get("citation", doc.get("source", "unknown"))
        content = doc.get("content", "")[:600]
        score = doc.get("score", 0)
        lines.append(f"{i}. [{citation}] (score: {score:.2f})\n{content}")
    return "\n\n".join(lines)

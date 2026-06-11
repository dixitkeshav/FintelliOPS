"""
Foundry IQ — grounded knowledge retrieval layer (synthetic demo knowledge base).

In production, this connects to Azure AI Search via Microsoft Foundry IQ
with permission-aware retrieval from SharePoint, Blob Storage, or OneLake.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "documents"


class FoundryIQ:
    """Permission-aware grounded retrieval from approved synthetic knowledge sources."""

    def __init__(self) -> None:
        self._sources: dict[str, str] = {}
        for path in DATA_DIR.glob("*.md"):
            self._sources[path.stem] = path.read_text(encoding="utf-8")

    def list_sources(self) -> list[str]:
        return list(self._sources.keys())

    def retrieve(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        """Simple keyword retrieval with citations (demo Foundry IQ pattern)."""
        query_terms = {t.lower() for t in re.findall(r"\w+", query) if len(t) > 2}
        scored: list[tuple[float, str, str]] = []

        for source_id, content in self._sources.items():
            content_lower = content.lower()
            hits = sum(1 for term in query_terms if term in content_lower)
            if hits:
                scored.append((hits / max(len(query_terms), 1), source_id, content))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, source_id, content in scored[:top_k]:
            excerpt = self._best_excerpt(content, query_terms)
            results.append({
                "source_id": source_id,
                "source_title": source_id.replace("_", " ").title(),
                "relevance_score": round(score, 2),
                "excerpt": excerpt,
                "citation": f"[{source_id}.md]",
            })
        return results

    def _best_excerpt(self, content: str, terms: set[str], window: int = 280) -> str:
        lines = [ln.strip() for ln in content.splitlines() if ln.strip() and not ln.startswith("#")]
        for line in lines:
            if any(t in line.lower() for t in terms):
                return line[:window]
        return (lines[0] if lines else content)[:window]

    def grounded_answer(self, query: str) -> dict[str, Any]:
        chunks = self.retrieve(query, top_k=3)
        if not chunks:
            return {
                "answer": "No grounded content found in approved knowledge base.",
                "citations": [],
                "grounded": False,
            }
        answer_parts = [c["excerpt"] for c in chunks]
        return {
            "answer": " ".join(answer_parts),
            "citations": [c["citation"] for c in chunks],
            "sources": chunks,
            "grounded": True,
            "layer": "Foundry IQ",
        }

    def generate_assessment_context(self, certification: str, skill: str) -> dict[str, Any]:
        query = f"{certification} {skill} assessment readiness practice"
        grounded = self.grounded_answer(query)
        return {
            "certification": certification,
            "skill": skill,
            "grounded_context": grounded,
            "question_seed_topics": self._extract_topics(certification),
        }

    def _extract_topics(self, certification: str) -> list[str]:
        chunks = self.retrieve(certification, top_k=2)
        topics: list[str] = []
        for c in chunks:
            for line in c["excerpt"].split(","):
                t = line.strip()
                if t and len(t) < 60:
                    topics.append(t)
        return topics[:5] or [f"{certification} fundamentals", "Best practices", "Exam readiness"]

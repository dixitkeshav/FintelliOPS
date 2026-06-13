"""
Foundry IQ — Grounded knowledge retrieval for FintelliOps.

DEMO: Azure AI Search (free tier) over synthetic financial documents:
  earnings reports, macro policy statements, sector analyses.

PRODUCTION: Azure AI Search with semantic ranking + permission filters
  connected to real Bloomberg/Reuters feeds, earnings databases,
  internal research notes via SharePoint/OneLake connectors.

Agent contract is identical in both cases:
  retrieve(query) -> list[{content, citation, score, doc_type}]
"""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

import os

logger = logging.getLogger(__name__)

DOCS_PATH = Path(__file__).resolve().parent.parent / "fintelliops_data" / "documents"
CHUNK_SIZE = 400
CHUNK_OVERLAP = 50


class FoundryIQClient:
    """Grounded financial knowledge retrieval."""

    def __init__(self) -> None:
        self.endpoint = (os.getenv("AZURE_SEARCH_ENDPOINT", "") or "").strip()
        self.key = os.getenv("AZURE_SEARCH_KEY", "")
        self.index_name = os.getenv("AZURE_SEARCH_INDEX_NAME", "fintelliops-knowledge")
        self.available = bool(self.endpoint and self.key)
        self.fallback = not self.available
        self.client = None

        if self.available:
            try:
                from azure.core.credentials import AzureKeyCredential
                from azure.search.documents import SearchClient

                self.client = SearchClient(
                    endpoint=self.endpoint,
                    index_name=self.index_name,
                    credential=AzureKeyCredential(self.key),
                )
                self.fallback = False
                logger.info("FoundryIQ: Azure AI Search connected")
            except Exception as exc:
                logger.warning("FoundryIQ init failed: %s", exc)
                self.fallback = True
        else:
            logger.warning("FoundryIQ: Azure Search not configured — using local fallback")

        self._local_docs = self._load_local_docs(str(DOCS_PATH))

    def retrieve(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        if self.fallback or self.client is None:
            return self._local_retrieve(query, top_k)
        try:
            results = self.client.search(
                search_text=query,
                top=top_k,
                select=["content", "source", "doc_type", "chunk_index"],
            )
            return [
                {
                    "content": r["content"],
                    "citation": r["source"],
                    "doc_type": r.get("doc_type", "knowledge"),
                    "score": r.get("@search.score", 0.0),
                    "chunk_index": r.get("chunk_index", 0),
                }
                for r in results
            ]
        except Exception as exc:
            logger.error("Azure Search failed: %s — falling back to local", exc)
            return self._local_retrieve(query, top_k)

    def _local_retrieve(self, query: str, top_k: int) -> list[dict[str, Any]]:
        query_words = set(re.findall(r"\w+", query.lower()))
        scored: list[tuple[float, dict[str, Any]]] = []
        for doc in self._local_docs:
            content_words = set(re.findall(r"\w+", doc["content"].lower()))
            overlap = len(query_words & content_words)
            score = overlap / max(len(query_words), 1)
            if overlap > 0:
                scored.append((score, {**doc, "score": score}))
        scored.sort(key=lambda x: x[0], reverse=True)
        if not scored:
            return [{**d, "score": 0.1} for d in self._local_docs[:top_k]]
        return [item[1] for item in scored[:top_k]]

    def _load_local_docs(self, docs_path: str) -> list[dict[str, Any]]:
        docs: list[dict[str, Any]] = []
        path = Path(docs_path)
        if not path.exists():
            return docs
        for md_file in sorted(path.glob("*.md")):
            words = md_file.read_text(encoding="utf-8").split()
            if not words:
                continue
            step = CHUNK_SIZE - CHUNK_OVERLAP
            chunk_index = 0
            for i in range(0, len(words), step):
                chunk_words = words[i : i + CHUNK_SIZE]
                if not chunk_words:
                    break
                docs.append(
                    {
                        "content": " ".join(chunk_words),
                        "source": md_file.name,
                        "citation": md_file.name,
                        "doc_type": self._infer_doc_type(md_file.name),
                        "chunk_index": chunk_index,
                    }
                )
                chunk_index += 1
        return docs

    @staticmethod
    def _infer_doc_type(filename: str) -> str:
        lower = filename.lower()
        if "earnings" in lower:
            return "earnings"
        if "macro" in lower:
            return "macro"
        if "sector" in lower:
            return "sector"
        return "knowledge"

    def health_check(self) -> dict[str, Any]:
        if self.fallback or self.client is None:
            return {
                "available": bool(self._local_docs),
                "mode": "local_fallback",
                "docs_loaded": len(self._local_docs),
                "index": self.index_name,
            }
        try:
            list(self.client.search(search_text="market", top=1))
            return {"available": True, "mode": "azure_search", "index": self.index_name}
        except Exception:
            return {"available": False, "mode": "error", "index": self.index_name}

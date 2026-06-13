"""
Foundry IQ — Grounded knowledge retrieval layer.

DEMO: Azure AI Search (free tier F1) over synthetic knowledge documents.
PRODUCTION: Azure AI Search with semantic ranking, permission filters,
and multi-source connectors (SharePoint, OneLake, Blob Storage).

The agent contract is identical in both cases:
retrieve(query) -> list of {content, citation, score}
"""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

import os

logger = logging.getLogger(__name__)


def _setting(name: str, default: str = "") -> str:
    try:
        from django.conf import settings as django_settings

        return getattr(django_settings, name, default) or os.getenv(name, default)
    except Exception:
        return os.getenv(name, default)

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "documents"
CHUNK_SIZE = 400
CHUNK_OVERLAP = 50


class FoundryIQClient:
    """Grounded knowledge retrieval via Azure AI Search with local fallback."""

    def __init__(self) -> None:
        endpoint = (_setting("AZURE_SEARCH_ENDPOINT") or "").strip()
        key = _setting("AZURE_SEARCH_KEY")
        index_name = _setting("AZURE_SEARCH_INDEX_NAME", "fintelliops-knowledge")
        self.index_name = index_name
        self.available = bool(endpoint and key)
        self.fallback = not self.available
        self.client = None

        if self.available:
            try:
                from azure.core.credentials import AzureKeyCredential
                from azure.search.documents import SearchClient

                self.client = SearchClient(
                    endpoint=endpoint,
                    index_name=index_name,
                    credential=AzureKeyCredential(key),
                )
            except Exception as exc:
                logger.warning("Azure Search init failed, using local fallback: %s", exc)
                self.fallback = True
                self.available = False
        else:
            logger.warning("Azure Search not configured — local fallback active")

        self._local_docs = self._load_local_docs(str(DATA_DIR))

    def retrieve(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        if self.fallback or not self.available or self.client is None:
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
            logger.warning("Azure Search query failed, using local fallback: %s", exc)
            return self._local_retrieve(query, top_k)

    def _local_retrieve(self, query: str, top_k: int) -> list[dict[str, Any]]:
        query_words = set(re.findall(r"\w+", query.lower()))
        if not query_words:
            return self._local_docs[:top_k]

        scored: list[tuple[float, dict[str, Any]]] = []
        for doc in self._local_docs:
            content_words = re.findall(r"\w+", doc["content"].lower())
            if not content_words:
                continue
            overlap = len(query_words & set(content_words))
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
            text = md_file.read_text(encoding="utf-8")
            words = text.split()
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
                        "doc_type": self._infer_doc_type(md_file.name),
                        "chunk_index": chunk_index,
                    }
                )
                chunk_index += 1
        return docs

    @staticmethod
    def _infer_doc_type(filename: str) -> str:
        lower = filename.lower()
        if "guide" in lower:
            return "guide"
        if "report" in lower:
            return "report"
        if "insights" in lower:
            return "insights"
        return "knowledge"

    def health_check(self) -> dict[str, Any]:
        mode = "local_fallback" if self.fallback else "azure_search"
        if self.fallback or self.client is None:
            return {
                "available": bool(self._local_docs),
                "mode": mode,
                "index": self.index_name,
            }
        try:
            list(self.client.search(search_text="certification", top=1))
            return {"available": True, "mode": mode, "index": self.index_name}
        except Exception as exc:
            logger.warning("Foundry IQ health check failed: %s", exc)
            return {
                "available": bool(self._local_docs),
                "mode": "local_fallback",
                "index": self.index_name,
            }

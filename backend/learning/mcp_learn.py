"""
Optional Microsoft Learn MCP integration.

When MCP_LEARN_ENABLED=true, agents can augment grounded content with
Microsoft Learn documentation via an MCP server. Falls back to local Foundry IQ.
"""
from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

MCP_LEARN_ENABLED = os.getenv("MCP_LEARN_ENABLED", "false").lower() == "true"
MCP_LEARN_SERVER_URL = os.getenv("MCP_LEARN_SERVER_URL", "")


def is_mcp_available() -> bool:
    return MCP_LEARN_ENABLED and bool(MCP_LEARN_SERVER_URL)


def search_learn_docs(query: str, top_k: int = 3) -> list[dict[str, Any]]:
    """
    Query Microsoft Learn via MCP when configured.
    Demo mode returns structured placeholder results.
    """
    if not is_mcp_available():
        return []

    try:
        import requests

        resp = requests.post(
            f"{MCP_LEARN_SERVER_URL.rstrip('/')}/tools/search",
            json={"query": query, "limit": top_k},
            timeout=10,
        )
        if resp.ok:
            return resp.json().get("results", [])
    except Exception as e:
        logger.warning("MCP Learn search failed: %s", e)

    return []


def augment_with_learn(query: str, local_results: list[dict[str, Any]]) -> dict[str, Any]:
    """Merge local Foundry IQ results with optional Microsoft Learn MCP results."""
    mcp_results = search_learn_docs(query)
    return {
        "local_sources": local_results,
        "learn_mcp_sources": mcp_results,
        "mcp_enabled": is_mcp_available(),
        "combined_count": len(local_results) + len(mcp_results),
    }

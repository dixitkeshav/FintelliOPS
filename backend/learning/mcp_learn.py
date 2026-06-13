"""Optional MCP Learn augmentation hook."""
from __future__ import annotations

import logging
from typing import Any

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def augment_with_learn(query: str, citations: list[dict[str, Any]]) -> dict[str, Any]:
    if not getattr(settings, "MCP_LEARN_ENABLED", False):
        return {"augmented": False, "sources": citations}

    server_url = getattr(settings, "MCP_LEARN_SERVER_URL", "") or ""
    if not server_url:
        return {"augmented": False, "sources": citations}

    try:
        resp = requests.post(
            f"{server_url.rstrip('/')}/retrieve",
            json={"query": query},
            timeout=10,
        )
        resp.raise_for_status()
        extra = resp.json().get("results", [])
        return {"augmented": True, "sources": citations + extra}
    except Exception as exc:
        logger.warning("MCP Learn augmentation failed: %s", exc)
        return {"augmented": False, "sources": citations}

"""
Synthetic financial news for offline agent pipeline testing.

All data is fabricated for demo and test runs — no real market feeds or PII.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DATA_PATH = Path(__file__).resolve().parent / "data" / "synthetic_articles.json"


def load_synthetic_articles(ticker: str | None = None) -> list[dict[str, Any]]:
    """Return synthetic articles for a ticker, falling back to DEFAULT."""
    with open(DATA_PATH, encoding="utf-8") as f:
        catalog = json.load(f)

    key = (ticker or "").strip().upper()
    if key and key in catalog:
        articles = catalog[key]
    elif key:
        # Partial match e.g. RELIANCE.NS → RELIANCE
        for k, items in catalog.items():
            if k != "DEFAULT" and key.startswith(k):
                articles = items
                break
        else:
            articles = catalog.get("DEFAULT", [])
    else:
        articles = catalog.get("DEFAULT", [])

    return [dict(a) for a in articles]


def aggregate_sentiment(articles: list[dict[str, Any]]) -> str:
    if not articles:
        return "neutral"
    pos = sum(1 for a in articles if (a.get("sentiment") or "").lower() == "positive")
    neg = sum(1 for a in articles if (a.get("sentiment") or "").lower() == "negative")
    if pos > neg and pos > len(articles) - pos - neg:
        return "positive"
    if neg > pos:
        return "negative"
    return "neutral"


def list_synthetic_tickers() -> list[str]:
    with open(DATA_PATH, encoding="utf-8") as f:
        return [k for k in json.load(f).keys() if k != "DEFAULT"]

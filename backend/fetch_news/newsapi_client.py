"""
NewsAPI client wrapper for consistent usage across backend modules.
Uses NEWSAPI_KEY from environment.
"""
from __future__ import annotations

import logging
import os
from datetime import date, datetime
from typing import Any, Optional

logger = logging.getLogger(__name__)

try:
    from newsapi import NewsApiClient
except Exception:  # pragma: no cover - optional import safety
    NewsApiClient = None  # type: ignore[assignment]


def _api_key() -> str:
    return (os.getenv("NEWSAPI_KEY") or "").strip()


def is_configured() -> bool:
    return bool(_api_key()) and NewsApiClient is not None


def _client() -> Optional[Any]:
    key = _api_key()
    if not key or NewsApiClient is None:
        return None
    try:
        return NewsApiClient(api_key=key)
    except Exception as exc:
        logger.warning("Failed to initialize NewsApiClient: %s", exc)
        return None


def _to_iso_date(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def _normalize_article(item: dict[str, Any]) -> dict[str, Any]:
    src = item.get("source") or {}
    source_name = src.get("name") if isinstance(src, dict) else "NewsAPI"
    return {
        "title": item.get("title") or "No Title",
        "summary": item.get("description") or item.get("content") or "",
        "url": item.get("url") or "#",
        "source": source_name or "NewsAPI",
        "time_published": item.get("publishedAt") or "",
    }


def get_everything(
    *,
    query: str,
    from_param: Any = None,
    to: Any = None,
    language: str = "en",
    sort_by: str = "publishedAt",
    page_size: int = 30,
    page: int = 1,
) -> list[dict[str, Any]]:
    client = _client()
    if client is None:
        return []
    try:
        payload = client.get_everything(
            q=query,
            from_param=_to_iso_date(from_param),
            to=_to_iso_date(to),
            language=language,
            sort_by=sort_by,
            page=page,
            page_size=max(1, min(page_size, 100)),
        )
    except Exception as exc:
        logger.warning("NewsAPI everything failed: %s", exc)
        return []

    articles = payload.get("articles") or []
    if not isinstance(articles, list):
        return []
    return [_normalize_article(x) for x in articles]


def fetch_market_news(limit: int = 30) -> list[dict[str, Any]]:
    query = "stocks OR markets OR finance OR nifty OR sensex OR federal reserve OR rbi"
    return get_everything(query=query, language="en", sort_by="publishedAt", page_size=limit)


def _normalize_news_symbol(symbol: str) -> str:
    """
    Map user/UI symbols to common NewsAPI query terms.
    This is important for indices where users often type NIFTY50 / ^NSEI / ^BSESN.
    """
    s = (symbol or "").strip().upper()
    s = s.replace(".NS", "").replace(".BO", "")
    alias = {
        "NIFTY50": "NIFTY",
        "NIFTY 50": "NIFTY",
        "^NSEI": "NIFTY",
        "^NSEBANK": "BANKNIFTY",
        "^BSESN": "SENSEX",
    }
    return alias.get(s, s)


def fetch_symbol_news(symbol: str, limit: int = 20, from_param: Any = None, to: Any = None) -> list[dict[str, Any]]:
    raw = (symbol or "").strip()
    sym = _normalize_news_symbol(raw)
    if not sym:
        return []
    # Indices need broader query terms — headlines rarely contain the user's exact ticker input.
    is_index = sym in {"NIFTY", "BANKNIFTY", "SENSEX"}
    if is_index:
        if sym == "NIFTY":
            name = '(NIFTY OR "NIFTY 50" OR NSEI)'
        elif sym == "BANKNIFTY":
            name = '(BANKNIFTY OR "BANK NIFTY" OR NSEBANK)'
        else:
            name = '(SENSEX OR "BSE SENSEX" OR BSESN)'
        query = f"{name} AND (index OR market OR stocks OR derivatives OR options OR futures OR expiry OR RBI)"
    else:
        query = f'"{sym}" AND (stock OR shares OR earnings OR market)'
    items = get_everything(
        query=query,
        from_param=from_param,
        to=to,
        language="en",
        sort_by="publishedAt",
        page_size=limit,
    )
    # Some plans/providers return sparse results with strict date bounds; retry unbounded.
    if not items and (from_param or to):
        items = get_everything(
            query=query,
            language="en",
            sort_by="publishedAt",
            page_size=limit,
        )
    return items


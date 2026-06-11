"""
Merge NewsAPI, yfinance, Finnhub, and Alpha Vantage into one deduplicated feed with FinBERT sentiment.
"""
from __future__ import annotations

import hashlib
import logging
import os
from typing import Any, Optional

import requests

from fetch_news import finnhub_client as fh
from fetch_news import newsapi_client as na
from fetch_news.newsapi_client import _normalize_news_symbol

logger = logging.getLogger(__name__)

ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "")


def _article_key(item: dict[str, Any]) -> str:
    url = (item.get("url") or "").strip()
    if url and url != "#":
        return hashlib.md5(url.encode()).hexdigest()
    title = (item.get("title") or "").strip().lower()
    return hashlib.md5(title.encode()).hexdigest()


def _with_finbert(item: dict[str, Any]) -> dict[str, Any]:
    from fetch_news.sentiment import analyze_financial_sentiment

    text = f"{item.get('title', '')} {item.get('summary', '')}".strip()[:2000]
    if not text:
        return {**item, "sentiment": "neutral", "sentiment_score": 0.0}
    try:
        label, probs = analyze_financial_sentiment(text)
        lab = (label or "neutral").lower()
        score = 0.0
        if probs is not None and len(probs) >= 3:
            score = float(probs[2]) - float(probs[0])
        return {
            **item,
            "sentiment": lab,
            "sentiment_score": round(score, 4),
            "sentiment_probs": {
                "negative": float(probs[0]) if probs is not None else 0,
                "neutral": float(probs[1]) if probs is not None and len(probs) > 1 else 0,
                "positive": float(probs[2]) if probs is not None and len(probs) > 2 else 0,
            },
        }
    except Exception as exc:
        logger.debug("FinBERT failed: %s", exc)
        return {**item, "sentiment": item.get("sentiment", "neutral"), "sentiment_score": 0.0}


def _fetch_yfinance_news(symbol: str, limit: int = 15) -> list[dict[str, Any]]:
    sym = _normalize_news_symbol(symbol)
    yf_sym = sym
    if sym not in ("NIFTY", "BANKNIFTY", "SENSEX") and "." not in sym:
        yf_sym = f"{sym}.NS"
    try:
        import yfinance as yf

        raw = getattr(yf.Ticker(yf_sym), "news", None) or []
        out: list[dict[str, Any]] = []
        for row in raw[:limit]:
            if not isinstance(row, dict):
                continue
            title = row.get("title") or ""
            if not title:
                continue
            pub = row.get("providerPublishTime")
            time_published = ""
            if pub:
                try:
                    from datetime import datetime

                    time_published = datetime.utcfromtimestamp(int(pub)).isoformat() + "Z"
                except Exception:
                    pass
            out.append(
                {
                    "title": title,
                    "summary": row.get("summary") or title,
                    "url": row.get("link") or row.get("url") or "#",
                    "source": (row.get("publisher") or "Yahoo Finance"),
                    "time_published": time_published,
                    "provider": "yfinance",
                }
            )
        return out
    except Exception as exc:
        logger.debug("yfinance news for %s: %s", yf_sym, exc)
        return []


def _fetch_finnhub_news(symbol: str, limit: int = 15) -> list[dict[str, Any]]:
    if not fh.is_configured():
        return []
    try:
        items = fh.company_news(symbol, days=14) or []
        out: list[dict[str, Any]] = []
        for item in items[:limit]:
            title = item.get("title") or item.get("headline") or ""
            if not title:
                continue
            out.append(
                {
                    "title": title,
                    "summary": item.get("summary") or title,
                    "url": item.get("url") or "#",
                    "source": item.get("source") or "Finnhub",
                    "time_published": item.get("time_published") or item.get("datetime") or "",
                    "provider": "finnhub",
                }
            )
        return out
    except Exception as exc:
        logger.debug("finnhub news for %s: %s", symbol, exc)
        return []


def _fetch_alpha_vantage_news(symbol: str, limit: int = 15) -> list[dict[str, Any]]:
    if not ALPHA_VANTAGE_API_KEY or ALPHA_VANTAGE_API_KEY == "YOUR_API_KEY_HERE":
        return []
    sym = _normalize_news_symbol(symbol)
    try:
        url = (
            "https://www.alphavantage.co/query"
            f"?function=NEWS_SENTIMENT&tickers={sym}&apikey={ALPHA_VANTAGE_API_KEY}&limit={limit}"
        )
        r = requests.get(url, timeout=15)
        feed = r.json().get("feed") or []
        out: list[dict[str, Any]] = []
        for item in feed[:limit]:
            title = item.get("title") or ""
            if not title:
                continue
            out.append(
                {
                    "title": title,
                    "summary": item.get("summary") or title,
                    "url": item.get("url") or "#",
                    "source": item.get("source") or "Alpha Vantage",
                    "time_published": item.get("time_published") or "",
                    "sentiment": (item.get("overall_sentiment_label") or "Neutral").lower(),
                    "provider": "alpha_vantage",
                }
            )
        return out
    except Exception as exc:
        logger.debug("alpha vantage news for %s: %s", symbol, exc)
        return []


def fetch_merged_news(
    symbol: Optional[str] = None,
    *,
    limit: int = 40,
    run_finbert: bool = True,
    include_market: bool = False,
) -> dict[str, Any]:
    """
    Returns { articles, sources, counts }.
    Primary providers: NewsAPI → yfinance → Finnhub → Alpha Vantage.
    """
    merged: dict[str, dict[str, Any]] = {}
    source_counts: dict[str, int] = {
        "newsapi": 0,
        "yfinance": 0,
        "finnhub": 0,
        "alpha_vantage": 0,
    }

    def add_batch(rows: list[dict[str, Any]], provider: str) -> None:
        for row in rows:
            key = _article_key(row)
            if key in merged:
                continue
            row = {**row, "provider": provider}
            merged[key] = row
            source_counts[provider] = source_counts.get(provider, 0) + 1

    if symbol:
        sym = symbol.strip().upper()
        if na.is_configured():
            add_batch(
                [
                    {
                        "title": i.get("title", ""),
                        "summary": i.get("summary", ""),
                        "url": i.get("url", "#"),
                        "source": i.get("source", "NewsAPI"),
                        "time_published": i.get("time_published", ""),
                    }
                    for i in na.fetch_symbol_news(sym, limit=min(limit, 30))
                ],
                "newsapi",
            )
        add_batch(_fetch_yfinance_news(sym, limit=min(limit, 20)), "yfinance")
        add_batch(_fetch_finnhub_news(sym, limit=min(limit, 15)), "finnhub")
        add_batch(_fetch_alpha_vantage_news(sym, limit=min(limit, 15)), "alpha_vantage")
    elif include_market or not symbol:
        if na.is_configured():
            add_batch(
                [
                    {
                        "title": i.get("title", ""),
                        "summary": i.get("summary", ""),
                        "url": i.get("url", "#"),
                        "source": i.get("source", "NewsAPI"),
                        "time_published": i.get("time_published", ""),
                    }
                    for i in na.fetch_market_news(limit=min(limit, 30))
                ],
                "newsapi",
            )
        if fh.is_configured():
            add_batch(
                [
                    {
                        "title": i.get("title", ""),
                        "summary": i.get("summary", ""),
                        "url": i.get("url", "#"),
                        "source": i.get("source") or "Finnhub",
                        "time_published": i.get("time_published", ""),
                    }
                    for i in fh.market_news("general")[: min(limit, 20)]
                ],
                "finnhub",
            )

    articles = list(merged.values())[:limit]
    if run_finbert:
        articles = [_with_finbert(a) for a in articles]

    providers = [p for p, c in source_counts.items() if c > 0]
    source_label = "+".join(providers) if providers else "none"

    return {
        "articles": articles,
        "sources": source_counts,
        "source": source_label,
        "total": len(articles),
    }

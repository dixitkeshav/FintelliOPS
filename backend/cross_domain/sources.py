"""
Cross-domain news: crypto, commodities, FX, geopolitical.
Uses NewsAPI queries (with Alpha Vantage fallback when needed).
"""
import logging
import os
from typing import Any

import requests
from fetch_news import newsapi_client as na

logger = logging.getLogger(__name__)

ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
BASE_URL = "https://www.alphavantage.co/query"

# Topic mapping for Alpha Vantage NEWS_SENTIMENT
TOPICS = {
    "crypto": "blockchain",
    "commodities": "commodities",
    "fx": "economy_fiscal",
    "geopolitical": "economy_macro",
    "earnings": "earnings",
    "ipo": "ipo",
    "mergers": "mergers_and_acquisitions",
    "financial_markets": "financial_markets",
}


def fetch_domain_news(domain: str, limit: int = 20) -> list[dict]:
    """Fetch news for a domain (crypto, commodities, fx, geopolitical, etc.)."""
    topic = TOPICS.get(domain.lower(), "financial_markets")
    query_by_domain = {
        "crypto": "bitcoin OR ethereum OR crypto market",
        "commodities": "commodities OR crude oil OR gold OR metal prices",
        "fx": "forex OR currency market OR dollar index",
        "geopolitical": "geopolitical OR sanctions OR war OR trade tensions",
        "earnings": "earnings results OR quarterly results",
        "ipo": "IPO OR listed today",
        "mergers": "merger OR acquisition deal",
        "financial_markets": "stock market OR equity market OR bonds OR central bank",
    }
    if na.is_configured():
        items = na.get_everything(
            query=query_by_domain.get(domain.lower(), query_by_domain["financial_markets"]),
            language="en",
            sort_by="publishedAt",
            page_size=limit,
        )
        if items:
            return [
                {
                    "title": item.get("title", ""),
                    "summary": item.get("summary", ""),
                    "url": item.get("url", ""),
                    "sentiment": "neutral",
                    "domain": domain,
                }
                for item in items[:limit]
            ]
    if not ALPHA_VANTAGE_API_KEY:
        return []
    try:
        r = requests.get(
            BASE_URL,
            params={"function": "NEWS_SENTIMENT", "apikey": ALPHA_VANTAGE_API_KEY, "limit": limit, "topics": topic},
            timeout=15,
        )
        if r.status_code != 200:
            return []
        feed = r.json().get("feed", [])
        return [
            {
                "title": item.get("title", ""),
                "summary": item.get("summary", ""),
                "url": item.get("url", ""),
                "sentiment": (item.get("overall_sentiment_label") or "Neutral").lower(),
                "domain": domain,
            }
            for item in feed[:limit]
        ]
    except Exception as e:
        logger.exception("fetch_domain_news %s failed: %s", domain, e)
        return []


def cross_domain_reasoning(domain_insights: dict[str, Any]) -> str:
    """
    Simple cross-domain reasoning: e.g. geopolitical tension -> oil -> inflation -> banks.
    Can be replaced with LLM call.
    """
    parts = []
    if domain_insights.get("geopolitical") and "negative" in str(domain_insights.get("geopolitical", "")).lower():
        parts.append("Geopolitical tension often supports oil prices and inflation risk.")
    if domain_insights.get("commodities"):
        parts.append("Commodity moves can feed into inflation expectations and rate expectations.")
    if domain_insights.get("fx"):
        parts.append("FX volatility can impact EM and risk assets.")
    if not parts:
        return "Cross-domain view: aggregate news sentiment across assets for a broader risk view."
    return " ".join(parts) + " Consider impact on rates and bank/equity sectors."

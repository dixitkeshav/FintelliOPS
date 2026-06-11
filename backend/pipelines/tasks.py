"""
Celery tasks for async news ingestion and sentiment processing.
"""
import logging
import os
from typing import Any

from fetch_news import newsapi_client as na

logger = logging.getLogger(__name__)

# Only define tasks if Celery is configured (Redis available)
try:
    from celery import shared_task
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    def shared_task(*args, **kwargs):
        def decorator(f):
            return f
        return decorator


def _fetch_newsapi_news(ticker: str = "", topic: str = "financial_markets") -> list:
    if na.is_configured():
        query_map = {
            "financial_markets": "stock market OR financial markets OR central bank",
            "economy_macro": "macroeconomy OR inflation OR interest rates",
            "commodities": "commodities OR crude oil OR gold",
            "blockchain": "crypto OR bitcoin OR ethereum",
        }
        query = query_map.get(topic, query_map["financial_markets"])
        if ticker:
            query = f'"{ticker}" AND ({query})'
        items = na.get_everything(query=query, language="en", sort_by="publishedAt", page_size=50)
        return [
            {
                "title": x.get("title", ""),
                "summary": x.get("summary", ""),
                "url": x.get("url", ""),
                "overall_sentiment_label": "Neutral",
                "ticker_sentiment": [],
            }
            for x in items
        ]

    # Alpha Vantage fallback for compatibility.
    import requests
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    if not api_key:
        return []
    url = "https://www.alphavantage.co/query"
    params = {"function": "NEWS_SENTIMENT", "apikey": api_key, "limit": 50}
    if ticker:
        params["tickers"] = ticker
    if topic:
        params["topics"] = topic
    r = requests.get(url, params=params, timeout=15)
    if r.status_code != 200:
        return []
    data = r.json()
    return data.get("feed", [])


@shared_task(bind=True, max_retries=3)
def ingest_news_task(self, ticker: str = "", topic: str = "financial_markets") -> dict[str, Any]:
    """Async task: fetch news and optionally run sentiment + store."""
    if not CELERY_AVAILABLE:
        return {"status": "skipped", "reason": "Celery not installed"}
    try:
        from pipelines.ingestion import fetch_news_with_retry
        feed = fetch_news_with_retry(lambda: _fetch_newsapi_news(ticker, topic), source="newsapi")
        if not feed:
            return {"status": "ok", "count": 0, "articles": []}
        articles = [
            {
                "title": item.get("title", ""),
                "summary": item.get("summary", ""),
                "url": item.get("url", ""),
                "sentiment": (item.get("overall_sentiment_label") or "Neutral").lower(),
                "ticker_sentiment": item.get("ticker_sentiment", []),
            }
            for item in feed[:30]
        ]
        return {"status": "ok", "count": len(articles), "articles": articles}
    except Exception as e:
        logger.exception("ingest_news_task failed: %s", e)
        raise self.retry(exc=e)

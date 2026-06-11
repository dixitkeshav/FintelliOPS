import hashlib
import logging
from datetime import timedelta

import feedparser
from django.core.cache import cache
from fetch_news import newsapi_client as na

logger = logging.getLogger(__name__)

RSS_FEEDS = {
    'RBI': 'https://www.rbi.org.in/Scripts/RSS.aspx',
    'SEBI': 'https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListingAll=yes&sid=1&ssid=3&smid=0',
    'ET': 'https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms',
    'MC': 'https://www.moneycontrol.com/rss/marketsbuzz.xml',
    'MINT': 'https://www.livemint.com/rss/markets',
    'BS': 'https://www.business-standard.com/rss/markets-106.rss',
}

SOURCE_WEIGHTS = {
    'RBI': 1.0,
    'SEBI': 1.0,
    'ET': 0.75,
    'MC': 0.70,
    'MINT': 0.70,
    'BS': 0.70,
}


def fetch_headlines_for_date(target_date, index_name: str = "NIFTY") -> str:
    """Historical headlines via NewsAPI (backtest). Requires NEWSAPI_KEY in settings."""
    bundle = fetch_headlines_bundle_for_date(target_date, index_name=index_name)
    return bundle.get("combined_text") or _fallback_headline_for_date(target_date)


def fetch_headlines_bundle_for_date(target_date, index_name: str = "NIFTY") -> dict:
    """
    Fetch multiple headlines for a shock day; used for cause classification.
    Returns { combined_text, headlines: [{title, summary, source}], top_title }.
    """
    date_str = target_date.strftime("%Y-%m-%d")
    next_day = (target_date + timedelta(days=1)).strftime("%Y-%m-%d")
    idx = (index_name or "NIFTY").upper()
    query = (
        f"(NIFTY OR sensex OR banknifty OR {idx}) AND "
        "(market OR stocks OR RBI OR SEBI OR budget OR tax OR policy OR crash OR rally OR index)"
    )
    headlines: list[dict] = []
    if na.is_configured():
        try:
            articles = na.get_everything(
                query=query,
                from_param=date_str,
                to=next_day,
                language="en",
                sort_by="relevancy",
                page_size=15,
            )
            for a in articles or []:
                headlines.append(
                    {
                        "title": a.get("title", ""),
                        "summary": (a.get("summary") or "")[:400],
                        "source": a.get("source", "NewsAPI"),
                        "url": a.get("url", "#"),
                    }
                )
        except Exception as e:
            logger.debug("NewsAPI fetch failed for %s: %s", target_date, e)

    if not headlines:
        fb = _fallback_headline_for_date(target_date)
        headlines = [{"title": fb, "summary": fb, "source": "fallback"}]

    combined = " ".join(
        f"{h.get('title', '')}. {h.get('summary', '')}" for h in headlines[:8]
    )
    return {
        "combined_text": combined[:4000],
        "headlines": headlines[:10],
        "top_title": headlines[0].get("title", "") if headlines else "",
    }


def _fallback_headline_for_date(target_date) -> str:
    """Keyword-only fallback when NewsAPI is unavailable."""
    return (
        f"Nifty market session on {target_date.isoformat()} — "
        "Indian equities volatile amid global and domestic factors."
    )


def poll_feed(source_name: str, feed_url: str) -> list[dict]:
    """Poll one RSS feed; dedupe via Redis cache."""
    new_entries = []
    try:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:20]:
            uid = hashlib.md5(
                (entry.get('link', '') + entry.get('title', '')).encode()
            ).hexdigest()
            cache_key = f"shock:seen:{uid}"
            if cache.get(cache_key):
                continue
            cache.set(cache_key, 1, timeout=86400)
            new_entries.append({
                'uid': uid,
                'source': source_name,
                'title': entry.get('title', ''),
                'summary': entry.get('summary', ''),
                'link': entry.get('link', ''),
                'published': entry.get('published', ''),
                'full_text': entry.get('title', '') + '. ' + entry.get('summary', ''),
                'weight': SOURCE_WEIGHTS.get(source_name, 0.5),
            })
    except Exception as e:
        logger.debug("RSS poll failed %s: %s", source_name, e)
    return new_entries


def poll_all_feeds() -> list[dict]:
    results = []
    for source, url in RSS_FEEDS.items():
        results.extend(poll_feed(source, url))
    return results

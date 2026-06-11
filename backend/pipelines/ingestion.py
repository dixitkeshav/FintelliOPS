"""
Rate-limit safe news ingestion. Can be called synchronously or via Celery.
"""
import logging
import time
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)

# Simple in-memory rate limit (per source). Redis can replace this.
_last_call: dict[str, float] = {}
_min_interval = 1.5  # Keep small delay to avoid bursty provider calls.


def rate_limit_safe(source: str = "default") -> bool:
    """Returns True if enough time has passed since last call."""
    now = time.time()
    last = _last_call.get(source, 0)
    if now - last < _min_interval:
        return False
    _last_call[source] = now
    return True


def fetch_news_with_retry(
    fetch_fn: Callable[[], Any],
    max_retries: int = 2,
    source: str = "newsapi",
) -> Any:
    """Call fetch_fn with rate limiting and retries."""
    for attempt in range(max_retries + 1):
        if not rate_limit_safe(source):
            if attempt == 0:
                time.sleep(_min_interval)
                continue
        try:
            return fetch_fn()
        except Exception as e:
            logger.warning("Ingestion attempt %s failed: %s", attempt + 1, e)
            if attempt < max_retries:
                time.sleep(2 ** attempt)
    return None

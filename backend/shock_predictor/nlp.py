"""
FinBERT + keyword cause classification for shock events.
Reuses the project's lazy-loaded FinBERT in fetch_news.sentiment (no second model load).
"""
from fetch_news.sentiment import analyze_financial_sentiment

CAUSE_KEYWORDS = {
    'policy': [
        'rbi', 'repo rate', 'monetary policy', 'sebi', 'regulation', 'circular',
        'rate cut', 'rate hike', 'fema', 'fii limit', 'circuit breaker', 'ban',
        'budget', 'tax', 'gst', 'fiscal policy', 'finance minister',
    ],
    'macro': [
        'gdp', 'inflation', 'cpi', 'fed', 'federal reserve', 'dollar', 'crude oil',
        'recession', 'current account', 'trade deficit', 'imf', 'world bank',
        'global slowdown', 'china', 'us economy',
    ],
    'geopolitical': [
        'war', 'conflict', 'sanctions', 'election', 'terror', 'attack',
        'geopolitical', 'border', 'pakistan', 'nuclear', 'oil embargo',
    ],
    'technical': [
        'fii selling', 'fii outflow', 'dii buying', 'margin call', 'circuit',
        'block deal', 'bulk deal', 'expiry', 'short covering', 'stop loss',
        'unwinding', 'derivative', 'rollover',
    ],
    'corporate': [
        'earnings', 'results', 'profit', 'loss', 'default', 'insolvency',
        'merger', 'acquisition', 'ipo', 'delisting', 'fraud', 'scam',
    ],
}


def get_finbert_sentiment(text: str) -> float:
    """
    Returns a float in [-1, 1] using existing FinBERT (negative / neutral / positive).
    """
    if not text or len(text.strip()) < 5:
        return 0.0
    try:
        label, probs = analyze_financial_sentiment(text[:512])
        if not probs or len(probs) < 3:
            return 0.0
        neg, neu, pos = float(probs[0]), float(probs[1]), float(probs[2])
        if label == 'positive':
            return pos - neg
        if label == 'negative':
            return -(neg - pos)
        return pos - neg
    except Exception:
        return 0.0


def _keyword_in_text(keyword: str, text_lower: str) -> bool:
    """Match whole words/phrases so e.g. 'ban' does not match 'banknifty'."""
    import re
    if ' ' in keyword:
        return keyword in text_lower
    return bool(re.search(rf'\b{re.escape(keyword)}\b', text_lower))


def classify_cause_type(headline: str, date=None) -> tuple[str, str]:
    """
    Rule-based keyword classifier. Returns (cause_type, summary_string).
    """
    return classify_cause_from_text(headline, date=date)


def classify_cause_from_text(
    text: str,
    date=None,
    headlines: list | None = None,
) -> tuple[str, str]:
    """
    Classify shock cause from combined text and optional headline list.
    """
    parts = [text or ""]
    if headlines:
        for h in headlines:
            if isinstance(h, dict):
                parts.append(h.get("title", ""))
                parts.append(h.get("summary", ""))
            else:
                parts.append(str(h))
    blob = " ".join(parts).lower()
    scores = {}
    matched_kw: dict[str, list[str]] = {k: [] for k in CAUSE_KEYWORDS}
    for cause, keywords in CAUSE_KEYWORDS.items():
        for kw in keywords:
            if _keyword_in_text(kw, blob):
                scores[cause] = scores.get(cause, 0) + 1
                matched_kw[cause].append(kw)

    best_cause = max(scores, key=scores.get) if scores else "unknown"
    if scores.get(best_cause, 0) == 0:
        best_cause = "unknown"

    date_s = f" on {date}" if date else ""
    top_h = ""
    if headlines and isinstance(headlines[0], dict):
        top_h = (headlines[0].get("title") or "")[:160]
    elif text:
        top_h = text[:160]

    kw_sample = ", ".join(matched_kw.get(best_cause, [])[:5])
    summary = (
        f"Likely {best_cause} shock{date_s}. "
        f"Matched keywords: {kw_sample or 'none'}. "
        f"Lead headline: {top_h}"
    )
    if best_cause == "unknown" and ("budget" in blob or "tax" in blob or "stt" in blob):
        best_cause = "policy"
        summary = (
            f"Policy/fiscal headline cluster{date_s} (budget/tax/STT keywords). Lead: {top_h}"
        )
    return best_cause, summary

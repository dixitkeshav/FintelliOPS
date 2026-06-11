"""
Sentiment-based quant signals: momentum, mean reversion, sector rotation.
"""
import logging
from typing import Any, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def sentiment_score_from_probs(probs: dict) -> float:
    """Map {negative, neutral, positive} probs to a score in [-1, 1]."""
    neg = probs.get("negative", 0) or 0
    neu = probs.get("neutral", 0) or 0
    pos = probs.get("positive", 0) or 0
    return float(pos - neg)


def sentiment_momentum(sentiment_series: pd.Series, window: int = 5) -> pd.Series:
    """Sentiment momentum: rolling change in average sentiment."""
    if sentiment_series is None or len(sentiment_series) < 2:
        return pd.Series(dtype=float)
    rolling = sentiment_series.rolling(window=min(window, len(sentiment_series)), min_periods=1).mean()
    return rolling.diff()


def sentiment_ma_crossover(sentiment_series: pd.Series, short: int = 3, long: int = 7) -> dict:
    """Signal: short MA crosses above/below long MA. Returns last signal."""
    if sentiment_series is None or len(sentiment_series) < long:
        return {"signal": 0, "short_ma": None, "long_ma": None}
    short_ma = sentiment_series.rolling(short, min_periods=1).mean()
    long_ma = sentiment_series.rolling(long, min_periods=1).mean()
    # 1 = bullish cross, -1 = bearish
    cross = np.sign(short_ma.iloc[-1] - long_ma.iloc[-1]) if len(sentiment_series) >= long else 0
    return {"signal": int(cross), "short_ma": float(short_ma.iloc[-1]), "long_ma": float(long_ma.iloc[-1])}


def extreme_sentiment_mean_reversion(sentiment: float, threshold: float = 0.7) -> int:
    """
    Extreme negative sentiment + rising volume → short-term mean reversion (bullish signal).
    Extreme positive → possible reversion down. Returns -1, 0, or 1.
    """
    if sentiment <= -threshold:
        return 1   # mean reversion long
    if sentiment >= threshold:
        return -1  # mean reversion short
    return 0


def build_signal_payload(
    sentiment_series: Optional[pd.Series] = None,
    last_probs: Optional[dict] = None,
    window: int = 5,
) -> dict[str, Any]:
    """Build a payload of quant signals for API."""
    payload = {"momentum": None, "ma_crossover": None, "mean_reversion": None}
    if last_probs:
        score = sentiment_score_from_probs(last_probs)
        payload["sentiment_score"] = score
        payload["mean_reversion"] = extreme_sentiment_mean_reversion(score)
    if sentiment_series is not None and len(sentiment_series) >= 2:
        mom = sentiment_momentum(sentiment_series, window)
        payload["momentum"] = float(mom.iloc[-1]) if len(mom) and pd.notna(mom.iloc[-1]) else None
        payload["ma_crossover"] = sentiment_ma_crossover(sentiment_series)
    return payload

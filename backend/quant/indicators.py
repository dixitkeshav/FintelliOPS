"""Technical indicators for backtesting."""
from __future__ import annotations

import numpy as np
import pandas as pd


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, 1e-10)
    return 100 - (100 / (1 + rs))


def mfi(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    volume: pd.Series,
    period: int = 14,
) -> pd.Series:
    typical = (high + low + close) / 3.0
    raw_money = typical * volume.replace(0, 1)
    delta = typical.diff()
    pos_flow = raw_money.where(delta > 0, 0.0)
    neg_flow = raw_money.where(delta < 0, 0.0)
    pos_sum = pos_flow.rolling(period, min_periods=period).sum()
    neg_sum = neg_flow.rolling(period, min_periods=period).sum()
    mfr = pos_sum / neg_sum.replace(0, 1e-10)
    return 100 - (100 / (1 + mfr))


def macd_histogram(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.Series:
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    return macd_line - signal_line


def bollinger_pct_b(close: pd.Series, period: int = 20, std_mult: float = 2.0) -> pd.Series:
    """Bollinger %B scaled 0-100 (50 = middle band)."""
    mid = close.rolling(period, min_periods=period).mean()
    std = close.rolling(period, min_periods=period).std()
    upper = mid + std_mult * std
    lower = mid - std_mult * std
    width = (upper - lower).replace(0, np.nan)
    pct_b = (close - lower) / width
    return (pct_b * 100).clip(0, 100)


def vwap_distance_pct(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    volume: pd.Series,
) -> pd.Series:
    """Rolling session-style VWAP distance: (close - vwap) / vwap * 100."""
    typical = (high + low + close) / 3.0
    vol = volume.fillna(0).replace(0, np.nan)
    cum_tpv = (typical * vol).cumsum()
    cum_vol = vol.cumsum()
    vwap = cum_tpv / cum_vol.replace(0, np.nan)
    return ((close - vwap) / vwap.replace(0, np.nan)) * 100.0


def zigzag_trend(close: pd.Series, pct_threshold: float = 3.0) -> pd.Series:
    """
    Simplified zigzag leg direction: 1 up-leg, -1 down-leg, 0 chop.
    """
    out = pd.Series(0.0, index=close.index)
    if len(close) < 3:
        return out
    last_pivot = float(close.iloc[0])
    direction = 0
    for i in range(1, len(close)):
        price = float(close.iloc[i])
        chg = (price - last_pivot) / last_pivot * 100 if last_pivot else 0
        if chg >= pct_threshold:
            direction = 1
            last_pivot = price
        elif chg <= -pct_threshold:
            direction = -1
            last_pivot = price
        out.iloc[i] = direction
    return out


def enrich_ohlc(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    vol = out["volume"].fillna(0) if "volume" in out.columns else pd.Series(0, index=out.index)
    out["rsi"] = rsi(out["close"])
    out["mfi"] = mfi(out["high"], out["low"], out["close"], vol)
    out["macd_hist"] = macd_histogram(out["close"])
    out["bb_pct"] = bollinger_pct_b(out["close"])
    out["vwap_dist"] = vwap_distance_pct(out["high"], out["low"], out["close"], vol)
    out["zigzag_trend"] = zigzag_trend(out["close"])
    return out

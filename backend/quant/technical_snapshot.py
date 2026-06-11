"""
Fundamental + technical snapshot for a symbol (price action, volume, indicators, candle hints).
"""
from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np
import pandas as pd

from quant.indicators import enrich_ohlc, rsi, mfi, macd_histogram, bollinger_pct_b, vwap_distance_pct

logger = logging.getLogger(__name__)


def _yf_symbol(symbol: str) -> str:
    s = (symbol or "").strip().upper().replace("$", "")
    if s in ("NIFTY", "NIFTY50", "NIFTY 50"):
        return "^NSEI"
    if s in ("SENSEX", "^BSESN"):
        return "^BSESN"
    if s in ("BANKNIFTY", "BANK NIFTY"):
        return "^NSEBANK"
    if "." not in s and not s.startswith("^"):
        return f"{s}.NS"
    return s


def _fetch_ohlc(symbol: str, period: str = "1y") -> Optional[pd.DataFrame]:
    try:
        import yfinance as yf

        hist = yf.Ticker(_yf_symbol(symbol)).history(period=period)
        if hist is None or hist.empty:
            return None
        df = pd.DataFrame(
            {
                "open": hist["Open"],
                "high": hist["High"],
                "low": hist["Low"],
                "close": hist["Close"],
                "volume": hist.get("Volume", 0),
            }
        )
        if getattr(df.index, "tz", None) is not None:
            df.index = df.index.tz_localize(None)
        return df.sort_index()
    except Exception as exc:
        logger.warning("OHLC fetch failed %s: %s", symbol, exc)
        return None


def _stoch_kd(high: pd.Series, low: pd.Series, close: pd.Series, k_period: int = 14, d_period: int = 3):
    lowest = low.rolling(k_period).min()
    highest = high.rolling(k_period).max()
    k = 100 * (close - lowest) / (highest - lowest).replace(0, np.nan)
    d = k.rolling(d_period).mean()
    return k, d


def _cci(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 20) -> pd.Series:
    tp = (high + low + close) / 3.0
    sma = tp.rolling(period).mean()
    mad = tp.rolling(period).apply(lambda x: np.abs(x - x.mean()).mean(), raw=True)
    return (tp - sma) / (0.015 * mad.replace(0, np.nan))


def _williams_r(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    highest = high.rolling(period).max()
    lowest = low.rolling(period).min()
    return -100 * (highest - close) / (highest - lowest).replace(0, np.nan)


def _atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    prev_close = close.shift(1)
    tr = pd.concat(
        [
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr.rolling(period).mean()


def _obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    direction = np.sign(close.diff()).fillna(0)
    return (direction * volume.fillna(0)).cumsum()


def _detect_candlestick_patterns(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Simple rule-based detection on last 3 bars."""
    if len(df) < 2:
        return []
    patterns: list[dict[str, Any]] = []
    o, h, l, c = df.iloc[-1]["open"], df.iloc[-1]["high"], df.iloc[-1]["low"], df.iloc[-1]["close"]
    body = abs(c - o)
    rng = h - l if h > l else 1e-9
    upper = h - max(o, c)
    lower = min(o, c) - l

    if body / rng < 0.1:
        patterns.append({"id": "doji", "name": "Doji", "bar": "last"})
    if lower > 2 * body and upper < body and c > o:
        patterns.append({"id": "hammer", "name": "Hammer", "bar": "last"})
    if upper > 2 * body and lower < body and c < o:
        patterns.append({"id": "shooting_star", "name": "Shooting Star", "bar": "last"})

    if len(df) >= 2:
        po, ph, pl, pc = df.iloc[-2][["open", "high", "low", "close"]]
        if pc < po and c > o and o <= pc and c >= po:
            patterns.append({"id": "engulfing_bull", "name": "Bullish Engulfing", "bar": "last"})
        if pc > po and c < o and o >= pc and c <= po:
            patterns.append({"id": "engulfing_bear", "name": "Bearish Engulfing", "bar": "last"})

    return patterns


def build_technical_snapshot(symbol: str, selected_indicators: Optional[list[str]] = None) -> dict[str, Any]:
    df = _fetch_ohlc(symbol)
    if df is None or len(df) < 30:
        return {"error": f"Insufficient OHLC for {symbol}", "symbol": symbol}

    vol = df["volume"].fillna(0)
    close = df["close"]
    high, low = df["high"], df["low"]

    enriched = enrich_ohlc(df)
    last = enriched.iloc[-1]
    prev = enriched.iloc[-2] if len(enriched) > 1 else last

    stoch_k, stoch_d = _stoch_kd(high, low, close)
    cci_s = _cci(high, low, close)
    wr = _williams_r(high, low, close)
    atr_s = _atr(high, low, close)
    obv_s = _obv(close, vol)
    macd_h = macd_histogram(close)
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()

    ret_1d = float((close.iloc[-1] / close.iloc[-2] - 1) * 100) if len(close) > 1 else 0.0
    ret_5d = float((close.iloc[-1] / close.iloc[-5] - 1) * 100) if len(close) > 5 else 0.0
    ret_21d = float((close.iloc[-1] / close.iloc[-22] - 1) * 100) if len(close) > 22 else 0.0
    vol_sma = vol.rolling(20).mean().iloc[-1] or 1
    vol_ratio = float(vol.iloc[-1] / vol_sma) if vol_sma else 1.0

    high_52 = float(close.max())
    low_52 = float(close.min())
    last_c = float(close.iloc[-1])

    all_indicators = {
        "rsi": round(float(last["rsi"]), 2) if pd.notna(last.get("rsi")) else None,
        "mfi": round(float(last["mfi"]), 2) if pd.notna(last.get("mfi")) else None,
        "macd_hist": round(float(last["macd_hist"]), 4) if pd.notna(last.get("macd_hist")) else None,
        "bb_pct": round(float(last["bb_pct"]), 2) if pd.notna(last.get("bb_pct")) else None,
        "vwap_dist": round(float(last["vwap_dist"]), 2) if pd.notna(last.get("vwap_dist")) else None,
        "zigzag_trend": int(last["zigzag_trend"]) if pd.notna(last.get("zigzag_trend")) else 0,
        "stoch_k": round(float(stoch_k.iloc[-1]), 2) if pd.notna(stoch_k.iloc[-1]) else None,
        "stoch_d": round(float(stoch_d.iloc[-1]), 2) if pd.notna(stoch_d.iloc[-1]) else None,
        "cci": round(float(cci_s.iloc[-1]), 2) if pd.notna(cci_s.iloc[-1]) else None,
        "williams_r": round(float(wr.iloc[-1]), 2) if pd.notna(wr.iloc[-1]) else None,
        "atr": round(float(atr_s.iloc[-1]), 2) if pd.notna(atr_s.iloc[-1]) else None,
        "atr_pct": round(float(atr_s.iloc[-1] / last_c * 100), 2) if last_c else None,
        "obv": round(float(obv_s.iloc[-1]), 0),
        "sma_20": round(float(close.rolling(20).mean().iloc[-1]), 2),
        "sma_50": round(float(close.rolling(50).mean().iloc[-1]), 2) if len(close) >= 50 else None,
        "sma_200": round(float(close.rolling(200).mean().iloc[-1]), 2) if len(close) >= 200 else None,
        "ema_12": round(float(ema12.iloc[-1]), 2),
        "ema_26": round(float(ema26.iloc[-1]), 2),
        "return_1d": round(ret_1d, 2),
        "return_5d": round(ret_5d, 2),
        "return_21d": round(ret_21d, 2),
        "volume_sma_ratio": round(vol_ratio, 2),
        "high_52w_dist": round((last_c / high_52 - 1) * 100, 2) if high_52 else None,
        "low_52w_dist": round((last_c / low_52 - 1) * 100, 2) if low_52 else None,
        "last_close": round(last_c, 2),
    }

    if selected_indicators:
        indicators = {k: v for k, v in all_indicators.items() if k in selected_indicators or k == "last_close"}
    else:
        indicators = all_indicators

    # Trend label
    sma20 = all_indicators.get("sma_20") or last_c
    sma50 = all_indicators.get("sma_50") or sma20
    if last_c > sma20 > sma50:
        trend = "bullish"
    elif last_c < sma20 < sma50:
        trend = "bearish"
    else:
        trend = "neutral"

    patterns = _detect_candlestick_patterns(df.tail(5))

    summary_parts = [
        f"Last {last_c:.2f}",
        f"Trend: {trend}",
        f"RSI {indicators.get('rsi', '—')}",
        f"MFI {indicators.get('mfi', '—')}",
        f"21d return {ret_21d:.1f}%",
        f"Vol ratio {vol_ratio:.2f}x",
    ]
    if patterns:
        summary_parts.append("Patterns: " + ", ".join(p["name"] for p in patterns[:3]))

    return {
        "symbol": symbol,
        "trend": trend,
        "summary": ". ".join(summary_parts),
        "indicators": indicators,
        "candlestick_patterns": patterns,
        "price_action": {
            "return_1d_pct": ret_1d,
            "return_5d_pct": ret_5d,
            "return_21d_pct": ret_21d,
            "volume_vs_20d": vol_ratio,
        },
        "bars": len(df),
    }

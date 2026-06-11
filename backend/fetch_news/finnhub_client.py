"""
Finnhub REST client (quotes, candles, news, option chain).
Uses FINNHUB_API_KEY from environment. FINNHUB_SECRET is not used by public REST API.
"""
from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import requests

logger = logging.getLogger(__name__)

BASE = "https://finnhub.io/api/v1"


def _token() -> str:
    return (os.getenv("FINNHUB_API_KEY") or "").strip()


def is_configured() -> bool:
    return bool(_token())


def _get(path: str, params: dict[str, Any]) -> Optional[dict[str, Any]]:
    token = _token()
    if not token:
        return None
    p = {"token": token, **params}
    try:
        r = requests.get(f"{BASE}{path}", params=p, timeout=20)
        if r.status_code != 200:
            logger.warning("Finnhub %s %s: %s", path, r.status_code, r.text[:200])
            return None
        return r.json()
    except Exception as e:
        logger.warning("Finnhub request failed %s: %s", path, e)
        return None


def map_yahoo_to_finnhub(symbol: str) -> str:
    """
    Map Yahoo-style symbols to Finnhub symbols where needed.
    Finnhub US equities: AAPL. India: NSE:RELIANCE. Indices: OANDA:* or ETF proxies.
    """
    s = (symbol or "").strip().upper()
    if not s:
        return s
    if ":" in s:
        return s
    if s.endswith(".NS"):
        return f"NSE:{s[:-3]}"
    if s.endswith(".BO"):
        return f"BSE:{s[:-3]}"
    # Major indices (Yahoo -> Finnhub/OANDA or liquid ETF proxy)
    index_map = {
        "^GSPC": "OANDA:SPX500_USD",
        "^DJI": "OANDA:US30_USD",
        "^IXIC": "OANDA:NAS100_USD",
        "^NSEI": "NSE:NIFTY",
        "^BSESN": "BSE:SENSEX",
        "^N225": "OANDA:JP225_USD",
        "^FTSE": "OANDA:UK100_GBP",
        "^GDAXI": "OANDA:DE30_EUR",
    }
    return index_map.get(s, s)


def quote(symbol: str) -> Optional[dict[str, Any]]:
    """GET /quote — returns c, d, dp, h, l, o, pc, t"""
    fh = map_yahoo_to_finnhub(symbol)
    data = _get("/quote", {"symbol": fh})
    if not data or data.get("c") in (None, 0) and data.get("pc") in (None, 0):
        # Try raw symbol if mapped failed
        if fh != symbol:
            data = _get("/quote", {"symbol": symbol})
    return data


def company_profile2(symbol: str) -> Optional[dict[str, Any]]:
    fh = map_yahoo_to_finnhub(symbol)
    data = _get("/stock/profile2", {"symbol": fh})
    if not data and fh != symbol:
        data = _get("/stock/profile2", {"symbol": symbol})
    return data


def stock_candles(symbol: str, period: str) -> tuple[list[dict[str, Any]], Optional[str]]:
    """
    GET /stock/candle. resolution: 1,5,15,30,60,D,W,M
    Returns (history_rows, error_message)
    """
    now = int(time.time())
    days = {"1d": 2, "5d": 7, "1mo": 35, "3mo": 95, "6mo": 190, "1y": 380, "2y": 760}.get(period, 35)
    start = now - days * 86400
    res_map = {"1d": "15", "5d": "60", "1mo": "D", "3mo": "D", "6mo": "D", "1y": "D", "2y": "D"}
    resolution = res_map.get(period, "D")
    fh = map_yahoo_to_finnhub(symbol)
    data = _get(
        "/stock/candle",
        {"symbol": fh, "resolution": resolution, "from": start, "to": now},
    )
    if not data or data.get("s") != "ok":
        if fh != symbol:
            data = _get(
                "/stock/candle",
                {"symbol": symbol, "resolution": resolution, "from": start, "to": now},
            )
    if not data or data.get("s") != "ok":
        err = (data or {}).get("s") or "no data"
        return [], str(err)

    ts = data.get("t") or []
    o = data.get("o") or []
    h = data.get("h") or []
    low = data.get("l") or []
    c = data.get("c") or []
    v = data.get("v") or []
    rows: list[dict[str, Any]] = []
    for i in range(len(ts)):
        rows.append(
            {
                "timestamp": int(ts[i]) * 1000,
                "open": round(float(o[i]), 4) if i < len(o) else 0,
                "high": round(float(h[i]), 4) if i < len(h) else 0,
                "low": round(float(low[i]), 4) if i < len(low) else 0,
                "close": round(float(c[i]), 4) if i < len(c) else 0,
                "volume": int(v[i]) if i < len(v) else 0,
            }
        )
    return rows, None


def market_news(category: str = "general") -> list[dict[str, Any]]:
    """GET /news — category: general, forex, crypto, merger"""
    data = _get("/news", {"category": category})
    if not isinstance(data, list):
        return []
    out = []
    for item in data[:30]:
        out.append(
            {
                "title": item.get("headline") or item.get("title") or "News",
                "summary": item.get("summary") or "",
                "url": item.get("url") or "#",
                "source": item.get("source") or "Finnhub",
                "time_published": _finnhub_news_time(item.get("datetime")),
            }
        )
    return out


def company_news(symbol: str, days: int = 7) -> list[dict[str, Any]]:
    """GET /company-news"""
    fh = map_yahoo_to_finnhub(symbol)
    to_d = datetime.now(timezone.utc).date()
    from_d = to_d - timedelta(days=days)
    data = _get(
        "/company-news",
        {
            "symbol": fh,
            "from": from_d.isoformat(),
            "to": to_d.isoformat(),
        },
    )
    if not isinstance(data, list) and fh != symbol:
        data = _get(
            "/company-news",
            {
                "symbol": symbol,
                "from": from_d.isoformat(),
                "to": to_d.isoformat(),
            },
        )
    if not isinstance(data, list):
        return []
    out = []
    for item in data[:20]:
        out.append(
            {
                "title": item.get("headline") or "",
                "summary": item.get("summary") or "",
                "url": item.get("url") or "#",
                "datetime": item.get("datetime"),
            }
        )
    return out


def _finnhub_news_time(dt_val: Any) -> str:
    if dt_val is None:
        return ""
    try:
        if isinstance(dt_val, (int, float)):
            ts = int(dt_val)
            if ts > 1_000_000_000_000:
                ts //= 1000
            return datetime.utcfromtimestamp(ts).strftime("%Y%m%dT%H%M%S")
    except Exception:
        pass
    return ""


def option_chain(symbol: str) -> tuple[Optional[str], list[str], list[dict[str, Any]], Optional[str]]:
    """
    GET /stock/option-chain
    Returns (selected_expiry, expiries_list, rows, error)
    """
    # US equities only for standard endpoint; strip exchange prefix
    raw = (symbol or "").strip().upper()
    if ":" in raw:
        raw = raw.split(":")[-1]
    if raw.endswith(".NS") or raw.endswith(".BO"):
        return None, [], [], "Finnhub option chain is US-only; use a US symbol or yfinance fallback"
    clean = raw.replace("^", "")

    data = _get("/stock/option-chain", {"symbol": clean})
    if not data:
        return None, [], [], "No option chain data"

    expiries: list[str] = []
    rows: list[dict[str, Any]] = []
    data_block = data.get("data")
    if not isinstance(data_block, list):
        return None, [], [], "Unexpected option chain response"

    for block in data_block:
        exp = block.get("expirationDate") or block.get("expiration_date")
        if exp:
            expiries.append(str(exp))

    if not expiries:
        return None, [], [], "No expiries in option chain"

    first = data_block[0]
    calls = first.get("call") or first.get("calls") or first.get("CALL") or []
    puts = first.get("put") or first.get("puts") or first.get("PUT") or []

    if isinstance(calls, list) and isinstance(puts, list) and (calls or puts):
        strikes_set: set[float] = set()
        for x in calls:
            if x.get("strike") is not None:
                strikes_set.add(float(x["strike"]))
        for x in puts:
            if x.get("strike") is not None:
                strikes_set.add(float(x["strike"]))
        for strike in sorted(strikes_set):
            ce = next((x for x in calls if x.get("strike") is not None and float(x["strike"]) == strike), {})
            pe = next((x for x in puts if x.get("strike") is not None and float(x["strike"]) == strike), {})
            rows.append({"strike": strike, "call": _norm_side(ce), "put": _norm_side(pe)})

    sel = expiries[0] if expiries else None
    if not rows:
        return sel, expiries, [], "Could not parse strikes (check Finnhub response format)"
    return sel, expiries, rows, None


def _norm_side(side: dict) -> dict[str, Any]:
    if not side:
        return {
            "bid": None,
            "ask": None,
            "lastPrice": None,
            "impliedVolatility": None,
            "openInterest": None,
            "volume": None,
        }
    return {
        "bid": side.get("bid"),
        "ask": side.get("ask"),
        "lastPrice": side.get("lastPrice") or side.get("last_price"),
        "impliedVolatility": side.get("impliedVolatility") or side.get("implied_volatility"),
        "openInterest": side.get("openInterest") or side.get("open_interest"),
        "volume": side.get("volume"),
    }


def momentum_from_candles(symbol: str, period: str) -> dict[str, Any]:
    """Compute (end/start - 1) from Finnhub daily candles."""
    rows, err = stock_candles(symbol, period)
    if err or len(rows) < 2:
        return {"momentum": 0.0, "start_price": None, "end_price": None, "error": err}
    start = rows[0]["close"]
    end = rows[-1]["close"]
    mom = (end / start - 1.0) if start else 0.0
    return {"momentum": mom, "start_price": start, "end_price": end, "error": None}


def aggregate_sentiment_company_news(symbol: str, days: int = 14) -> dict[str, Any]:
    """
    Use Finnhub company news + FinBERT to produce pos/neg/neu counts (for screener).
    Capped at 5 headlines per symbol so multi-symbol scans stay responsive (FinBERT is heavy).
    """
    from .sentiment import analyze_financial_sentiment

    news = company_news(symbol, days=days)
    if not news:
        return {"sentiment": "neutral", "count": 0, "positive": 0, "negative": 0, "neutral": 0}

    pos = neg = neu = 0
    for item in news[:5]:
        text = ((item.get("title") or "") + " " + (item.get("summary") or ""))[:1500]
        if not text.strip():
            continue
        try:
            s, _ = analyze_financial_sentiment(text)
            s = (s or "neutral").lower()
            if s == "positive":
                pos += 1
            elif s == "negative":
                neg += 1
            else:
                neu += 1
        except Exception:
            neu += 1

    count = pos + neg + neu
    if count == 0:
        sentiment = "neutral"
    elif pos > neg and pos > neu:
        sentiment = "positive"
    elif neg > pos and neg > neu:
        sentiment = "negative"
    else:
        sentiment = "neutral"

    return {
        "sentiment": sentiment,
        "count": count,
        "positive": pos,
        "negative": neg,
        "neutral": neu,
    }

"""
News-triggered and rule-based backtesting with trade log transparency.
"""
from __future__ import annotations

import logging
import math
from collections import defaultdict
from datetime import datetime
from typing import Any, Optional

import numpy as np
import pandas as pd

from fetch_news import newsapi_client as na
from fetch_news.sentiment import analyze_financial_sentiment
from quant.indicators import enrich_ohlc
from quant.strategy_engine import resolve_rules, rules_pass

logger = logging.getLogger(__name__)

RELEVANCE_KEYWORDS = [
    "invest",
    "investment",
    "stake",
    "acquisition",
    "merger",
    "fii",
    "dii",
    "shareholding",
    "shareholder",
    "buyback",
    "dividend",
    "results",
    "earnings",
    "guidance",
    "partnership",
    "deal",
    "funding",
    "subsidiary",
    "stake sale",
    "block deal",
    "promoter",
    "qip",
    "ipo",
    "rights issue",
]


def _normalize_ticker(ticker: str) -> str:
    t = (ticker or "").strip().upper()
    # yfinance sometimes echoes warnings with a leading "$" (e.g. "$RELIANCE").
    # Treat "$" as non-semantic decoration for our normalization purposes.
    if t.startswith("$"):
        t = t[1:]
    t = t.replace("$", "")
    return t.replace(".NS", "").replace(".BO", "")


def _strike_step(symbol: str) -> float:
    s = _normalize_ticker(symbol)
    if "NIFTY" in s or "SENSEX" in s or s.startswith("^"):
        return 50.0
    return 10.0


def _atm_strike(price: float, symbol: str) -> float:
    step = _strike_step(symbol)
    p = float(price)
    if not np.isfinite(p) or p <= 0:
        return step
    return round(p / step) * step


def _atm_strike_from_chain(chain_rows: list[dict], price: float) -> float:
    strikes: list[float] = []
    for row in chain_rows:
        for key in ("strike", "Strike", "strikePrice"):
            if row.get(key) is not None:
                try:
                    strikes.append(float(row[key]))
                except (TypeError, ValueError):
                    pass
    if not strikes:
        return _atm_strike(price, "")
    return min(strikes, key=lambda s: abs(s - price))


def _apply_period(
    df: pd.DataFrame,
    days: int,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> pd.DataFrame:
    out = df.sort_index()
    if start_date:
        out = out[out.index >= pd.Timestamp(start_date).normalize()]
    if end_date:
        out = out[out.index <= pd.Timestamp(end_date).normalize()]
    if not start_date and days:
        out = out.tail(max(days + 30, 60))
    return out


def _build_execution(
    *,
    symbol: str,
    mode: str,
    action: str,
    structure: str,
    entry_dt: pd.Timestamp,
    exit_dt: pd.Timestamp,
    entry_price: float,
    exit_price: float,
    o: float,
    h: float,
    l: float,
    c: float,
    sl_pct: Optional[float],
    tp_pct: Optional[float],
    options_proxy: bool,
    chain_snapshot: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Trade ticket-style execution details (daily bar → NSE session times)."""
    entry_time = "09:15 IST"
    exit_time = "15:30 IST" if mode == "equity_intraday" else "15:30 IST (next session)"
    decision = "ENTER_LONG"
    if mode == "options":
        if "VOL" in (action or "") and "SELL" in (action or ""):
            decision = "SELL_VOL_STRUCTURE"
        elif "VOL" in (action or ""):
            decision = "BUY_VOL_STRUCTURE"
        else:
            decision = "OPTIONS_NEUTRAL"
    elif "SELL" in (action or "").upper():
        decision = "ENTER_SHORT"

    chain_rows = (chain_snapshot or {}).get("data") or []
    strike_source = "computed_atm"
    option_expiry = (chain_snapshot or {}).get("expiry")
    if chain_rows and mode == "options":
        strike = _atm_strike_from_chain(chain_rows, c)
        strike_source = "chain_atm"
        options_proxy = False
    else:
        strike = _atm_strike(c, symbol)
    step = _strike_step(symbol)
    legs: list[dict[str, Any]] = []
    if mode == "options":
        if structure == "iron_condor":
            legs = [
                {"leg": "SELL_PUT", "strike": strike - 2 * step},
                {"leg": "BUY_PUT", "strike": strike - 3 * step},
                {"leg": "SELL_CALL", "strike": strike + 2 * step},
                {"leg": "BUY_CALL", "strike": strike + 3 * step},
            ]
        elif structure == "butterfly":
            legs = [
                {"leg": "BUY_PUT", "strike": strike - step},
                {"leg": "SELL_PUT", "strike": strike},
                {"leg": "SELL_CALL", "strike": strike},
                {"leg": "BUY_CALL", "strike": strike + step},
            ]
        else:
            legs = [
                {"leg": "BUY_CALL", "strike": strike},
                {"leg": "BUY_PUT", "strike": strike},
            ]

    sl_price = tp_price = None
    if sl_pct is not None and entry_price:
        sl_price = round(entry_price * (1 - sl_pct / 100), 2)
        if decision == "ENTER_SHORT":
            sl_price = round(entry_price * (1 + sl_pct / 100), 2)
    if tp_pct is not None and entry_price:
        tp_price = round(entry_price * (1 + tp_pct / 100), 2)
        if decision == "ENTER_SHORT":
            tp_price = round(entry_price * (1 - tp_pct / 100), 2)

    return {
        "decision": decision,
        "entry_date": entry_dt.strftime("%Y-%m-%d"),
        "entry_time": entry_time,
        "exit_date": exit_dt.strftime("%Y-%m-%d"),
        "exit_time": exit_time,
        "entry_price": round(entry_price, 2),
        "exit_price": round(exit_price, 2),
        "stop_loss_price": sl_price,
        "take_profit_price": tp_price,
        "stop_loss_pct": sl_pct,
        "take_profit_pct": tp_pct,
        "strike": strike,
        "strike_step": step,
        "strike_source": strike_source if mode == "options" else None,
        "option_expiry": option_expiry if mode == "options" else None,
        "option_structure": structure if mode == "options" else None,
        "option_legs": legs if legs else None,
        "chain_source": (chain_snapshot or {}).get("source") if mode == "options" else None,
        "session": (
            "NSE F&O (live chain)"
            if mode == "options" and strike_source == "chain_atm"
            else "NSE F&O (proxy on underlying)"
            if options_proxy and mode == "options"
            else "NSE F&O"
            if mode == "options"
            else "NSE cash"
        ),
        "bar_ohlc": {"open": o, "high": h, "low": l, "close": c},
    }


def _fetch_ohlc_yfinance(ticker: str, days: int) -> Optional[pd.DataFrame]:
    try:
        import yfinance as yf

        period = "1y" if days >= 252 else f"{max(days, 60)}d"
        # Sanitize weird prefixes so we don't end up calling yf.Ticker("$RELIANCE")
        raw = (ticker or "").strip().upper()
        if raw.startswith("$"):
            raw = raw[1:]
        raw = raw.replace("$", "")

        symbols = [raw]
        base = _normalize_ticker(raw)
        index_map = {
            "NIFTY": "^NSEI",
            "NIFTY50": "^NSEI",
            "BANKNIFTY": "^NSEBANK",
            "SENSEX": "^BSESN",
        }
        if base in index_map:
            symbols = [index_map[base], base]
        elif base and "." not in raw and not raw.startswith("^"):
            symbols = [f"{base}.NS", f"{base}.BO", base, raw]
        for sym in symbols:
            hist = yf.Ticker(sym).history(period=period)
            if hist is None or hist.empty or len(hist) < 20:
                continue
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
            df.index = pd.DatetimeIndex(df.index).normalize()
            return df.sort_index()
        return None
    except Exception as e:
        logger.warning("OHLC fetch failed: %s", e)
        return None


def _ohlc_from_history_payload(history: list[dict]) -> Optional[pd.DataFrame]:
    rows = []
    for row in history:
        ts = row.get("date") or row.get("timestamp")
        if not ts:
            continue
        try:
            dt = pd.Timestamp(ts).normalize()
            rows.append(
                {
                    "date": dt,
                    "open": float(row.get("open") or row.get("close") or 0),
                    "high": float(row.get("high") or row.get("close") or 0),
                    "low": float(row.get("low") or row.get("close") or 0),
                    "close": float(row.get("close") or 0),
                    "volume": float(row.get("volume") or 0),
                }
            )
        except (TypeError, ValueError):
            continue
    if len(rows) < 20:
        return None
    df = pd.DataFrame(rows).set_index("date").sort_index()
    return df


# Yahoo / NSE symbol candidates for options chain lookup
_OPTIONS_SYMBOL_MAP: dict[str, list[str]] = {
    "NIFTY": ["^NSEI", "NIFTY.NS"],
    "NIFTY50": ["^NSEI"],
    "NIFTY 50": ["^NSEI"],
    "BANKNIFTY": ["^NSEBANK", "BANKNIFTY.NS"],
    "SENSEX": ["^BSESN"],
    "RELIANCE": ["RELIANCE.NS", "RELIANCE.BO", "RELIANCE"],
    "TCS": ["TCS.NS", "TCS"],
    "INFY": ["INFY.NS", "INFY"],
    "HDFCBANK": ["HDFCBANK.NS", "HDFCBANK"],
    "ICICIBANK": ["ICICIBANK.NS", "ICICIBANK"],
}

_INDEX_UNDERLYINGS = {"NIFTY", "NIFTY50", "NIFTY 50", "BANKNIFTY", "SENSEX", "^NSEI", "^BSESN", "^NSEBANK"}


def _options_yfinance_candidates(symbol: str) -> list[str]:
    sym = _normalize_ticker(symbol)
    key = sym.replace(" ", "")
    if key in _OPTIONS_SYMBOL_MAP:
        return _OPTIONS_SYMBOL_MAP[key]
    if sym.startswith("^"):
        return [sym]
    return [f"{sym}.NS", f"{sym}.BO", sym]


def check_options_chain_available(symbol: str, expiry: str | None = None) -> dict[str, Any]:
    """Yahoo Finance options chain availability."""
    sym = _normalize_ticker(symbol)
    tried: list[str] = []
    try:
        import yfinance as yf

        for yf_sym in _options_yfinance_candidates(symbol):
            tried.append(yf_sym)
            expiries = list(yf.Ticker(yf_sym).options or [])
            if expiries:
                return {
                    "available": True,
                    "proxy": False,
                    "source": "yfinance",
                    "expiries_count": len(expiries),
                    "nearest_expiry": expiries[0],
                    "symbol_checked": yf_sym,
                    "symbols_tried": tried,
                }

        is_index = sym in _INDEX_UNDERLYINGS or sym.startswith("^") or "NIFTY" in sym or "SENSEX" in sym
        if is_index:
            return {
                "available": True,
                "proxy": True,
                "source": "yfinance",
                "expiries_count": 0,
                "nearest_expiry": None,
                "symbol_checked": tried[0] if tried else sym,
                "symbols_tried": tried,
                "note": (
                    "Index options not on Yahoo Finance. "
                    "Using underlying OHLC with options strategy proxy."
                ),
            }

        return {
            "available": True,
            "proxy": True,
            "source": "yfinance",
            "expiries_count": 0,
            "nearest_expiry": None,
            "symbol_checked": tried[0] if tried else f"{sym}.NS",
            "symbols_tried": tried,
            "note": (
                "Live option chain not found via Yahoo Finance. "
                "Using underlying OHLC with options strategy proxy."
            ),
        }
    except Exception as e:
        return {"available": False, "proxy": False, "error": str(e), "symbol_checked": sym, "symbols_tried": tried}


def _article_date(item: dict) -> Optional[pd.Timestamp]:
    tp = item.get("time_published") or item.get("publishedAt") or ""
    if not tp:
        return None
    try:
        if "T" in tp:
            return pd.Timestamp(datetime.fromisoformat(tp.replace("Z", "+00:00"))).normalize()
        if len(tp) >= 8 and tp[:8].isdigit():
            return pd.Timestamp(datetime.strptime(tp[:8], "%Y%m%d")).normalize()
    except ValueError:
        pass
    try:
        return pd.Timestamp(tp).normalize()
    except Exception:
        return None


def _is_relevant_news(item: dict, symbol: str) -> bool:
    # Indices: NewsAPI queries are broader and headlines may not contain the exact symbol string.
    sym_norm = _normalize_ticker(symbol)
    sym = sym_norm.lower()
    text = f"{item.get('title', '')} {item.get('summary', '')}".lower()
    keyword_hit = any(k in text for k in RELEVANCE_KEYWORDS)

    is_index = sym_norm in _INDEX_UNDERLYINGS or "NIFTY" in sym_norm or "SENSEX" in sym_norm
    if is_index:
        # Allow index-related market headlines even when they don't repeat the symbol.
        mentions_index = any(k in text for k in ("nifty", "sensex", "banknifty", "nse", "bse", "f&o", "derivative", "options", "futures"))
        return bool(keyword_hit or mentions_index) and len(text) > 30

    if sym and sym in text:
        return keyword_hit or len(text) > 40
    return False


def _sentiment_for_text(text: str) -> tuple[str, float]:
    try:
        label, probs = analyze_financial_sentiment(text[:2000])
        lab = (label or "neutral").lower()
        score = float(probs[2] - probs[0]) if probs is not None and len(probs) >= 3 else 0.0
        return lab, score
    except Exception:
        return "neutral", 0.0


def _fetch_news_by_day(symbol: str, days: int) -> dict[pd.Timestamp, list[dict]]:
    if not na.is_configured():
        return {}
    # NewsAPI free tier may only allow recent history — try without old from_date first.
    to_dt = pd.Timestamp.utcnow().date().isoformat()
    from_dt = (pd.Timestamp.utcnow() - pd.Timedelta(days=min(days + 14, 30))).date().isoformat()
    items = na.fetch_symbol_news(symbol, limit=100, from_param=from_dt, to=to_dt)
    if not items:
        items = na.fetch_symbol_news(symbol, limit=100)
    by_day: dict[pd.Timestamp, list[dict]] = defaultdict(list)
    for item in items:
        if not _is_relevant_news(item, symbol):
            continue
        dt = _article_date(item)
        if dt is None:
            continue
        text = f"{item.get('title', '')} {item.get('summary', '')}"
        lab, sc = _sentiment_for_text(text)
        by_day[dt].append(
            {
                "title": item.get("title") or "",
                "summary": (item.get("summary") or "")[:500],
                "url": item.get("url") or "#",
                "source": item.get("source") or "NewsAPI",
                "sentiment": lab,
                "sentiment_score": round(sc, 4),
                "relevance": "company_news",
            }
        )
    return dict(by_day)


def _options_pnl_proxy(structure: str, day_return: float) -> float:
    """Educational proxy P&L % for options structures from underlying daily return."""
    r = abs(day_return)
    if structure == "iron_condor":
        return 0.8 if r < 0.012 else -1.5 * r * 100
    if structure == "butterfly":
        return 1.2 if r < 0.008 else -0.8 * r * 100
    if structure == "long_straddle":
        return (r * 100 * 1.8) - 0.6 if r > 0.005 else -0.4
    return day_return * 100


def run_event_backtest(
    ticker: str,
    mode: str = "equity_delivery",
    template_id: Optional[str] = None,
    strategy_prompt: Optional[str] = None,
    only_news_events: bool = True,
    days: int = 126,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    period_label: Optional[str] = None,
    price_history: Optional[list[dict]] = None,
    price_source: Optional[str] = None,
    custom_only: bool = False,
    compiled_rules: Optional[list[dict]] = None,
    compiled_meta: Optional[dict] = None,
    use_groq_compile: bool = False,
) -> dict[str, Any]:
    """
    mode: equity_intraday | equity_delivery | options
    """
    mode = (mode or "equity_delivery").lower()
    prompt = (strategy_prompt or "").strip()
    compile_info: dict[str, Any] = {}

    if use_groq_compile and prompt:
        from quant.strategy_llm import compile_strategy

        compile_info = compile_strategy(prompt, mode_hint=mode)
        if compile_info.get("rules"):
            compiled_rules = compile_info["rules"]
            compiled_meta = {
                "id": template_id or "custom",
                "name": "AI-compiled strategy",
                "description": compile_info.get("normalized_prompt") or prompt,
                "action": compile_info.get("action"),
                "options_structure": compile_info.get("options_structure"),
                "risk_reward": compile_info.get("risk_reward"),
            }
        elif compile_info.get("source") == "fallback":
            compiled_rules = None

    tpl_meta, rules = resolve_rules(
        template_id,
        strategy_prompt,
        custom_only=custom_only,
        compiled_rules=compiled_rules,
        compiled_meta=compiled_meta,
    )
    if compile_info:
        tpl_meta["compile"] = compile_info

    options_info = check_options_chain_available(ticker)
    chain_snapshot = options_info.get("chain") if options_info.get("source") == "yfinance" else None

    if mode == "options" and not options_info.get("available"):
        return {
            "error": "Could not run options backtest for this symbol.",
            "ticker": ticker,
            "options_chain": options_info,
            "strategy": tpl_meta,
        }

    df = _ohlc_from_history_payload(price_history or [])
    src = price_source or "kite"
    if df is None or len(df) < 20:
        df = _fetch_ohlc_yfinance(ticker, days)
        src = "yfinance"
    if df is None or len(df) < 20:
        return {
            "error": "Could not load OHLC history for backtest.",
            "ticker": ticker,
            "strategy": tpl_meta,
        }

    df = _apply_period(df, days, start_date, end_date)
    if len(df) < 20:
        return {
            "error": "Not enough price data in selected period.",
            "ticker": ticker,
            "strategy": tpl_meta,
            "period": {"start_date": start_date, "end_date": end_date, "days": days},
        }
    df = enrich_ohlc(df)
    period_info = {
        "start": df.index[0].strftime("%Y-%m-%d"),
        "end": df.index[-1].strftime("%Y-%m-%d"),
        "days_requested": days,
        "start_date": start_date,
        "end_date": end_date,
        "bars_in_range": len(df),
        "label": period_label or (f"{start_date} → {end_date}" if start_date else f"Last ~{days} calendar days"),
    }
    news_by_day = _fetch_news_by_day(ticker, max(days, (df.index[-1] - df.index[0]).days + 30))
    all_news: list[dict] = []
    for d, articles in sorted(news_by_day.items()):
        for a in articles:
            all_news.append({**a, "date": d.strftime("%Y-%m-%d")})

    trades: list[dict[str, Any]] = []
    equity = 1.0
    wins = 0
    structure = tpl_meta.get("options_structure") or compile_info.get("options_structure") or "long_straddle"
    risk_rr = tpl_meta.get("risk_reward") or compile_info.get("risk_reward")
    sl_pct = float(risk_rr.get("stop_loss_pct", 1.0)) if risk_rr else None
    tp_pct = float(risk_rr.get("take_profit_pct", 2.0)) if risk_rr else None

    idx_list = list(df.index)
    for i, dt in enumerate(idx_list):
        if i < 20:
            continue
        row = df.loc[dt]
        has_news = dt in news_by_day
        if only_news_events and not has_news:
            continue

        day_articles = news_by_day.get(dt, [])
        avg_sent = (
            float(np.mean([a["sentiment_score"] for a in day_articles]))
            if day_articles
            else 0.0
        )
        row_dict = {
            "rsi": float(row["rsi"]) if pd.notna(row["rsi"]) else None,
            "mfi": float(row["mfi"]) if pd.notna(row["mfi"]) else None,
            "macd_hist": float(row["macd_hist"]) if pd.notna(row["macd_hist"]) else None,
            "bb_pct": float(row["bb_pct"]) if "bb_pct" in row and pd.notna(row["bb_pct"]) else None,
            "vwap_dist": float(row["vwap_dist"]) if "vwap_dist" in row and pd.notna(row["vwap_dist"]) else None,
            "zigzag_trend": float(row["zigzag_trend"]) if "zigzag_trend" in row and pd.notna(row["zigzag_trend"]) else None,
        }
        if not rules_pass(rules, row_dict, avg_sent, has_news):
            continue

        o, h, l, c = float(row["open"]), float(row["high"]), float(row["low"]), float(row["close"])
        if not all(np.isfinite(x) for x in (o, h, l, c)) or c <= 0:
            continue
        action = tpl_meta.get("action", "BUY")
        entry_price = o
        exit_dt = dt
        exit_price = c

        if mode == "equity_intraday":
            pnl_pct = ((c - o) / o * 100) if o else 0.0
            hold = "same_day"
            entry_price, exit_price = o, c
            exit_dt = dt
        elif mode == "options":
            day_ret = (c - o) / o if o else 0.0
            pnl_pct = _options_pnl_proxy(structure, day_ret)
            action = tpl_meta.get("action", "OPTIONS")
            hold = structure
            entry_price, exit_price = c, c  # mark at close for proxy
            exit_dt = dt
        else:
            if i + 1 < len(idx_list):
                exit_dt = idx_list[i + 1]
                next_close = float(df.loc[exit_dt]["close"])
                raw_pnl = ((next_close - c) / c * 100) if c else 0.0
                exit_price = next_close
            else:
                raw_pnl = ((c - o) / o * 100) if o else 0.0
                exit_price = c
            if sl_pct is not None and tp_pct is not None:
                if raw_pnl <= -sl_pct:
                    pnl_pct = -sl_pct
                elif raw_pnl >= tp_pct:
                    pnl_pct = tp_pct
                else:
                    pnl_pct = raw_pnl
            else:
                pnl_pct = raw_pnl
            entry_price = c
            hold = "next_day"

        execution = _build_execution(
            symbol=ticker,
            mode=mode,
            action=str(action),
            structure=structure,
            entry_dt=dt,
            exit_dt=exit_dt,
            entry_price=entry_price,
            exit_price=exit_price,
            o=o,
            h=h,
            l=l,
            c=c,
            sl_pct=sl_pct,
            tp_pct=tp_pct,
            options_proxy=bool(options_info.get("proxy")),
            chain_snapshot=chain_snapshot if mode == "options" else None,
        )

        if pnl_pct > 0:
            wins += 1
        step = pnl_pct / 100.0
        if step == step:  # finite
            equity *= 1 + step

        reason_parts = [
            f"Strategy: {tpl_meta.get('name', 'custom')}",
            f"Mode: {mode}",
        ]
        if has_news:
            reason_parts.append(f"{len(day_articles)} relevant headline(s) on this date")
        if row_dict.get("rsi") is not None:
            reason_parts.append(f"RSI={row_dict['rsi']:.1f}")
        if row_dict.get("mfi") is not None:
            reason_parts.append(f"MFI={row_dict['mfi']:.1f}")
        if row_dict.get("bb_pct") is not None:
            reason_parts.append(f"BB%={row_dict['bb_pct']:.1f}")
        if row_dict.get("vwap_dist") is not None:
            reason_parts.append(f"VWAP dist={row_dict['vwap_dist']:.2f}%")
        if row_dict.get("zigzag_trend") is not None:
            reason_parts.append(f"Zigzag={int(row_dict['zigzag_trend'])}")

        trades.append(
            {
                "date": dt.strftime("%Y-%m-%d"),
                "action": action,
                "hold_type": hold,
                "pnl_pct": round(pnl_pct, 3),
                "execution": execution,
                "news": day_articles,
                "metrics": {
                    "open": round(o, 2),
                    "high": round(h, 2),
                    "low": round(l, 2),
                    "close": round(c, 2),
                    "volume": int(row.get("volume") or 0),
                    "day_return_pct": round(((c - o) / o * 100) if o else 0, 3),
                    "rsi": round(row_dict["rsi"], 2) if row_dict["rsi"] is not None else None,
                    "mfi": round(row_dict["mfi"], 2) if row_dict["mfi"] is not None else None,
                    "macd_hist": round(row_dict["macd_hist"], 4) if row_dict["macd_hist"] is not None else None,
                    "bb_pct": row_dict["bb_pct"],
                    "vwap_dist": row_dict["vwap_dist"],
                    "zigzag_trend": row_dict["zigzag_trend"],
                    "avg_news_sentiment": round(avg_sent, 4),
                },
                "reason": " · ".join(reason_parts),
                "rules_matched": rules,
            }
        )

    n = len(trades)
    win_rate = (wins / n * 100) if n else 0.0
    total_return = (equity - 1.0) * 100
    if not math.isfinite(total_return):
        total_return = 0.0
    if not math.isfinite(win_rate):
        win_rate = 0.0

    if not rules and not trades:
        return {
            "error": (
                "No rules matched — write custom rules or click “Fix with AI”, "
                "or pick a template. Try unchecking “news only” for more signals."
            ),
            "ticker": ticker,
            "strategy": tpl_meta,
            "options_chain": options_info,
        }

    return {
        "ticker": ticker,
        "mode": mode,
        "period": period_info,
        "only_news_events": only_news_events,
        "price_source": src,
        "options_chain": options_info,
        "strategy": {
            **{k: tpl_meta.get(k) for k in ("id", "name", "description", "options_structure")},
            "parsed_rules": rules,
            "custom_prompt": strategy_prompt,
        },
        "summary": {
            "total_trades": n,
            "winning_trades": wins,
            "win_rate_pct": round(win_rate, 2),
            "total_return_pct": round(total_return, 2),
            "news_articles_considered": len(all_news),
            "trading_days_in_sample": len(df),
        },
        "trades": trades,
        "news_pool": all_news[:50],
        "explanation": {
            "headline": (
                f"{_normalize_ticker(ticker)}: {n} trades triggered "
                f"({'news-only days' if only_news_events else 'all matching rule days'})."
            ),
            "methodology": (
                "Fetches headlines via NewsAPI, flags relevant company news (investment, stake, earnings, etc.), "
                "computes RSI/MFI/MACD on daily OHLC, and applies your template or natural-language rules. "
                "Each trade row shows the exact news and metrics used that day. Options modes use simplified "
                "educational proxies — not exchange-accurate option pricing."
            ),
            "disclaimer": "Educational simulation only. Not financial advice.",
        },
    }
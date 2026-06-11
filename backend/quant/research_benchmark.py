"""
Research-oriented benchmark harness for multi-market strategy comparison.

Includes transaction costs, slippage, and Indian symbol handling.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from quant.event_backtest import run_event_backtest
from quant.indicators import enrich_ohlc


INDIA_DEFAULT_UNIVERSE = [
    "^NSEI",
    "^BSESN",
    "^NSEBANK",
    "RELIANCE.NS",
    "TCS.NS",
    "INFY.NS",
    "HDFCBANK.NS",
    "ICICIBANK.NS",
]

GLOBAL_DEFAULT_UNIVERSE = [
    "AAPL",
    "MSFT",
    "NVDA",
]


def _normalize_symbol(symbol: str) -> str:
    s = (symbol or "").strip().upper()
    if s in {"NIFTY", "NIFTY50"}:
        return "^NSEI"
    if s in {"SENSEX"}:
        return "^BSESN"
    if s in {"BANKNIFTY", "NIFTYBANK"}:
        return "^NSEBANK"
    return s


def _candidate_symbols(symbol: str) -> list[str]:
    s = _normalize_symbol(symbol)
    if s.startswith("^") or "." in s:
        return [s]
    return [f"{s}.NS", f"{s}.BO", s]


def _to_ohlc(rows: list[dict[str, Any]]) -> pd.DataFrame | None:
    cleaned: list[dict[str, Any]] = []
    for row in rows or []:
        ts = row.get("date") or row.get("timestamp")
        close = row.get("close")
        if ts is None or close is None:
            continue
        try:
            dt = pd.Timestamp(ts).normalize()
            c = float(close)
            o = float(row.get("open") or c)
            h = float(row.get("high") or max(o, c))
            l = float(row.get("low") or min(o, c))
            v = float(row.get("volume") or 0)
        except (TypeError, ValueError):
            continue
        cleaned.append({"date": dt, "open": o, "high": h, "low": l, "close": c, "volume": v})
    if len(cleaned) < 60:
        return None
    return pd.DataFrame(cleaned).set_index("date").sort_index()


def _fetch_ohlc(symbol: str, days: int) -> tuple[pd.DataFrame | None, str]:
    try:
        import yfinance as yf

        period = "2y" if days > 252 else "1y"
        for cand in _candidate_symbols(symbol):
            hist = yf.Ticker(cand).history(period=period)
            if hist is None or hist.empty or len(hist) < 60:
                continue
            frame = pd.DataFrame(
                {
                    "open": hist["Open"],
                    "high": hist["High"],
                    "low": hist["Low"],
                    "close": hist["Close"],
                    "volume": hist.get("Volume", 0),
                }
            )
            if getattr(frame.index, "tz", None) is not None:
                frame.index = frame.index.tz_localize(None)
            frame.index = pd.DatetimeIndex(frame.index).normalize()
            return frame.sort_index().tail(days), "yfinance"
    except Exception:
        pass

    return None, "none"


def _max_drawdown(equity_curve: pd.Series) -> float:
    if equity_curve is None or equity_curve.empty:
        return 0.0
    running_peak = equity_curve.cummax()
    dd = (equity_curve - running_peak) / running_peak.replace(0, np.nan)
    return float(abs(dd.min()) * 100.0) if len(dd) else 0.0


def _metrics(returns: pd.Series) -> dict[str, float]:
    if returns is None or returns.empty:
        return {"CR_pct": 0.0, "AR_pct": 0.0, "SR": 0.0, "MDD_pct": 0.0}
    equity = (1.0 + returns.fillna(0)).cumprod()
    cr = float((equity.iloc[-1] - 1.0) * 100.0)
    years = max(1 / 252, len(returns) / 252.0)
    ar = float(((equity.iloc[-1]) ** (1 / years) - 1.0) * 100.0)
    vol = returns.std()
    sr = float((returns.mean() / vol) * np.sqrt(252)) if vol and np.isfinite(vol) and vol > 0 else 0.0
    mdd = _max_drawdown(equity)
    return {"CR_pct": round(cr, 2), "AR_pct": round(ar, 2), "SR": round(sr, 3), "MDD_pct": round(mdd, 2)}


def _signal_sma(df: pd.DataFrame) -> pd.Series:
    sma_fast = df["close"].rolling(20, min_periods=20).mean()
    sma_slow = df["close"].rolling(50, min_periods=50).mean()
    sig = pd.Series(0, index=df.index, dtype=float)
    sig[sma_fast > sma_slow] = 1
    sig[sma_fast < sma_slow] = -1
    return sig


def _signal_macd(df: pd.DataFrame) -> pd.Series:
    sig = pd.Series(0, index=df.index, dtype=float)
    sig[df["macd_hist"] > 0] = 1
    sig[df["macd_hist"] < 0] = -1
    return sig


def _signal_rsi_reversion(df: pd.DataFrame) -> pd.Series:
    sig = pd.Series(0, index=df.index, dtype=float)
    sig[df["rsi"] < 35] = 1
    sig[df["rsi"] > 70] = -1
    return sig


def _signal_zmr(df: pd.DataFrame) -> pd.Series:
    r = df["close"].pct_change()
    z = (r - r.rolling(20, min_periods=20).mean()) / r.rolling(20, min_periods=20).std().replace(0, np.nan)
    sig = pd.Series(0, index=df.index, dtype=float)
    sig[z < -1.5] = 1
    sig[z > 1.5] = -1
    return sig.fillna(0)


def _signal_agentic(symbol: str, index: pd.DatetimeIndex, days: int) -> pd.Series:
    """
    Convert event-backtest trades into daily direction signal.
    """
    sig = pd.Series(0, index=index, dtype=float)
    try:
        out = run_event_backtest(
            ticker=symbol,
            mode="equity_delivery",
            template_id="sentiment_news_combo",
            days=days,
            only_news_events=True,
            use_groq_compile=False,
        )
    except Exception:
        return sig
    trades = out.get("trades") or []
    if not isinstance(trades, list):
        return sig
    for tr in trades:
        dt = tr.get("date")
        if not dt:
            continue
        try:
            t = pd.Timestamp(dt).normalize()
        except Exception:
            continue
        action = str(tr.get("action") or "BUY").upper()
        direction = -1 if "SELL" in action else 1
        if t in sig.index:
            sig.loc[t] = direction
            next_idx = sig.index[sig.index > t]
            if len(next_idx):
                sig.loc[next_idx[0]] = direction
    return sig


@dataclass
class BenchConfig:
    days: int = 252
    transaction_cost_bps: float = 8.0
    slippage_bps: float = 4.0
    include_agentic: bool = True


def _run_single_strategy(
    prices: pd.DataFrame,
    signal: pd.Series,
    *,
    transaction_cost_bps: float,
    slippage_bps: float,
) -> dict[str, Any]:
    ret = prices["close"].pct_change().fillna(0.0)
    position = signal.reindex(prices.index).ffill().fillna(0.0)
    shifted_position = position.shift(1).fillna(0.0)
    gross = shifted_position * ret

    turnover = position.diff().abs().fillna(0.0)
    cost = turnover * ((transaction_cost_bps + slippage_bps) / 10000.0)
    net = gross - cost
    trades = int((turnover > 0).sum())

    out = _metrics(net)
    out["trades"] = trades
    out["avg_turnover"] = round(float(turnover.mean()), 4)
    return out


def run_research_benchmark(
    *,
    symbols: list[str] | None = None,
    include_global: bool = False,
    days: int = 252,
    transaction_cost_bps: float = 8.0,
    slippage_bps: float = 4.0,
    include_agentic: bool = True,
) -> dict[str, Any]:
    universe = list(symbols or INDIA_DEFAULT_UNIVERSE)
    if include_global:
        universe.extend(GLOBAL_DEFAULT_UNIVERSE)
    universe = list(dict.fromkeys([_normalize_symbol(x) for x in universe if x]))

    cfg = BenchConfig(
        days=max(90, min(int(days), 756)),
        transaction_cost_bps=max(0.0, float(transaction_cost_bps)),
        slippage_bps=max(0.0, float(slippage_bps)),
        include_agentic=bool(include_agentic),
    )

    strategy_order = ["buy_and_hold", "sma_20_50", "macd_hist", "rsi_reversion", "zmr"]
    if cfg.include_agentic:
        strategy_order.append("agentic_news_debate")

    rows: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []
    for sym in universe:
        frame, source = _fetch_ohlc(sym, cfg.days)
        if frame is None or len(frame) < 60:
            skipped.append({"symbol": sym, "reason": "insufficient_history"})
            continue
        frame = enrich_ohlc(frame)

        signals = {
            "buy_and_hold": pd.Series(1.0, index=frame.index),
            "sma_20_50": _signal_sma(frame),
            "macd_hist": _signal_macd(frame),
            "rsi_reversion": _signal_rsi_reversion(frame),
            "zmr": _signal_zmr(frame),
        }
        if cfg.include_agentic:
            signals["agentic_news_debate"] = _signal_agentic(sym, frame.index, min(cfg.days, len(frame)))

        for name in strategy_order:
            stats = _run_single_strategy(
                frame,
                signals[name],
                transaction_cost_bps=cfg.transaction_cost_bps,
                slippage_bps=cfg.slippage_bps,
            )
            rows.append(
                {
                    "symbol": sym,
                    "market": "india" if (".NS" in sym or sym.startswith("^NSE") or sym == "^BSESN") else "global",
                    "source": source,
                    "strategy": name,
                    **stats,
                }
            )

    if not rows:
        return {
            "error": "No benchmark rows generated.",
            "universe": universe,
            "skipped": skipped,
        }

    df = pd.DataFrame(rows)
    grouped = (
        df.groupby("strategy")[["CR_pct", "AR_pct", "SR", "MDD_pct", "trades"]]
        .mean()
        .round(3)
        .reset_index()
        .sort_values("SR", ascending=False)
    )

    best_strategy = grouped.iloc[0]["strategy"] if len(grouped) else None
    return {
        "config": {
            "days": cfg.days,
            "transaction_cost_bps": cfg.transaction_cost_bps,
            "slippage_bps": cfg.slippage_bps,
            "include_agentic": cfg.include_agentic,
            "universe_size": len(universe),
        },
        "aggregate": grouped.to_dict(orient="records"),
        "by_symbol": df.sort_values(["symbol", "SR"], ascending=[True, False]).to_dict(orient="records"),
        "best_strategy_by_avg_sharpe": best_strategy,
        "skipped": skipped,
    }


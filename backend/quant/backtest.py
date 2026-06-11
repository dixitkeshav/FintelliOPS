"""
Simple backtester: compare price-only vs price + sentiment strategy.
Uses pandas and optional yfinance for price data; NewsAPI is primary for headline sentiment.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np
import pandas as pd
from fetch_news import newsapi_client as na
from fetch_news.sentiment import analyze_financial_sentiment

logger = logging.getLogger(__name__)


def _normalize_ticker_for_yfinance(ticker: str) -> str:
    """Normalize ticker casing/spacing without forcing an exchange suffix."""
    t = (ticker or "").strip().upper()
    return t


def _candidate_yfinance_symbols(ticker: str) -> list[str]:
    """Try base symbol first, then NSE suffix for Indian equities."""
    t = _normalize_ticker_for_yfinance(ticker)
    if not t:
        return []
    if t.startswith("^") or "." in t:
        return [t]
    return [t, f"{t}.NS"]


def _fetch_prices(ticker: str, days: int = 252) -> Optional[pd.Series]:
    """Fetch daily close prices via yfinance."""
    try:
        import yfinance as yf

        period = "1y" if days >= 252 else f"{max(days, 30)}d"
        for yf_symbol in _candidate_yfinance_symbols(ticker):
            hist = yf.Ticker(yf_symbol).history(period=period)
            if hist is None or hist.empty:
                continue
            closes = hist["Close"].dropna()
            if len(closes) < 10:
                continue
            if getattr(closes.index, "tz", None) is not None:
                closes.index = closes.index.tz_localize(None)
            return closes
        return None
    except Exception as e:
        logger.warning("yfinance fetch failed for %s: %s", ticker, e)
        return None


def _fetch_newsapi_sentiment_series(ticker: str, days: int = 252) -> Optional[pd.Series]:
    """
    Aggregate NewsAPI headline sentiment scores by calendar day.
    Returns a Series indexed by date (timezone-naive) with mean sentiment score per day.
    """
    if not na.is_configured():
        return None
    try:
        from_dt = pd.Timestamp.utcnow().normalize() - pd.Timedelta(days=max(30, days))
        items = na.fetch_symbol_news(
            ticker,
            limit=100,
            from_param=from_dt.date().isoformat(),
            to=pd.Timestamp.utcnow().date().isoformat(),
        )
        if not items:
            return None
    except Exception as e:
        logger.warning("NewsAPI sentiment fetch failed: %s", e)
        return None

    from collections import defaultdict
    from datetime import datetime

    by_day: dict[Any, list[float]] = defaultdict(list)
    for item in items:
        text = ((item.get("title") or "") + " " + (item.get("summary") or ""))[:1500]
        if not text.strip():
            continue
        try:
            sent, probs = analyze_financial_sentiment(text)
            label = (sent or "neutral").lower()
            if label == "positive":
                sc = float(probs[2] - probs[0])
            elif label == "negative":
                sc = float(probs[2] - probs[0])
            else:
                sc = float(probs[2] - probs[0])
        except Exception:
            continue

        tp = item.get("time_published") or ""
        try:
            dt = datetime.fromisoformat(tp.replace("Z", "+00:00")).date()
        except ValueError:
            continue
        by_day[pd.Timestamp(dt)].append(sc)

    if not by_day:
        return None

    idx = sorted(by_day.keys())
    vals = [float(np.mean(by_day[k])) for k in idx]
    return pd.Series(vals, index=pd.DatetimeIndex(idx)).sort_index()


def _simulate_returns(prices: pd.Series, signals: pd.Series) -> pd.Series:
    """Strategy returns: when signal > 0 long, when signal < 0 short (as -1 * return)."""
    ret = prices.pct_change().dropna()
    common = ret.index.intersection(signals.index)
    if common.empty:
        return pd.Series(dtype=float)
    ret = ret.reindex(common).ffill().fillna(0)
    sig = signals.reindex(common).ffill().fillna(0)
    strategy_ret = ret * np.sign(sig)
    return strategy_ret


def sharpe_ratio(returns: pd.Series, risk_free: float = 0.0, annualize: bool = True) -> float:
    """Annualized Sharpe (assuming daily returns if annualize=True)."""
    if returns is None or len(returns) < 2:
        return 0.0
    excess = returns - risk_free / 252 if annualize else returns
    std = excess.std()
    if std == 0:
        return 0.0
    ann = np.sqrt(252) if annualize else 1
    return float(excess.mean() / std * ann)


def information_coefficient(signal: pd.Series, forward_returns: pd.Series) -> float:
    """IC = correlation(signal, forward return)."""
    if signal is None or forward_returns is None or min(len(signal), len(forward_returns)) < 5:
        return 0.0
    common = signal.index.intersection(forward_returns.index)
    s = signal.reindex(common).dropna()
    r = forward_returns.reindex(common).dropna()
    common = s.index.intersection(r.index)
    if len(common) < 5:
        return 0.0
    return float(s.loc[common].corr(r.loc[common]))


def _pct_return(prices: pd.Series, lookback: int) -> Optional[float]:
    if prices is None or len(prices) < lookback + 1:
        return None
    p0 = float(prices.iloc[-lookback - 1])
    p1 = float(prices.iloc[-1])
    if p0 == 0:
        return None
    return (p1 / p0) - 1.0


def _build_explanation(
    ticker: str,
    prices: pd.Series,
    price_returns: pd.Series,
    price_only_sharpe: float,
    strategy_sharpe: Optional[float],
    ic: Optional[float],
    total_return_price: Optional[float],
    total_return_strategy: Optional[float],
    sentiment_source: str,
) -> dict[str, Any]:
    vol = float(price_returns.std() * np.sqrt(252)) if len(price_returns) > 1 else 0.0
    r_21 = _pct_return(prices, 21)
    r_63 = _pct_return(prices, 63)

    if r_21 is not None:
        if r_21 > 0.03:
            trend = "The stock has risen meaningfully over roughly the last month."
        elif r_21 < -0.03:
            trend = "The stock has fallen meaningfully over roughly the last month."
        else:
            trend = "Recent price action over the last month has been relatively flat."
    else:
        trend = "There was not enough history to compute a clean one-month trend."

    if r_63 is not None:
        if r_63 > 0.05:
            quarter = f"Over about three months, cumulative returns have been positive ({r_63*100:.1f}%)."
        elif r_63 < -0.05:
            quarter = f"Over about three months, cumulative returns have been negative ({r_63*100:.1f}%)."
        else:
            quarter = f"Over about three months, price drift has been modest ({r_63*100:.1f}%)."
    else:
        quarter = "Quarterly trend could not be computed from available bars."

    why: list[str] = []
    if r_21 is not None and r_21 > 0:
        why.append(
            "Upward pressure in the sample window is consistent with positive recent returns (momentum)."
        )
    if r_21 is not None and r_21 < 0:
        why.append(
            "Downward pressure in the sample window is consistent with negative recent returns (momentum)."
        )
    if vol > 0.25:
        why.append(
            f"Annualized volatility of daily returns is around {vol*100:.0f}% — large swings are common, so short-term direction is noisy."
        )
    elif vol < 0.15 and vol > 0:
        why.append(
            f"Volatility has been relatively moderate compared with many single names (≈{vol*100:.0f}% annualized)."
        )

    if sentiment_source in ("newsapi", "user") and ic is not None:
        if ic > 0.05:
            why.append(
                "News sentiment scores from NewsAPI headlines show a weak positive link with next-day returns in this sample (information coefficient > 0)."
            )
        elif ic < -0.05:
            why.append(
                "In this sample, the sentiment score series moved opposite to next-day returns, so the simple sentiment-follow strategy is not supported."
            )
        else:
            why.append(
                "The sentiment score from headlines did not line up strongly with next-day price moves in this window (IC near zero)."
            )

    headline = (
        f"{ticker}: buy-and-hold Sharpe ratio is {price_only_sharpe:.2f} over the backtest window. "
        f"{trend}"
    )

    strat_note = ""
    if sentiment_source == "none":
        strat_note = (
            "No sentiment time series was available. The sentiment strategy line is omitted. "
            "Enable Alpha Vantage news sentiment (or pass a sentiment series) to compare against buy-and-hold."
        )
    elif sentiment_source == "user" and strategy_sharpe is not None:
        strat_note = (
            f"Strategy uses your supplied sentiment series (sign of signal vs daily returns). "
            f"Strategy Sharpe: {strategy_sharpe:.2f} vs buy-and-hold Sharpe: {price_only_sharpe:.2f}. "
            "This is a toy model and not a trading recommendation."
        )
    elif sentiment_source == "newsapi" and strategy_sharpe is not None:
        strat_note = (
            f"Strategy uses daily news sentiment scores (sign of score) to flip long vs short vs cash. "
            f"Strategy Sharpe: {strategy_sharpe:.2f} vs buy-and-hold Sharpe: {price_only_sharpe:.2f}. "
            "This is a toy model and not a trading recommendation."
        )

    return {
        "headline": headline,
        "recent_trend": trend,
        "quarterly_context": quarter,
        "why_price_might_move": why,
        "methodology": (
            "We use daily close prices from Yahoo Finance (yfinance). "
            "Buy-and-hold Sharpe uses daily log returns. "
            "When sentiment is enabled, we align NewsAPI-derived headline sentiment scores per day "
            "to trading days, forward-fill missing days, and use the sign of the score to scale "
            "daily returns (long if positive, short if negative). "
            "This does not predict the future; it summarizes historical behavior in the sample."
        ),
        "strategy_note": strat_note,
        "disclaimer": (
            "Educational backtest only. Past performance does not guarantee future results. "
            "News APIs are delayed and rate-limited; sentiment labels are noisy."
        ),
    }


def _prices_from_history_payload(history: list[dict]) -> Optional[pd.Series]:
    """Build close price series from [{date|timestamp, close}, ...] (e.g. Kite OHLC)."""
    if not history:
        return None
    rows: list[tuple[Any, float]] = []
    for row in history:
        close = row.get("close")
        if close is None:
            continue
        ts = row.get("date") or row.get("timestamp")
        if not ts:
            continue
        try:
            dt = pd.Timestamp(ts)
            rows.append((dt, float(close)))
        except (TypeError, ValueError):
            continue
    if len(rows) < 10:
        return None
    rows.sort(key=lambda x: x[0])
    idx = pd.DatetimeIndex([r[0] for r in rows])
    vals = [r[1] for r in rows]
    return pd.Series(vals, index=idx).sort_index()


def run_backtest(
    ticker: str = "AAPL",
    sentiment_series: Optional[pd.Series] = None,
    days: int = 252,
    alpha_vantage_key: Optional[str] = None,
    use_alpha_sentiment: bool = True,
    price_history: Optional[list[dict]] = None,
    price_source: Optional[str] = None,
) -> dict[str, Any]:
    """
    Run backtest: buy-and-hold vs sentiment-based (signal = sign(sentiment)).
    If sentiment_series is None and use_alpha_sentiment is True, tries NewsAPI-derived headline sentiment.
    If price_history is provided (e.g. from Kite), uses that instead of yfinance.
    """
    _ = alpha_vantage_key  # Backward-compatible argument; not used when NewsAPI is primary.
    sentiment_source = "none"

    if sentiment_series is not None and len(sentiment_series) > 0:
        sentiment_source = "user"
    elif use_alpha_sentiment:
        sentiment_series = _fetch_newsapi_sentiment_series(ticker, days=days)
        if sentiment_series is not None and len(sentiment_series) > 0:
            sentiment_source = "newsapi"

    prices = _prices_from_history_payload(price_history or [])
    data_source = price_source or ("kite" if prices is not None and len(prices) >= 10 else "yfinance")
    if prices is None or len(prices) < 10:
        prices = _fetch_prices(ticker, days)
        data_source = "yfinance"
    if prices is None or len(prices) < 10:
        yf_hint = ", ".join(_candidate_yfinance_symbols(ticker)) or _normalize_ticker_for_yfinance(ticker)
        return {
            "error": "Could not fetch price data",
            "ticker": ticker,
            "yfinance_symbol": yf_hint,
            "price_only_sharpe": None,
            "strategy_sharpe": None,
            "ic": None,
            "explanation": {
                "headline": f"Could not load price history for {ticker}.",
                "disclaimer": (
                    f"Tried Yahoo Finance as {yf_hint}. "
                    "For Indian stocks use RELIANCE or RELIANCE.NS."
                ),
            },
        }

    price_returns = prices.pct_change().dropna()

    price_only_sharpe = sharpe_ratio(price_returns)

    strategy_returns = pd.Series(dtype=float)
    strategy_sharpe = None
    ic = None

    if sentiment_series is not None and len(sentiment_series) > 0:
        signal = sentiment_series.reindex(prices.index).ffill().bfill().fillna(0)
        strategy_returns = _simulate_returns(prices, signal)
        strategy_sharpe = sharpe_ratio(strategy_returns)
        fwd_ret = prices.pct_change().shift(-1).dropna()
        ic = information_coefficient(signal, fwd_ret)

    total_return_price = float((1 + price_returns).prod() - 1) if len(price_returns) else None
    total_return_strategy = float((1 + strategy_returns).prod() - 1) if len(strategy_returns) else None

    r_21 = _pct_return(prices, 21)
    r_63 = _pct_return(prices, 63)
    vol_ann = float(price_returns.std() * np.sqrt(252)) if len(price_returns) > 1 else None

    explanation = _build_explanation(
        ticker=ticker,
        prices=prices,
        price_returns=price_returns,
        price_only_sharpe=price_only_sharpe,
        strategy_sharpe=strategy_sharpe,
        ic=ic,
        total_return_price=total_return_price,
        total_return_strategy=total_return_strategy,
        sentiment_source=sentiment_source,
    )
    if data_source == "kite":
        explanation["methodology"] = (
            "Daily close prices from Zerodha Kite Connect (NSE). "
            + explanation.get("methodology", "")
        )
    return {
        "ticker": ticker,
        "price_source": data_source,
        "sentiment_source": sentiment_source,
        "price_only_sharpe": round(price_only_sharpe, 4),
        "strategy_sharpe": round(strategy_sharpe, 4) if strategy_sharpe is not None else None,
        "ic": round(ic, 4) if ic is not None else None,
        "total_return_price": total_return_price,
        "total_return_strategy": total_return_strategy,
        "num_days": len(prices),
        "recent_price_context": {
            "approx_return_1m": round(r_21, 4) if r_21 is not None else None,
            "approx_return_3m": round(r_63, 4) if r_63 is not None else None,
            "annualized_volatility": round(vol_ann, 4) if vol_ann is not None else None,
        },
        "explanation": explanation,
    }

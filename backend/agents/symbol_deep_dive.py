"""
Symbol Deep-Dive Agent: for a given stock/symbol, fetch price + details, relevant news,
full price history, find similar stocks, and predict performance based on historical
movements of similar stocks (and name those stocks).
"""
import logging
from typing import Any, Optional

from .base import BaseAgent
from fetch_news import newsapi_client as na

logger = logging.getLogger(__name__)

# Sector -> example tickers (US) for similar-stock comparison. Expand as needed.
SECTOR_PEERS = {
    "Technology": ["MSFT", "GOOGL", "META", "NVDA", "AVGO"],
    "Financial Services": ["JPM", "BAC", "WFC", "GS", "MS"],
    "Healthcare": ["JNJ", "UNH", "PFE", "ABBV", "TMO"],
    "Consumer Cyclical": ["AMZN", "TSLA", "HD", "NKE", "MCD"],
    "Consumer Defensive": ["PG", "KO", "PEP", "WMT", "COST"],
    "Industrials": ["CAT", "UNP", "HON", "UPS", "BA"],
    "Energy": ["XOM", "CVX", "COP", "SLB", "EOG"],
    "Basic Materials": ["LIN", "APD", "SHW", "ECL", "FCX"],
    "Real Estate": ["PLD", "AMT", "EQIX", "PSA", "O"],
    "Communication Services": ["GOOGL", "META", "NFLX", "DIS", "CMCSA"],
    "Utilities": ["NEE", "DUK", "SO", "D", "AEP"],
}


def _fetch_symbol_info_and_history(symbol: str) -> dict:
    """Fetch current price, details, and history via yfinance."""
    out = {"symbol": symbol, "current_price": None, "info": {}, "history": [], "sector": None, "error": None}
    try:
        import yfinance as yf
        t = yf.Ticker(symbol)
        info = t.info
        out["info"] = {k: v for k, v in info.items() if v is not None and k in (
            "shortName", "sector", "industry", "marketCap", "previousClose", "open", "volume", "averageVolume",
            "fiftyTwoWeekHigh", "fiftyTwoWeekLow", "recommendationKey", "targetMeanPrice"
        )}
        out["current_price"] = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose")
        out["sector"] = (info.get("sector") or "Technology").strip()
        hist = t.history(period="1y")
        if hist is not None and not hist.empty:
            out["history"] = hist["Close"].tail(30).tolist()
    except Exception as e:
        out["error"] = str(e)
        logger.warning("yfinance fetch for %s: %s", symbol, e)
    return out


def _fetch_news_for_symbol(symbol: str, limit: int = 10) -> list:
    """Fetch relevant news for symbol (NewsAPI primary)."""
    if not na.is_configured():
        return []
    try:
        items = na.fetch_symbol_news(symbol, limit=limit)
        return [
            {
                "title": i.get("title", ""),
                "summary": (i.get("summary") or "")[:300],
                "sentiment": "Neutral",
            }
            for i in items[:limit]
        ]
    except Exception as e:
        logger.warning("News fetch for %s: %s", symbol, e)
        return []


def _get_similar_tickers(sector: str, exclude: str, max_peers: int = 5) -> list:
    """Return list of similar (peer) tickers by sector."""
    peers = SECTOR_PEERS.get(sector, SECTOR_PEERS.get("Technology", []))
    return [p for p in peers if p.upper() != exclude.upper()][:max_peers]


def _historical_movements_summary(symbol: str, similar_tickers: list) -> str:
    """Get short summary of recent returns for symbol and similar tickers (yfinance)."""
    lines = []
    try:
        import yfinance as yf
        for sym in [symbol] + similar_tickers[:3]:
            t = yf.Ticker(sym)
            hist = t.history(period="1mo")
            if hist is not None and len(hist) >= 2:
                start = hist["Close"].iloc[0]
                end = hist["Close"].iloc[-1]
                pct = ((end - start) / start * 100) if start else 0
                lines.append(f"{sym}: 1M return {pct:.2f}%")
    except Exception as e:
        lines.append(f"Error: {e}")
    return "; ".join(lines) if lines else "No history"


def _build_prediction_with_llm(symbol: str, symbol_info: dict, news: list, similar_tickers: list, movements_summary: str) -> str:
    """Use Groq/OpenAI to generate prediction and name similar stocks."""
    from intelligence.llm import chat_completion
    news_text = "\n".join([f"- {n.get('title', '')} ({n.get('sentiment', '')})" for n in news[:5]])
    prompt = (
        f"Symbol: {symbol}. Sector: {symbol_info.get('sector', 'N/A')}. Current price context: {symbol_info.get('current_price')}.\n"
        f"Similar stocks (by sector) used for comparison: {', '.join(similar_tickers)}.\n"
        f"Recent price movements (1M): {movements_summary}.\n"
        f"Recent news headlines (sentiment):\n{news_text}\n\n"
        "Based on this symbol's details, relevant news, and historical movements of the similar stocks listed above, "
        "write a short paragraph: (1) How do you expect this stock to perform in the near term? (2) Explicitly name the similar stocks you used for comparison. Be concise."
    )
    result = chat_completion(prompt, system_content="You are a quantitative equity analyst. Be specific and cite the similar stocks.", max_tokens=350)
    return result or (
        f"Based on sector peers {', '.join(similar_tickers)} and recent news, monitor {symbol} for sector-driven moves. "
        "Similar stocks used: " + ", ".join(similar_tickers) + "."
    )


class SymbolDeepDiveAgent(BaseAgent):
    """
    Fetches for a given symbol: price + details, relevant news, history;
    finds similar stocks; predicts performance based on similar stocks' historical movements;
    names the similar stocks in the output.
    """

    def __init__(self):
        super().__init__(name="SymbolDeepDive", role="Stock deep-dive: price, news, similar stocks, prediction")

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        symbol = (context.get("symbol") or "").upper().strip()
        if not symbol:
            return {"error": "No symbol provided", "prediction": "", "similar_stocks": []}

        symbol_info = _fetch_symbol_info_and_history(symbol)
        if symbol_info.get("error"):
            return {"error": symbol_info["error"], "prediction": "", "similar_stocks": []}

        news = _fetch_news_for_symbol(symbol, limit=10)
        sector = symbol_info.get("sector") or "Technology"
        similar_tickers = _get_similar_tickers(sector, symbol, max_peers=5)
        movements_summary = _historical_movements_summary(symbol, similar_tickers)
        prediction = _build_prediction_with_llm(symbol, symbol_info, news, similar_tickers, movements_summary)

        self._remember({
            "symbol": symbol,
            "similar_stocks": similar_tickers,
            "prediction": prediction[:200],
        })

        return {
            "symbol": symbol,
            "current_price": symbol_info.get("current_price"),
            "sector": sector,
            "company_name": (symbol_info.get("info") or {}).get("shortName"),
            "relevant_news": news[:5],
            "similar_stocks": similar_tickers,
            "similar_stocks_movements_summary": movements_summary,
            "prediction": prediction,
        }

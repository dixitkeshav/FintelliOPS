# Market Data & News APIs — India, US & Global

Use this as a reference for **market data**, **news**, and **alternative data** for Indian, US, and global markets. Alpha Vantage is a good start; for production you’ll want additional sources.

---

## US markets

| API | Data | Notes |
|-----|------|--------|
| **Alpha Vantage** | Quotes, news sentiment, FX, crypto, fundamentals | Free tier: 25 req/day. Good for news + GLOBAL_QUOTE. |
| **Polygon.io** | Real-time & historical equities, options, forex | Free tier limited; paid for real-time. |
| **Finnhub** | Real-time quotes, news, fundamentals, earnings | Free tier: 60 req/min. Good for news + quotes. |
| **Yahoo Finance (yfinance)** | Quotes, history, info (sector, cap) | No official API; use `yfinance` library. Free, rate-limit yourself. |
| **Twelve Data** | Stocks, forex, crypto, ETFs | Free tier: 8 req/min. |
| **IEX Cloud** | US equities, fundamentals, news | Free tier available. |
| **Benzinga** | News, earnings, ratings | Paid; very rich for news/sentiment. |
| **NewsAPI** | General news (keyword search) | Free tier: 100 req/day. |

---

## Indian markets

| API / Source | Data | Notes |
|--------------|------|--------|
| **NSE India** | Nifty, NSE indices, equity quotes (delayed) | Official site; scrape or use unofficial APIs. |
| **BSE India** | BSE Sensex, BSE stocks | Official; check terms for programmatic use. |
| **Yahoo Finance** | NSE/BSE symbols (e.g. `RELIANCE.NS`, `TCS.BO`) | Use `yfinance` for RELIANCE.NS, ^NSEI, ^BSESN. |
| **Alpha Vantage** | Global quote for `.NS`/`.BO` if supported | Check symbol format (e.g. NSE/BSE suffix). |
| **Moneycontrol** | News, indices (scraping) | For news; respect robots.txt and rate limits. |
| **Economic Times** | News (RSS/API if available) | Often via RSS or scraping. |
| **Kite Connect (Zerodha)** | Live quotes, order placement (India) | Requires Zerodha account; proper for trading. |
| **NSE PyPI** (unofficial) | NSE data via Python | Community packages; verify before production. |

---

## Global (multi-region)

| API | Coverage | Notes |
|-----|----------|--------|
| **Alpha Vantage** | US, FX, crypto, some global | Single key for many asset classes. |
| **Twelve Data** | Stocks, forex, crypto (global) | Multiple exchanges. |
| **Yahoo Finance** | Many global symbols (suffixes: .L, .PA, .NS, etc.) | One library for global quotes/history. |
| **NewsAPI** | Global news (keyword) | Good for “India + rate” or “Fed + stocks”. |
| **Exchange-specific** | LSE, Euronext, HKEX, etc. | Use official or licensed feeds for production. |

---

## What to use where (in this project)

- **Live ticker / indices (US + India):**  
  **yfinance** for ^GSPC, ^NSEI, ^BSESN, AAPL, RELIANCE.NS, etc. Already used in `live_ticker` and Symbol Deep-Dive.

- **News (US + global):**  
  **Alpha Vantage** NEWS_SENTIMENT (already used). Add **Finnhub** or **Benzinga** for more depth.

- **Indian news:**  
  Add **RSS** (Moneycontrol, ET) or a **NewsAPI** keyword search for “NSE”, “RBI”, “India stocks”, etc.

- **Real-time / production:**  
  Consider **Polygon**, **Finnhub**, or **Kite (India)** for low-latency quotes and reliability.

---

## Env vars (examples)

```env
ALPHA_VANTAGE_API_KEY=...
GROQ_API_KEY=...
FINNHUB_API_KEY=...
POLYGON_API_KEY=...
NEWSAPI_KEY=...
```

---

## Adding a new API in code

1. **Config:** Add the key to `config/settings.py` or `.env`.
2. **Client:** Add a small module under `fetch_news` or `DATA_FETCHING` (e.g. `finnhub_client.py`) that returns normalized items (e.g. `{ "title", "url", "sentiment", "source" }`).
3. **Views:** In `fetch_news/views.py`, call the new client and merge results with existing news (or switch by `?source=finnhub`).
4. **Live ticker:** For new symbols or exchanges, extend the `symbols` list in the `live_ticker` view and map exchange suffixes (e.g. `.NS`, `.BO`) if needed.

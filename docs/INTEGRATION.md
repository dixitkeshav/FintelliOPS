# Frontend-Backend Integration Guide

This document describes how the Next.js frontend connects to the Django backend and what APIs/services are required.

## Environment Variables

### Frontend (`.env.local`)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000    # Django backend URL
NEXT_PUBLIC_WS_URL=ws://localhost:8000       # WebSocket URL (optional, for future use)
```

### Backend (`.env`)

```env
ALPHA_VANTAGE_API_KEY=your_key_here   # Required for news & ticker search
GROQ_API_KEY=your_key_here            # Optional: for GenAI agent insights
DJANGO_DEBUG=True
DJANGO_SECRET_KEY=your_secret
```

## API Endpoints Used by Frontend

| Frontend Component | Backend Endpoint | Method | Purpose |
|-------------------|------------------|--------|---------|
| NewsFeed | `/api/fetch-news/` | GET | Financial news from Alpha Vantage |
| TradingChart | `/api/market/<symbol>/history/` | GET | OHLC price history (yfinance) |
| SentimentChart | `/api/chart-data/` | GET | Sentiment distribution & trend |
| MarketTicker, PriceWidget | `/api/live-ticker/` | GET | Live indices & stock prices |
| AgentCard | `/api/agents/run/` | POST | Multi-agent AI pipeline |
| (Future) Symbol Deep-Dive | `/api/agents/symbol-deep-dive/?symbol=AAPL` | GET | Stock analysis |

## Component-to-API Mapping

### 1. News Feed
- **Hook:** `useNewsFeed`
- **API:** `GET /api/fetch-news/`
- **Response:** `{ articles: [{ title, summary, url, sentiment, source, time_published }] }`
- **Polling:** Every 30 seconds

### 2. Trading Chart
- **API:** `GET /api/market/{symbol}/history/?period=1mo`
- **Query params:** `period` = 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y
- **Response:** `{ symbol, history: [{ timestamp, open, high, low, close, volume }] }`
- **Default symbol:** ^NSEI (Nifty 50)

### 3. Sentiment Chart
- **API:** `GET /api/chart-data/`
- **Response:** `{ distribution: { labels, data }, trend: { labels, positive[], negative[] } }`
- **Data source:** Analyzes stored NewsArticle sentiment or returns sample data

### 4. Live Ticker
- **Hook:** `useLiveTicker`
- **API:** `GET /api/live-ticker/`
- **Response:** `{ tickers: [{ symbol, name, price, change_pct }] }`
- **Polling:** Every 2 minutes
- **Requires:** yfinance, network access

### 5. Agent Insights
- **Hook:** `useAgentInsights`
- **API:** `POST /api/agents/run/` (optional: `?ticker=AAPL`)
- **Response:** `{ news_scout, macro_context, market_reaction, risk, decision, recommendation }`
- **Polling:** Every 5 minutes
- **Requires:** Alpha Vantage for news, optional Groq for LLM synthesis

## Additional Backend APIs (Available but not yet wired)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/agents/symbol-deep-dive/?symbol=AAPL` | GET | Price, news, similar stocks, prediction |
| `/api/analyze-sentiment/` | POST | FinBERT sentiment for custom text |
| `/api/custom-sentiment/` | POST | Aggregate sentiment for a ticker |
| `/api/quant/signals/` | POST | Sentiment momentum, MA crossover |
| `/api/quant/backtest/?ticker=AAPL` | GET | Backtest price vs sentiment strategy |
| `/api/cross-domain/?domain=crypto` | GET | Cross-domain news (crypto, commodities, etc.) |
| `/api/search-ticker/?q=AAPL` | GET | Ticker symbol autocomplete |

## CORS

The backend allows requests from `http://localhost:3000` and `http://127.0.0.1:3000`. For production, set `CORS_ALLOWED_ORIGINS` in Django settings.

## Running the Stack

1. **Backend:** `cd backend && python manage.py runserver` (port 8000)
2. **Frontend:** `cd frontend && npm run dev` (port 3000)
3. Ensure `ALPHA_VANTAGE_API_KEY` is set for news and live ticker to work.

## Data Flow Summary

```
┌─────────────┐     GET /api/fetch-news/      ┌──────────────┐
│  NewsFeed   │◄─────────────────────────────►│  Django      │
└─────────────┘                               │  Alpha       │
                                              │  Vantage     │
┌─────────────┐     GET /api/chart-data/      └──────────────┘
│ Sentiment   │◄─────────────────────────────►│ DB / Sample  │
│ Chart       │                               └──────────────┘
└─────────────┘

┌─────────────┐     GET /api/market/{sym}/history/
│ Trading     │◄─────────────────────────────►│ yfinance     │
│ Chart       │                               └──────────────┘
└─────────────┘

┌─────────────┐     GET /api/live-ticker/
│ Market      │◄─────────────────────────────►│ yfinance     │
│ Ticker      │                               └──────────────┘
└─────────────┘

┌─────────────┐     POST /api/agents/run/
│ Agent       │◄─────────────────────────────►│ Agent        │
│ Cards       │                               │ Orchestrator │
└─────────────┘                               └──────────────┘
```

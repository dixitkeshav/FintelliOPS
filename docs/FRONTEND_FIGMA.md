# Frontend & Figma Integration

## Current frontend (terminal style)

The app now uses a **Trading View / news-channel style** layout:

- **Top:** Scrolling ticker strip of indices and stock prices (e.g. S&P 500, Nifty, Sensex, AAPL, RELIANCE.NS) with % change. Data from `/api/live-ticker/` (yfinance).
- **Below:** Scrolling news headlines (sentiment-colored). Data from `/api/fetch-news/`.
- **Main area:** Cards for Live News, Sentiment chart, **Stock Deep-Dive** (one symbol → price, news, similar stocks, prediction), **Multi-Agent** run, GenAI news analysis, and trend chart.

Assets:

- `fetch_news/templates/index.html` — main page
- `fetch_news/static/css/terminal.css` — terminal theme (dark, ticker, cards)
- `fetch_news/static/js/terminal.js` — ticker, news, charts, deep-dive, agents

---

## Using Figma (or another design tool)

You can keep the **same backend APIs** and replace or refine the UI in two ways.

### Option 1: Design in Figma, export to HTML/CSS

1. **Design** the layout in Figma (e.g. ticker, sidebar, cards, charts).
2. **Export:**
   - Use a plugin like **Figma to HTML** or **Anima** to export components to HTML + CSS, or
   - Manually build HTML/CSS from the design (measurements, colors, fonts from Figma).
3. **Integrate with Django:**
   - Put the exported (or hand-coded) HTML into a **Django template** (e.g. `index.html`).
   - Keep the same **IDs and CSS classes** that `terminal.js` (or your script) uses, e.g.:
     - `#ticker-strip-inner`, `#news-feed`, `#sentimentChart`, `#trendChart`
     - `#deep-dive-symbol`, `#deep-dive-result`, `#agents-result`, `#news-text`, `#news-analysis-result`
   - Include your new CSS **after** Bootstrap (or replace our `terminal.css` with your styles).
   - Keep the same `<script src="{% static 'js/terminal.js' %}">` (or your JS that calls the same APIs).
4. **Data:** No backend change. JS still calls `/api/live-ticker/`, `/api/fetch-news/`, `/api/agents/run/`, `/api/agents/symbol-deep-dive/`, etc.

So: **Figma → HTML/CSS → paste into Django template and wire same IDs/JS.**

### Option 2: React/Next.js (or other SPA) from Figma

1. Design in Figma.
2. Build a **separate frontend** (e.g. React, Next.js) that talks to your Django **REST APIs** only (no Django templates for this app).
3. Deploy:
   - **Django** on one host (e.g. `api.yoursite.com`) with CORS allowed for your frontend origin.
   - **React** on another (e.g. Vercel, Netlify, or same domain with Nginx routing).
4. In the SPA, call the same endpoints:
   - `GET /api/live-ticker/`
   - `GET /api/fetch-news/`
   - `POST /api/agents/run/`
   - `GET /api/agents/symbol-deep-dive/?symbol=AAPL`
   - etc.

Figma → design; then implement in React (or export with a Figma-to-React plugin) and point the app at your Django API.

---

## Making the ticker “like a news channel”

Already in place:

- **Scrolling ticker strip** — CSS animation, content from `/api/live-ticker/` (symbol, name, price, change %). Refreshes every 2 minutes.
- **Scrolling headlines** — News titles + sentiment from `/api/fetch-news/`, infinite scroll animation.

To make it feel more “live”:

- **Refresh:** Decrease the `setInterval` in `terminal.js` for `loadTickerStrip` and `refreshNews` (e.g. 60s), or use WebSockets to push new ticker/news from the backend.
- **More symbols:** Add indices/tickers in the backend `live_ticker` view (e.g. more Indian symbols: `.NS`, `.BO` via yfinance).
- **Sound / alerts:** Optional browser notifications or a small sound when a new headline or threshold is met (implement in JS).

---

## Summary

- **Current stack:** Django templates + terminal CSS + `terminal.js` → Trading View / news-channel style with moving ticker and headlines.
- **Figma:** Use Figma to design; export to HTML/CSS and plug into the same template + JS, **or** build a separate SPA (e.g. React) that uses the same Django APIs.
- **APIs** stay the same; only the presentation layer (HTML/CSS/JS or React) changes.

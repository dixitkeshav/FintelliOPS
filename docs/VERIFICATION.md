# Verification checklist (backend + Next.js frontend)

## Prerequisites

1. **Backend** (from `Financial-News-Sentiment-Analysis/backend/`):
   ```bash
   pip install -r ../requirements.txt
   python manage.py migrate
   python manage.py runserver 0.0.0.0:8000
   ```
2. **Frontend** (from `Financial-News-Sentiment-Analysis/frontend/`):
   ```bash
   cp .env.local.example .env.local   # set NEXT_PUBLIC_API_URL if Django is not on :8000
   npm install
   npm run dev
   ```
   Open `http://localhost:3000/dashboard/...`

3. **Optional keys** (in `backend/.env`):
   - `ALPHA_VANTAGE_API_KEY` — news + backtest sentiment series (rate-limited).
   - `FINNHUB_API_KEY` — faster quotes / scanner path when configured.

## API smoke tests (curl)

With Django on `http://127.0.0.1:8000`:

```bash
# Live ticker (yfinance / Finnhub)
curl -s "http://127.0.0.1:8000/api/live-ticker/" | head -c 400

# Options chain — use a liquid US symbol (e.g. AAPL, SPY)
curl -s "http://127.0.0.1:8000/api/options-chain/?symbol=AAPL&nocache=1" | head -c 600

# Screener (limit symbol count for speed)
curl -s "http://127.0.0.1:8000/api/scanner/?symbols=AAPL,MSFT&period=3mo" | head -c 600

# Backtest
curl -s "http://127.0.0.1:8000/api/quant/backtest/?ticker=AAPL&use_alpha_sentiment=false" | head -c 800
```

**Expected:**

- **Options:** JSON with `"data": [ ... ]` for US symbols; Indian symbols often return `"error"` (no chain on free Yahoo/Finnhub).
- **Screener:** JSON with `"results": [ ... ]` per symbol. With Finnhub + FinBERT, first run can take **tens of seconds** if many symbols are scanned.
- **Backtest:** JSON with `"num_days"` and metrics; `"use_alpha_sentiment=false"` avoids Alpha Vantage and still returns buy-and-hold metrics.

## Common failures

| Symptom | Cause | Fix |
|--------|--------|-----|
| Frontend shows empty / failed fetch | Wrong `NEXT_PUBLIC_API_URL` | Set `.env.local` to your Django origin |
| CORS errors | Browser blocks cross-origin | `CORS_ALLOW_ALL_ORIGINS = True` is on; add origin in `settings.py` if you use a custom port |
| Options empty for `RELIANCE.NS` | Yahoo often has no option chain for that symbol | Test with `AAPL` or `SPY` |
| Screener very slow | Finnhub path runs FinBERT on up to 5 headlines per symbol | Reduce symbols or disable Finnhub to use Alpha-only path |
| Backtest `Could not fetch price` | Bad ticker or yfinance blocked | Retry; check network |

## UI

- Dashboard main area scrolls vertically (long Options / Backtest pages).
- Sidebar uses Next.js `Link` for client-side navigation.

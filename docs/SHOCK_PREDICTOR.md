# Market Shock Predictor (ShockAgent)

Integrated module for Nifty / Bank Nifty / Sensex intraday shock detection, live RSS scoring, WebSocket alerts, and orchestrator enrichment.

## Backend setup

```bash
cd backend
pip install feedparser   # if not already installed
python manage.py migrate
python manage.py backtest_shocks --fast --skip-newsapi --indices nifty   # ~40 Nifty shock days (recommended)
# python manage.py backtest_shocks --indices nifty,banknifty,sensex   # all indices (Sensex yfinance can be noisy)
# With NewsAPI headlines (150 req/day on free tier):
# NEWSAPI_KEY=... python manage.py backtest_shocks --skip-newsapi
# Full FinBERT on each day (slow):
# python manage.py backtest_shocks
```

### Environment (`backend/.env`)

```env
NEWSAPI_KEY=              # optional, for historical headlines in backtest
TELEGRAM_BOT_TOKEN=       # optional, alerts when score >= 70
TELEGRAM_CHAT_ID=
REDIS_URL=redis://127.0.0.1:6379/0
CELERY_BROKER_URL=redis://127.0.0.1:6379/1
```

## Run services

```bash
# Terminal 1 — ASGI (required for WebSockets)
daphne -b 0.0.0.0 -p 8000 config.asgi:application

# Terminal 2 — Celery worker
celery -A config worker -l info

# Terminal 3 — Celery Beat (30s poll during market hours 09:00–15:35 IST)
celery -A config beat -l info

# Terminal 4 — Frontend
cd ../frontend && npm run dev
```

Dashboard: **Shock Alert** → `/dashboard/shock`

## API

| Endpoint | Description |
|----------|-------------|
| `GET /api/shock/score/` | Latest score from Redis |
| `GET /api/shock/history/?page=1&cause=policy` | Backtested shock events |
| `GET /api/shock/alerts/` | Fired live alerts |
| `GET /api/shock/patterns/` | Precursor fingerprints per cause |
| `WS /ws/shock/` | Live score stream |

## Agent pipeline

`ShockAgent` runs in `agents/orchestrator.py` after Risk and before Decision. Agent run response includes `shock` with `shock_probability`, `trigger_cause`, `suggested_hedge`.

## Frontend env

```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
NEXT_PUBLIC_WS_URL=ws://127.0.0.1:8000
```

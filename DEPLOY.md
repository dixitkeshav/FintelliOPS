# Deploy FintelliAI — Vercel + Render (free tier)

One **PostgreSQL** database on Render is shared by:

| Consumer | Tables |
|----------|--------|
| **Django** | `fetch_news_newsarticle`, auth, admin, etc. |
| **Prisma (Next.js)** | `OHLCVCandle`, `Signal`, `BacktestRun`, `Settings`, … |

Django and Prisma use different table names — they coexist in the same database.

---

## Pre-deploy checklist (repo)

- [ ] No secrets in Git (`backend/.env`, `frontend/.env.local` must not be tracked)
- [ ] `.env.example` committed (placeholders only)
- [ ] `TRUEDATA` removed / disabled — free APIs are primary
- [ ] GitHub repo pushed to `main`

---

## Step 1 — Render Postgres (database)

1. [Render Dashboard](https://dashboard.render.com) → **New +** → **PostgreSQL**
2. Name: `fintelli-db` · Plan: **Free**
3. After create, open **Connections**:
   - **Internal Database URL** → paste into Render **backend** env as `DATABASE_URL`
   - **External Database URL** → paste into **Vercel** env as `DATABASE_URL` (Prisma from Vercel needs external + SSL)

> Free Postgres expires after 90 days of inactivity — recreate if needed.

---

## Step 2 — Render backend (Django API)

**Option A — Blueprint (easiest)**  
New → **Blueprint** → connect GitHub repo → Render reads `render.yaml`.

**Option B — Manual**

| Setting | Value |
|---------|--------|
| Type | Web Service |
| Root Directory | `backend` |
| Runtime | Python 3 |
| Build Command | `./build.sh` |
| Start Command | `daphne -b 0.0.0.0 -p $PORT config.asgi:application` |
| Plan | Free |

**Environment variables** (Render → Environment):

| Key | Value |
|-----|--------|
| `DATABASE_URL` | From Postgres (Internal URL) |
| `DATABASE_SSL` | `true` |
| `DJANGO_SECRET_KEY` | Random string |
| `DJANGO_DEBUG` | `False` |
| `DJANGO_ALLOWED_HOSTS` | `your-service.onrender.com` |
| `CORS_EXTRA_ORIGINS` | `https://your-app.vercel.app` (after Vercel deploy) |
| `NEWSAPI_KEY` | Your key |
| `FINNHUB_API_KEY` | Your key |
| `GROQ_API_KEY` | Your key |
| `ALPHA_VANTAGE_API_KEY` | Your key |

Leave `REDIS_URL` unset on free tier (in-memory cache/channels).

Copy API URL: `https://fintelli-api.onrender.com` (yours will differ).

---

## Step 3 — Vercel frontend (Next.js)

1. [Vercel Dashboard](https://vercel.com) → **Add New Project** → import GitHub repo
2. **Root Directory**: `frontend`
3. Framework: Next.js (auto)

**Environment variables**:

| Key | Value |
|-----|--------|
| `DATABASE_URL` | Postgres **External** URL (same DB as Django) |
| `NEXT_PUBLIC_API_URL` | `https://your-api.onrender.com` |
| `NEXT_PUBLIC_WS_URL` | `wss://your-api.onrender.com` |
| `NEXTAUTH_SECRET` | Random string |
| `NEXTAUTH_URL` | `https://your-app.vercel.app` |
| `DASHBOARD_PASSWORD` | Demo login password |

`vercel.json` runs `prisma migrate deploy` on each build to create Prisma tables.

4. Deploy → copy Vercel URL
5. Go back to Render → set `CORS_EXTRA_ORIGINS` to your Vercel URL → redeploy backend

---

## Step 4 — Verify

| Check | URL / action |
|-------|----------------|
| News API | `https://your-api.onrender.com/api/fetch-news/` |
| Login | `https://your-app.vercel.app/login` |
| Agents | Dashboard → Agent Insights |
| Backtest | Dashboard → Backtest |
| DB | Render Postgres → **Connect** → `\dt` shows Django + Prisma tables |

---

## Free tier limits

| Limit | Impact |
|-------|--------|
| Render sleeps after ~15 min idle | First load 30–60s cold start |
| 512 MB RAM on free web service | FinBERT first load is slow; may need upgrade if OOM |
| No free Redis on Render | Celery/shock background jobs off; REST polling works |
| Vercel serverless timeout | Very long backtests should hit Render API directly |

---

## Open source / LinkedIn

Commit only `.env.example` and `frontend/.env.local.example`.  
Tell contributors: copy examples, add their own API keys, never commit `.env` files.

---

## Local dev (unchanged)

```bash
# Backend — SQLite if DATABASE_URL unset
cd backend && pip install -r ../requirements.txt && python manage.py runserver

# Frontend
cd frontend && npm install && npm run dev
```

For local shared Postgres: `docker compose -f docker-compose.edge.yml up -d` and set `DATABASE_URL` in both env files.

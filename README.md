# FintelliAI — Multi-Agent Financial Intelligence

Multi-agent pipeline for financial news analysis, sentiment, technical signals, debate-driven recommendations, and shock prediction. Django backend + Next.js dashboard.

> **Synthetic demo data** available for offline testing — no live API keys required.

## Quick start

### Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r ../requirements.txt
cp ../.env.example .env    # optional: GROQ_API_KEY, NEWSAPI_KEY
python manage.py migrate
python manage.py runserver
```

### Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local   # NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
npm run dev
```

Open [http://localhost:3000/dashboard/agents](http://localhost:3000/dashboard/agents)

## Agent pipeline

| Step | Agent | Role |
|------|-------|------|
| 1 | News Scout | Sentiment spike detection |
| 2 | Macro Context | Rates, CPI, GDP linkage |
| 3 | Technical | RSI, MACD, moving averages |
| 4 | Market Reaction | Historical reaction patterns |
| 5 | Risk | Concentration and downside flags |
| 6 | Bull / Bear Research | Structured bull vs bear theses |
| 7 | Risk Committee | Position constraints |
| 8 | Debate Facilitator | Resolves bull vs bear stance |
| 9 | Shock Predictor | Nifty shock probability (optional) |
| 10 | Decision | Final BUY / HOLD / SELL synthesis |

## Synthetic testing (no API keys)

### CLI

```bash
cd backend
PYTHONPATH=. python3 -m agents.run_synthetic_test RELIANCE
PYTHONPATH=. python3 -m agents.run_synthetic_test NIFTY
```

### API

```bash
curl -X POST http://127.0.0.1:8000/api/agents/run/ \
  -H "Content-Type: application/json" \
  -d '{"ticker":"RELIANCE","use_synthetic":true}'
```

### UI

Click **Run Synthetic Demo** on the Agent Insights page.

## API response structure

Each run returns per-agent cards, pipeline steps, and evaluation scores:

```json
{
  "pipeline_completed": true,
  "agents": {
    "news_scout": { "called": true, "output": "...", "signal": "positive", "metrics": {} },
    "decision": { "called": true, "output": "HOLD ...", "signal": "neutral", "action": "HOLD" }
  },
  "evaluation": {
    "agents_called": ["news_scout", "macro_context", "..."],
    "coverage_score": 100,
    "overall_score": 95.2
  },
  "recommendation": "HOLD with 50% max size..."
}
```

## Synthetic data

Located in `backend/agents/data/synthetic_articles.json`:

- **RELIANCE** — 8 fabricated headlines (mixed sentiment)
- **NIFTY** — 6 index-level headlines
- **DEFAULT** — 5 general market headlines

All identifiers and content are fictional demo data.

## Environment variables

| Variable | Purpose |
|----------|---------|
| `GROQ_API_KEY` | LLM synthesis (free tier friendly) |
| `NEWSAPI_KEY` | Live news ingestion |
| `AZURE_OPENAI_ENDPOINT` | Optional Azure OpenAI |
| `AZURE_OPENAI_API_KEY` | Optional Azure OpenAI key |

## Project structure

```
FNSA-Agent-Showcase/
├── backend/agents/           # Multi-agent orchestrator + synthetic data
├── backend/fetch_news/       # News APIs + /api/agents/run/
├── backend/quant/            # Technical indicators
├── backend/shock_predictor/  # Shock agent
└── frontend/app/dashboard/agents/  # Agent Insights UI
```

## Author

**Keshav Dixit** — B.Tech Computer and Communication Engineering, Manipal University Jaipur

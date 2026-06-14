
# FintelliOPS

This repository contains FintelliOPS: an agent-orchestrated market intelligence system that combines multiple IQ layers (Foundry IQ, Fabric IQ, Work IQ) to answer market queries and produce structured investment briefings.

Example query

> "RBI holds repo rate, impact on banking sector."

Workflow overview

1. A user submits a market query to the orchestrator.
2. The orchestrator runs five agents sequentially, each enriching a shared context dictionary.
   - Agent 1: News Scout — retrieves relevant market events from Foundry IQ (Azure AI Search with semantic config).
   - Agent 2: Macro Context — combines Foundry IQ with Fabric IQ (semantic knowledge graph built on NetworkX).
   - Agent 3: Market Reaction — scores sector beta and rate sensitivity using Fabric IQ.
   - Agent 4: Risk — computes a 0–10 risk score and recommended actions.
   - Agent 5: Decision Agent — synthesizes outputs using Foundry IQ, Fabric IQ, and Work IQ to produce a seven-section investment briefing.

**Architecture**

ASCII diagram

```
                +----------------+
                |   User Query   |
                +--------+-------+
                         |
                         v
                +----------------+
                |  Orchestrator  |
                +--------+-------+
                         |
            Shared Context Dictionary (in-memory / persisted)
                         |
    +--------------------+--------------------+--------------------+
    |                    |                    |                    |
    v                    v                    v                    v
+----------+   +----------------+   +----------------+   +----------------+
| News     |-->| Macro Context  |-->| Market Reaction|-->| Risk Scoring   |
| Scout    |   | (Fabric +      |   | (Fabric IQ)    |   | (0-10 risk     |
| (Foundry)|   |  Foundry IQ)   |   |                |   |  score & action)|
+----------+   +----------------+   +----------------+   +----------------+
                                                     |
                                                     v
                                            +----------------+
                                            | Decision Agent |
                                            | (synthesizes   |
                                            |  Foundry,      |
                                            |  Fabric, Work) |
                                            +----------------+
                                                     |
                                                     v
                                            +----------------+
                                            | Investment      |
                                            | Briefing (7-    |
                                            | sections)       |
                                            +----------------+


**IQ Layers**

- **Foundry IQ**: Azure AI Search (semantic) used as the primary cited knowledge source.
  - Tech: Azure AI Search, semantic indexing
  - Role: Retrieve facts, documents, statements (e.g., RBI/Fed policy text, earnings reports)
  - Example output: cited passages with metadata and relevance scores
- **Fabric IQ**: Semantic knowledge graph built on NetworkX modeling sectors, correlations, and thresholds.
  - Tech: NetworkX-based graph, embedding-backed relations, local scoring functions
  - Role: Provide business context, sector relationships, sensitivity scoring
  - Example output: sector beta, rate sensitivity, semantic neighbors
- **Work IQ**: Analyst delivery signals and presentation controls (how to synthesize and format output).
  - Tech: internal store of templates, delivery heuristics, timestamped signals
  - Role: Structure briefings, tone, and analyst notes
  - Example output: delivery style, section ordering, prioritization

IQ Layer Table

| Layer | Purpose | Technologies | Example Inputs/Outputs |
|---|---:|---|---|
| Foundry IQ | Cited knowledge retrieval | Azure AI Search (semantic) | Inputs: query, filters. Outputs: passages, doc ids, confidence |
| Fabric IQ | Semantic business graph & scoring | NetworkX, embeddings | Inputs: Foundry passages. Outputs: sector beta, sensitivity scores |
| Work IQ | Analyst delivery + templates | Internal templates, heuristics | Inputs: synthesized analysis. Outputs: formatted briefing sections |

**Seven-section investment briefing (Decision Agent output)**

1. Executive Summary
2. Key Drivers (cited items)
3. Macro Context & Correlations
4. Sector Reaction & Scoring
5. Risk Assessment (0–10) & Rationale
6. Recommended Action(s)
7. Sources & Citations (Foundry IQ links)

**Setup & Development**

- Prerequisites
  - macOS or Linux
  - Python 3.10+ (project uses virtualenv)
  - PostgreSQL for production (SQLite is included for quick dev)
  - Azure credentials & indexing pipeline for Foundry IQ

- Quickstart (development)

```bash
# from repo root
python3 -m venv backend/.venv
source backend/.venv/bin/activate
pip install -r requirements.txt
cd backend
# create .env or set environment variables as needed
cp .env.example .env 2>/dev/null || true
python manage.py migrate
python manage.py runserver
```

- Environment variables (examples)
  - `DJANGO_SETTINGS_MODULE=backend.settings`
  - `DATABASE_URL=postgres://user:pass@localhost:5432/fintelliops` (or use default SQLite)
  - `AZURE_SEARCH_ENDPOINT` and `AZURE_SEARCH_KEY` for Foundry IQ

- Indexing & IQ ingestion
  - Foundry IQ: run the ingestion/indexing script to populate Azure Search with synthetic earnings, policy statements, sector analyses. See [backend/fintelliops_data](fintelliops_data) for example payloads.
  - Fabric IQ: run the graph builder in [backend/fintelliops_iq](backend/fintelliops_iq) (e.g., `python -m fintelliops_iq.indexer`) to build NetworkX graphs from ontology files.

- Running the orchestrator
  - To run a single query through the orchestrator use the management command or script (examples):

```bash
python backend/manage.py shell --command "from agents.orchestrator import run_query; print(run_query('RBI holds repo rate, impact on banking sector'))"
```

or run the provided runner (if any):

```bash
python -m backend.agents.run_synthetic_test
```

**Development tips**

- Agents live in [backend/agents](backend/agents). Key orchestrator entrypoint: [backend/agents/orchestrator.py](backend/agents/orchestrator.py).
- News Scout and retrieval helpers: [backend/fetch_news](backend/fetch_news).
- Fabric IQ helpers: [backend/fintelliops_iq](backend/fintelliops_iq).

**Contributing**

- Fork, create a branch, add tests in the relevant app, run migrations, and open a PR.

**References**

- Architecture and design notes: docs/VERIFICATION.md

---
If you want, I can also generate an Excalidraw export of the diagram or add PNG/SVG assets to `docs/`.

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

**Keshav Dixit** — B.Tech Computer and Communication Engineering, 
**Keshav Rai** - B.Tech Internet Of Things

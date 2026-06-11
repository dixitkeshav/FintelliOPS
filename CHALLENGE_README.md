# Reasoning Agents Challenge — Enterprise Learning Certification

**Track:** Battle #2 — Reasoning Agents with Microsoft Foundry  
**Challenge:** Multi-agent enterprise learning system for internal team certification programmes.

> **Synthetic data only.** This project uses fabricated identifiers (L-1001, EMP-001, TEAM-A) and demo documents. No real PII, customer data, or credentials are included.

## Solution overview

This submission implements a **multi-agent certification learning system** with:

| Component | Implementation |
|-----------|----------------|
| **Learning Path Curator** | Maps certification goals to cited skills via Foundry IQ + Fabric IQ |
| **Study Plan Generator** | Capacity-aware schedules via Fabric IQ + Work IQ |
| **Engagement Agent** | Work-context reminders via Work IQ |
| **Assessment Agent** | Grounded, cited practice questions via Foundry IQ + Fabric IQ |
| **Manager Insights Agent** | Team readiness summaries via Fabric IQ + Work IQ |
| **Work IQ** | Meeting load, focus hours, preferred learning slots (synthetic) |
| **Foundry IQ** | Grounded retrieval from approved synthetic knowledge docs |
| **Fabric IQ** | Semantic model: roles, certifications, skill gaps, readiness |
| **Microsoft Foundry** | Optional cloud LLM via `AZURE_AI_PROJECT_ENDPOINT` |
| **MCP** | Optional Microsoft Learn MCP augmentation |
| **Hosted Agents** | Container deployment pattern in `deploy/hosted-agent/` |

## Architecture

```
Learner request
    │
    ▼
Learning Path Curator ──► Foundry IQ (grounded docs) + Fabric IQ (role/cert semantics)
    │
    ▼
Study Plan Generator ───► Fabric IQ (milestones) + Work IQ (capacity)
    │
    ▼
Engagement Agent ───────► Work IQ (reminder windows)
    │
    ▼
Assessment Agent ───────► Foundry IQ (cited questions) + Fabric IQ (readiness)
    │
    ▼
Manager Insights ───────► Fabric IQ (team metrics) + Work IQ (capacity risks)
    │
    ▼
Next certification step OR loop back to preparation
```

## Quick start

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r ../requirements.txt
cp ../.env.example .env    # optional: GROQ_API_KEY or AZURE_AI_PROJECT_ENDPOINT
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

Open [http://localhost:3000](http://localhost:3000) → **Learning Certification** dashboard.

### API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/learning/health/` | GET | Subsystem health and IQ layer status |
| `/api/learning/learners/` | GET | List synthetic learners |
| `/api/learning/teams/` | GET | List synthetic teams |
| `/api/learning/run/` | POST | Run full multi-agent pipeline |
| `/api/learning/iq/` | GET | Inspect IQ layer sample retrieval |
| `/api/learning/docs/` | GET | List synthetic knowledge documents |

**Example run:**

```bash
curl -X POST http://127.0.0.1:8000/api/learning/run/ \
  -H "Content-Type: application/json" \
  -d '{"learner_id":"L-1001","team":"TEAM-A","topics":["Azure Functions","Exam prep"]}'
```

## Microsoft Foundry configuration

Add to `backend/.env`:

```env
# Option 1 (recommended)
AZURE_AI_PROJECT_ENDPOINT=https://your-project.services.ai.azure.com/api/projects/your-project
AZURE_AI_MODEL_DEPLOYMENT=gpt-4o

# Option 2
# AZURE_SUBSCRIPTION_ID=...
# AZURE_RESOURCE_GROUP=...
# AZURE_AI_PROJECT_NAME=...
```

Without Foundry credentials, agents use **Groq/OpenAI** (if configured) or **rule-based fallbacks**.

## Hosted Agent deployment

See `deploy/hosted-agent/README.md` for the Foundry Agent Service container pattern:

1. Build image → push to Azure Container Registry
2. Deploy as Hosted Agent in Foundry Agent Service
3. Entry agent orchestrates the 5 specialised sub-agents

## Synthetic data locations

- `backend/learning/data/learner_performance.json`
- `backend/learning/data/work_signals.json`
- `backend/learning/data/fabric_semantic_model.json`
- `backend/learning/data/documents/*.md`

## Submission checklist

- [x] Multi-agent system aligned to certification scenario
- [x] Microsoft Foundry SDK integration (with local fallback)
- [x] Reasoning and multi-step decision-making across agents
- [x] All three Microsoft IQ layers integrated
- [x] Synthetic data and documents only
- [x] Demoable UI with pipeline visualization
- [x] Documentation for agents, orchestration, tools, and data sources
- [x] Optional MCP integration hook
- [x] Hosted agent deployment story

## Evaluation alignment

| Criterion | How we address it |
|-----------|-------------------|
| Accuracy & Relevance | Role/cert mapping, grounded citations, readiness thresholds |
| Reasoning & Multi-step | Sequential orchestrator with feedback loop on assessment |
| Creativity | Work-context engagement + semantic skill gap modelling |
| UX & Presentation | Interactive dashboard with pipeline and agent cards |
| Reliability & Safety | Synthetic data guardrails, privacy-conscious manager view |

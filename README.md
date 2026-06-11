# Enterprise Learning Certification — Multi-Agent Showcase

**Microsoft Foundry Reasoning Agents Challenge** submission: a multi-agent enterprise learning system that helps organisations manage internal team certification programmes.

> **Synthetic data only** — fabricated learners (L-1001), employees (EMP-001), and demo documents. No real PII.

## What's included

- **5 specialised agents** orchestrated end-to-end: Learning Path Curator, Study Plan Generator, Engagement, Assessment, Manager Insights
- **3 Microsoft IQ layers**: Work IQ, Foundry IQ, Fabric IQ
- **Synthetic datasets** and approved knowledge documents for grounded retrieval
- **Microsoft Foundry SDK** integration with local LLM fallback
- **Optional MCP** hook for Microsoft Learn documentation
- **Hosted Agent** deployment pattern (`deploy/hosted-agent/`)
- **Next.js dashboard** with pipeline visualization and agent result cards
- **Legacy financial agents** still available at `/dashboard/agents`

See [CHALLENGE_README.md](./CHALLENGE_README.md) for full challenge alignment and evaluation mapping.

## Quick start

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r ../requirements.txt
cp ../.env.example .env     # optional: GROQ_API_KEY or AZURE_AI_PROJECT_ENDPOINT
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

### Run the pipeline

1. Select a synthetic learner (e.g. `L-1001 — Cloud Engineer (AZ-204)`)
2. Choose team and study topics
3. Click **Run Learning Pipeline**
4. View IQ-grounded agent outputs and manager insights

## API endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /api/learning/run/` | Run full certification multi-agent workflow |
| `GET /api/learning/health/` | Health check and IQ layer status |
| `GET /api/learning/learners/` | List synthetic learners |
| `GET /api/learning/iq/` | Sample IQ layer retrieval |

## Environment variables

| Variable | Purpose |
|----------|---------|
| `AZURE_AI_PROJECT_ENDPOINT` | Microsoft Foundry project (optional) |
| `AZURE_AI_MODEL_DEPLOYMENT` | Model deployment name (default: gpt-4o) |
| `GROQ_API_KEY` or `OPENAI_API_KEY` | Local LLM fallback |
| `MCP_LEARN_ENABLED` | Enable Microsoft Learn MCP (optional) |

## Project structure

```
FNSA-Agent-Showcase/
├── backend/learning/          # Challenge implementation
│   ├── agents/                # 5 agents + orchestrator
│   ├── iq/                    # Work IQ, Foundry IQ, Fabric IQ
│   ├── data/                  # Synthetic JSON + documents
│   └── foundry_client.py      # Azure Foundry integration
├── frontend/app/dashboard/learning/   # Certification UI
├── deploy/hosted-agent/       # Container deployment for Foundry
└── CHALLENGE_README.md        # Submission documentation
```

## Security

- Never commit `.env` files or credentials
- Use synthetic data only in demos and evaluations
- Manager insights use aggregated metrics — no sensitive personal data exposed

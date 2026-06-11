# Interview Guide — Agentic GenAI Financial Intelligence Platform (FintelliAI / FNSA)

Use this document as your **single source of truth** for what the codebase actually does, how to explain it in one minute, and how each technology fits. The main technical reference remains the root [`README.md`](./README.md).

---

## 1. Elevator pitch (30–45 seconds)

> “I built a full-stack financial intelligence platform that pulls live market news and prices, runs FinBERT for financial sentiment, layers LLM reasoning through a **multi-agent pipeline**, and exposes quant-style signals with backtesting. The backend is **Django + Django REST Framework** with optional **Redis, Celery, and Django Channels** for caching, async work, and WebSockets. The frontend is **Next.js** with dashboards for news, agents, scanners, options, and backtests. The idea is to fuse **narrative sentiment** with **price context** and **structured evaluation** so decisions are less noisy than using any single signal alone.”

---

## 2. How your prep doc compares to this repo (read before the interview)

Your Section 2.1 narrative is **directionally right** (multi-signal fusion, agents, real-time, FinBERT, Redis/Celery, Django API, Next.js). A few details should be aligned with what you can defend from the code:

| Topic | Prep doc | This repository |
|--------|----------|-----------------|
| Agent count & roles | Three agents (Strategy, Macro ReAct, Risk) | **Five** agents in a **linear pipeline**: News Scout → Macro Context → Market Reaction → Risk → Decision; plus **Symbol Deep-Dive** for single-ticker analysis. **Quant signals** (momentum, MA, etc.) live under `quant/`, not as a separate “Strategy agent” class. |
| How agents talk | Redis pub/sub between agents | Agents share a **Python context dictionary** inside `AgentOrchestrator` (`backend/agents/orchestrator.py`). **Redis** is used for **cache**, **Celery broker/backend**, and optionally **Django Channels’ channel layer** — not as an inter-agent message bus. |
| Macro agent | LangChain ReAct + economic tools | **Macro Context** uses **headline/heuristic linking** to macro themes (rates, CPI, GDP, yields); **LangChain** is used for **LLM prompts/chains** elsewhere (e.g. insights, debate-style synthesis in the Decision path). |
| Voting / weights | ≥2 agents agree; rolling 30-day precision weights | The pipeline is **sequential synthesis**; Risk uses **rules** (spikes, volume, negative share). If asked, say the **design goal** is multi-signal agreement; the **implemented** version is orchestrated steps + optional LLM synthesis — do not claim rolling precision weights unless you add them. |
| Impact numbers (~25% noise, 20% accuracy, 500+ points/min) | Strong story | Only cite if you can show **methodology, dataset, and how you measured** them. The repo includes **evaluation endpoints** (e.g. sentiment accuracy, latency); treat hard percentages as **hypotheses or offline experiments**, not production guarantees, unless you have written results. |

**Safe phrasing if pressed:** “The production path is an orchestrated multi-agent pipeline with shared context; Redis backs caching, Celery, and WebSockets. A pub/sub bus between agents would be a natural scale-out step for independent services.”

---

## 3. Corrected project description (Section 2.1 style)

**The problem**  
Financial decisions mix **fast price information**, **slow qualitative news**, and **slow-moving macro structure**. Many tools optimize one of these. This platform is built to **combine** sentiment from news, LLM reasoning, agent-level risk framing, and **quant-style signals** with **backtesting and evaluation** so you can reason about usefulness, not just display a score.

**Architecture**  
- **Ingestion:** News from external APIs (e.g. Alpha Vantage, Finnhub); prices and market data via APIs and (where configured) broker/ticker flows.  
- **NLP:** FinBERT (Transformers / PyTorch) for financial sentiment.  
- **GenAI:** Groq or OpenAI-compatible models via LangChain-style chaining for insights and agent summaries.  
- **Agents:** Five-step pipeline (news → macro themes → market reaction narrative → risk flags → decision synthesis).  
- **Quant:** Separate modules for signals and backtests (e.g. Sharpe, IC).  
- **Serving:** Django REST API; optional **ASGI + Daphne** for HTTP + WebSockets; Next.js dashboard consuming REST and WebSocket updates.  
- **Async & scale:** Celery for background tasks; Redis for cache and Celery broker when enabled.

**Your contributions (solo project framing)**  
End-to-end ownership: data ingestion, model integration, agent design, API surface, real-time channel, frontend UX, and evaluation hooks.

**Challenges (honest, interview-ready)**  
- **Look-ahead bias** in any backtest or “prediction” narrative — align train/label time with decision time; document assumptions.  
- **API rate limits and cost** — Redis TTL caching and async ingestion.  
- **Model latency** — Celery for offloading heavy FinBERT work; evaluation endpoint for latency awareness.  
- **Operational complexity** — feature flags so Redis/Celery/WebSockets can be disabled for simpler dev.

**Impact**  
Describe **qualitatively** (“fewer contradictory headlines turned into a single narrative + risk view”) and **quantitatively** only with **clear measurement** (benchmark scripts, held-out labels, load-test logs).

---

## 4. End-to-end flow (how to walk a whiteboard)

1. **User opens Next.js dashboard** → calls Django REST endpoints (news, sentiment, agents, quant, backtest).  
2. **News path** → APIs → optional cache (Redis) → store/serve articles → **FinBERT** labels sentiment.  
3. **GenAI path** → LangChain-style LLM calls enrich or summarize.  
4. **Agents** → `AgentOrchestrator.run()` fills `context` step by step; each agent reads prior outputs.  
5. **Quant** → time series of sentiment + price-derived logic → signals; **backtest** module measures risk-adjusted stats.  
6. **Real-time** → Django Channels consumer groups; clients subscribe to `ws/dashboard/` for pushes when wired.  
7. **Optional edge persistence** → Prisma + **PostgreSQL** for candles/signals/settings when `DATABASE_URL` is set (see `frontend/prisma/schema.prisma`).

---

## 5. Likely interview Q&A (short answers)

**Q: How do agents communicate?**  
**A:** In-process orchestration: a shared **context** object passed through a fixed pipeline. Redis is not used as agent-to-agent pub/sub in this codebase.

**Q: Why Django and also Next.js?**  
**A:** Django is strong for **ORM, admin, REST, and Channels** in one place. Next.js gives a **modern SPA**, routing, and API routes for edge concerns (auth, broker callbacks) while proxying to Django for core analytics.

**Q: Where does FinBERT run?**  
**A:** Backend inference (Transformers + PyTorch), typically triggered from analysis views/tasks — not in the browser.

**Q: How do you reduce a “noisy” LLM?**  
**A:** Combine **FinBERT** (supervised financial sentiment) with **structured agent outputs**, **rule-based risk flags**, and **quant evaluation** (IC, backtest) rather than trusting a single free-form answer.

---

## 6. Skills & technologies — definition and use (general + in this project)

Below: **Definition** = what it is; **Use case** = typical purpose; **Here** = how it appears in this repo (if it does).

### Languages

| Skill | Definition | Use case | Here |
|-------|------------|----------|------|
| **Python** | General-purpose language with strong data/ML ecosystem. | APIs, ML, scripting, automation. | Primary backend language (Django, agents, quant, FinBERT). |
| **NumPy** | N-dimensional arrays and fast vectorized math. | Numeric kernels, feature prep, array ops. | Underpins Pandas and scientific stack in quant/evaluation. |
| **Pandas** | Tabular data structures (`DataFrame`) and time-series tools. | Cleaning data, rolling windows, signals on series. | Sentiment series, rolling momentum/MA in `quant/signals.py`. |
| **Java (OOP)** | Statically typed OOP language on JVM. | Large enterprise services, Android, performance-sensitive backends. | Not this repo’s stack; fair as **other coursework/work** skill. |
| **C++** | Systems language: manual memory, high performance. | Games, engines, low-latency trading infra, embedded. | Not this repo; cite if you have **algo/performance** projects elsewhere. |
| **JavaScript** | Dynamic language of the browser; also Node tooling. | UI logic, bundlers, small scripts. | Next.js runtime and client components use JS/TS. |
| **TypeScript** | JavaScript with static types. | Safer large frontends, better IDE support. | Main frontend language in `frontend/`. |

### Backend

| Skill | Definition | Use case | Here |
|-------|------------|----------|------|
| **Django** | Batteries-included Python web framework (ORM, auth, admin). | Full web apps and internal tools quickly. | Core backend app, routing, models (e.g. SQLite for news). |
| **Django REST Framework (DRF)** | Toolkit on top of Django for REST APIs. | Serializers, browsable API, permissions. | JSON APIs for news, agents, quant, evaluation. |
| **FastAPI** | Modern async Python API framework (OpenAPI-first). | High-throughput microservices, ML model servers. | Not in this repo’s `requirements.txt`; OK as **adjacent** skill if true elsewhere. |
| **REST API design** | Resource-oriented HTTP (verbs, status codes, pagination, versioning). | Client/server contracts, integrations. | Frontend `apiClient` ↔ Django views/routers. |
| **WebSockets** | Full-duplex persistent TCP channel over HTTP upgrade. | Live prices, chat, collaborative dashboards. | `ws/dashboard/` via Django Channels consumer. |

### Frontend

| Skill | Definition | Use case | Here |
|-------|------------|----------|------|
| **React** | Component-based UI library. | Interactive dashboards, reusable UI. | Next.js app router pages and components. |
| **Next.js** | React framework: routing, SSR/SSG, API routes. | Production web apps with SEO and server logic. | `frontend/` dashboard, markets, agents, backtest pages. |
| **HTML / CSS** | Structure + presentation of web pages. | Layout, accessibility, branding. | JSX + Tailwind (utility CSS) in components. |
| **Responsive design** | UI adapts to screen size. | Mobile + desktop usability. | Dashboard layout, sidebar, charts. |
| **REST API integration** | Client calls HTTP endpoints, handles errors/loading. | Decoupled UI from backend. | `lib/apiClient.ts`, React Query patterns. |

### Databases

| Skill | Definition | Use case | Here |
|-------|------------|----------|------|
| **PostgreSQL** | Advanced open-source relational DB. | Durable transactional data, analytics. | Prisma `provider = "postgresql"` for edge models (candles, signals, settings). |
| **MySQL** | Popular relational DB (different dialect/features from Postgres). | Web apps, LAMP stacks, hosting defaults. | Not configured here; fine as **general** DB skill. |
| **Relational schema design** | Tables, keys, normalization, indexes. | Consistency, query performance. | Django models + Prisma schema with indexes/uniques. |
| **SQLite** | File-based embedded SQL engine. | Dev/small deployments, zero-ops DB. | Django default `db.sqlite3` for core app data. |
| **Query optimization** | Indexes, explain plans, avoiding N+1. | Latency and cost at scale. | Indexes on Prisma models; Django ORM patterns in views. |

### Systems & tools

| Skill | Definition | Use case | Here |
|-------|------------|----------|------|
| **Docker** | Pack apps + dependencies into images. | Reproducible deploys, CI. | `docker-compose.edge.yml` for optional services. |
| **Redis** | In-memory data store: cache, pub/sub, queues. | Speed, rate-limit buffers, Celery broker. | Django cache, Celery broker/backend, optional Channels layer. |
| **Celery** | Distributed task queue for Python. | Long jobs off the request thread. | `config/celery.py`, `pipelines/tasks.py`. |
| **Git** | Version control. | Collaboration, history, rollback. | Project source control. |
| **Linux** | Server-grade OS family. | Cloud VMs, containers, dev parity. | Typical deployment target for Django + Redis + Daphne. |

### AI / ML

| Skill | Definition | Use case | Here |
|-------|------------|----------|------|
| **FinBERT** | BERT-family model fine-tuned on financial text. | Sentiment/classification for headlines and filings. | `fetch_news/sentiment.py` and analysis endpoints. |
| **Transformers (Hugging Face)** | Library for pretrained transformer models. | Load FinBERT, tokenize, infer. | `requirements.txt` transformers stack. |
| **PyTorch** | Deep learning framework (tensors, autograd, deployment). | Training and inference for neural models. | Backend dependency for model execution. |
| **LangChain** | Framework to compose LLM calls, tools, parsers. | Prompt templates, chains, swapping providers. | `intelligence/` LLM integration (see root README Q&A). |
| **Feature engineering** | Build inputs models consume (lags, rolling stats, encodings). | Improve signal quality. | Rolling sentiment, MA crossover signals in `quant/`. |
| **Model evaluation** | Metrics beyond accuracy: F1, latency, IC, Sharpe. | Know if the signal is real. | Evaluation views; backtest metrics in `quant/backtest.py`. |

### Cloud experience

| Skill | Definition | Use case | Here |
|-------|------------|----------|------|
| **AWS (EC2, S3)** | EC2: VMs; S3: object storage. | Host Django, store artifacts, static assets. | Typical deployment pattern; not hard-coded in repo — describe **your** deploy if asked. |
| **GCP basics** | Google Cloud VMs, storage, IAM, etc. | Same as AWS at high level. | Optional; only mention with real experience. |
| **Cloud deployment workflows** | CI/CD, env vars, secrets, health checks. | Safe releases. | Align with Docker + env files (`.env`, `.env.example`). |

---

## 7. One-page “what I did” checklist

- [ ] **Problem:** fused news sentiment + LLM reasoning + quant + evaluation.  
- [ ] **Architecture:** Django REST + optional Redis/Celery/Channels + Next.js.  
- [ ] **Agents:** five-step orchestrator + Symbol Deep-Dive; quant separate.  
- [ ] **Honest differentiator:** FinBERT + structured agents + backtest/eval, not only chat.  
- [ ] **Trade-offs:** SQLite dev vs Postgres for edge; feature flags for optional infra.  
- [ ] **Metrics:** only claim numbers you can reproduce.

Good luck with the interview.

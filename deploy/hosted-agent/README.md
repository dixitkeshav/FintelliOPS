# Hosted Agent Deployment (Foundry Agent Service)

This folder documents the **recommended production deployment pattern** for the enterprise learning certification multi-agent system.

## Architecture

```
┌─────────────────────────────────────────┐
│  Foundry Agent Service (Hosted Agent)   │
│  Entry: LearningOrchestrator            │
│  ├── Learning Path Curator              │
│  ├── Study Plan Generator               │
│  ├── Engagement Agent                   │
│  ├── Assessment Agent                   │
│  └── Manager Insights                   │
└──────────────┬──────────────────────────┘
               │
    ┌──────────┼──────────┐
    ▼          ▼          ▼
 Foundry IQ  Fabric IQ  Work IQ
 (knowledge) (semantic) (work context)
```

## Steps

### 1. Build container

```bash
docker build -f deploy/hosted-agent/Dockerfile -t learning-orchestrator:latest .
```

### 2. Push to Azure Container Registry

```bash
az acr login --name <your-acr>
docker tag learning-orchestrator:latest <your-acr>.azurecr.io/learning-orchestrator:v1
docker push <your-acr>.azurecr.io/learning-orchestrator:v1
```

### 3. Configure environment (Key Vault / managed identity)

- `AZURE_AI_PROJECT_ENDPOINT`
- `AZURE_AI_MODEL_DEPLOYMENT`
- Do **not** bake secrets into the image

### 4. Deploy in Foundry Agent Service

Use the Foundry portal or SDK to create a Hosted Agent pointing at your ACR image. The container exposes port 8080 with a health endpoint at `/health`.

### 5. Observability

- Enable Foundry telemetry and trace logs
- Run evaluation test cases from `backend/learning/data/learner_performance.json`

## Local smoke test

```bash
docker run -p 8080:8080 -e GROQ_API_KEY=$GROQ_API_KEY learning-orchestrator:latest
curl http://localhost:8080/health
curl -X POST http://localhost:8080/run -H "Content-Type: application/json" \
  -d '{"learner_id":"L-1001","team":"TEAM-A"}'
```

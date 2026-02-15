
# Cyndx LangGraph API

A production-grade RESTful API wrapping a **LangGraph** conversational AI agent, deployed on **Google Cloud Run** with full **Terraform** infrastructure-as-code and **GitHub Actions** CI/CD.

Supports **4 LLM providers** (OpenAI, Anthropic, Google Gemini, Groq), **3 tool integrations** (web search, calculator, datetime), **SSE streaming**, and enterprise-grade observability.

---

##  Reviewer Quick Start

> **Live API**: `https://YOUR_DEPLOYED_URL` (active for 48 hours post-submission)
> **Swagger Docs**: `https://YOUR_DEPLOYED_URL/docs`

### Option 1: Use the Live API (no setup needed)

```bash
# Health check
curl https://YOUR_DEPLOYED_URL/health | jq

# Create session & chat (uses server's default LLM key)
curl -X POST https://YOUR_DEPLOYED_URL/sessions -H "Content-Type: application/json" -d '{}' | jq
```

### Option 1b: Use the Live API With YOUR OWN API Key

You can bring your own LLM key — just pass it when creating a session:

```bash
# Use your own OpenAI key
curl -X POST https://YOUR_DEPLOYED_URL/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "agent_config": {
      "model": "gpt-4o-mini",
      "llm_api_key": "sk-your-own-openai-key"
    }
  }' | jq

# Use your own Anthropic key
curl -X POST https://YOUR_DEPLOYED_URL/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "agent_config": {
      "model": "claude-3-5-haiku-20241022",
      "llm_api_key": "sk-ant-your-own-key"
    }
  }' | jq

# Use your own Groq key (free at https://console.groq.com)
curl -X POST https://YOUR_DEPLOYED_URL/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "agent_config": {
      "model": "llama-3.1-8b-instant",
      "llm_api_key": "gsk_your-own-key"
    }
  }' | jq
```

The key is only used for that session and is not stored anywhere.

See [CURL_CHEATSHEET.md](CURL_CHEATSHEET.md) for all example requests.

### Option 2: Run Locally With Your Own API Keys

```bash
git clone https://github.com/YOUR_USERNAME/cyndx-langgraph-api.git
cd cyndx-langgraph-api

# 1. Create .env and add YOUR keys (at least one LLM provider required)
cp .env.example .env
# Edit .env:
#   OPENAI_API_KEY=sk-...        ← any one of these four
#   ANTHROPIC_API_KEY=sk-ant-... ← is enough to run
#   GOOGLE_API_KEY=AI...         ← the application
#   GROQ_API_KEY=gsk_...         ← (Groq is free)
#   TAVILY_API_KEY=tvly-...      ← optional, enables web search tool

# 2. Install & run
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8080

# 3. Open Swagger UI
open http://localhost:8080/docs
```

### Option 3: Run With Docker

```bash
cp .env.example .env
# Edit .env with your keys
docker-compose up --build
```

### Option 4: Deploy to Your Own GCP Project

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars: project_id, region

terraform init
terraform apply \
  -var="openai_api_key=sk-YOUR_KEY" \
  -var="tavily_api_key=tvly-YOUR_KEY"
```

> **Note**: No API keys are stored in this repository. All secrets are provided via `.env` (local) or Secret Manager (cloud). See `.env.example` for the full list of configurable variables.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT                                       │
│              Postman / curl / Swagger UI (/docs)                     │
└───────────────────────────┬─────────────────────────────────────────┘
                            │ HTTPS
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    GCP CLOUD RUN                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  FastAPI Application                                          │  │
│  │  Middleware: Request ID → Rate Limiter → API Key Auth → Logger│  │
│  │                                                               │  │
│  │  ┌─────────────────────────────────────────────────────────┐  │  │
│  │  │  LangGraph Agent (4-Node Graph)                         │  │  │
│  │  │                                                         │  │  │
│  │  │  START → [Router] ──→ [Tool Executor] ──→ [Synthesizer] │  │  │
│  │  │              │              ▲                    │       │  │  │
│  │  │              │              │              [Quality Gate] │  │  │
│  │  │              │              └──── loop back ─────┘       │  │  │
│  │  │              └──── general_chat ──→ [Synthesizer]        │  │  │
│  │  └─────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────┘  │
└────────┬──────────┬──────────┬──────────┬──────────┬───────────────┘
         │          │          │          │          │
         ▼          ▼          ▼          ▼          ▼
   ┌──────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌──────────┐
   │ LLM      │ │ Tools  │ │ Secret │ │ Cloud  │ │ Cloud    │
   │ Provider │ │ Tavily │ │ Manager│ │Logging │ │Monitoring│
   │ OpenAI / │ │ Calc   │ │ API    │ │ JSON   │ │ Metrics  │
   │ Anthropic│ │ DateTime│ │ Keys   │ │ Logs   │ │ Alerts   │
   │ Gemini / │ │        │ │        │ │        │ │          │
   │ Groq     │ │        │ │        │ │        │ │          │
   └──────────┘ └────────┘ └────────┘ └────────┘ └──────────┘
```

### LangGraph Agent Graph

```
START
  │
  ▼
[Node 1: Intent Router]  ← Classifies: general_chat | research | analysis | tool_required
  │
  ├── general_chat ────────────────────────┐
  │                                        │
  ▼                                        ▼
[Node 2: Tool Executor]              [Node 3: Synthesizer]
  │  Tavily Search, Calculator,            │
  │  DateTime tools via LLM tool calling   │
  │                                        │
  └────────→ [Node 3: Synthesizer] ────────┘
                    │
                    ▼
             [Node 4: Quality Gate]
                    │
              ┌─────┴─────┐
              │            │
         needs_more    sufficient
         (max 3)          │
              │            ▼
              └──→ Tool    END
                  Executor
```

---

## Quick Start — Local Development

### Prerequisites

- Python 3.11+
- At least one LLM API key (Groq is free: https://console.groq.com/keys)

### Setup

```bash
# Clone
git clone https://github.com/YOUR_USERNAME/cyndx-langgraph-api.git
cd cyndx-langgraph-api

# Create .env
cp .env.example .env
# Edit .env — add your API key(s):
#   GROQ_API_KEY=gsk_...
#   DEFAULT_MODEL=llama-3.1-8b-instant

# Install
pip install -e ".[dev]"

# Run
uvicorn app.main:app --reload --port 8080
```

### With Docker

```bash
cp .env.example .env
# Edit .env with your keys
docker-compose up --build
```

The API is available at http://localhost:8080 and Swagger docs at http://localhost:8080/docs.

---

## API Reference

### Endpoints

| Method | Endpoint | Description | Status |
|--------|----------|-------------|--------|
| `POST` | `/sessions` | Create conversation session | 201 |
| `POST` | `/sessions/{id}/messages` | Send message to agent | 200 |
| `POST` | `/sessions/{id}/messages/stream` | SSE streaming response | 200 |
| `GET` | `/sessions/{id}/history` | Get conversation history | 200 |
| `DELETE` | `/sessions/{id}` | Terminate session | 200 |
| `GET` | `/health` | Health check | 200 |

### Example Requests

**Create Session:**
```bash
curl -X POST http://localhost:8080/sessions \
  -H "Content-Type: application/json" \
  -d '{"agent_config": {"model": "llama-3.1-8b-instant", "temperature": 0.7}}'
```

Response:
```json
{
  "session_id": "sess_a1b2c3d4e5f6",
  "created_at": "2025-02-13T14:30:00Z",
  "status": "active",
  "agent_config": { "model": "llama-3.1-8b-instant", "temperature": 0.7 }
}
```

**Send Message:**
```bash
curl -X POST http://localhost:8080/sessions/sess_a1b2c3d4e5f6/messages \
  -H "Content-Type: application/json" \
  -d '{"content": "What companies were acquired in the fintech space in 2024?"}'
```

Response:
```json
{
  "message_id": "msg_x9y8z7w6",
  "session_id": "sess_a1b2c3d4e5f6",
  "role": "assistant",
  "content": "Based on my research, several notable fintech acquisitions...",
  "tool_calls": [
    {
      "tool_name": "web_search",
      "input": { "query": "fintech acquisitions 2024" },
      "output_summary": "Found 3 relevant results..."
    }
  ],
  "usage": {
    "prompt_tokens": 342,
    "completion_tokens": 587,
    "total_tokens": 929,
    "llm_calls": 3
  },
  "latency_ms": 3420.15,
  "created_at": "2025-02-13T14:30:15Z"
}
```

**Get History:**
```bash
curl http://localhost:8080/sessions/sess_a1b2c3d4e5f6/history
```

**Delete Session:**
```bash
curl -X DELETE http://localhost:8080/sessions/sess_a1b2c3d4e5f6
```

**Health Check:**
```bash
curl http://localhost:8080/health
```

### Error Response Format

All errors follow a consistent structure:
```json
{
  "error": {
    "code": "SESSION_NOT_FOUND",
    "message": "No active session found with ID 'sess_invalid'.",
    "details": {},
    "request_id": "req_abc123"
  }
}
```

| Status | Code | When |
|--------|------|------|
| 400 | `INVALID_REQUEST` | Malformed request |
| 401 | `UNAUTHORIZED` | Missing/invalid API key |
| 404 | `SESSION_NOT_FOUND` | Session doesn't exist |
| 422 | `VALIDATION_ERROR` | Pydantic validation failure |
| 429 | `RATE_LIMITED` | Too many requests |
| 500 | `INTERNAL_ERROR` | Unexpected error |
| 503 | `SERVICE_UNAVAILABLE` | LLM provider down |

### Supported LLM Models

Create a session with any of these providers:

| Provider | Example Model | Env Variable |
|----------|--------------|--------------|
| OpenAI | `gpt-4o-mini` | `OPENAI_API_KEY` |
| Anthropic | `claude-3-5-haiku-20241022` | `ANTHROPIC_API_KEY` |
| Google | `gemini-2.0-flash` | `GOOGLE_API_KEY` |
| Groq | `llama-3.1-8b-instant` | `GROQ_API_KEY` |

---

## Running Tests

```bash
# Unit tests (no API keys needed — uses mocked agent)
pytest tests/ -v

# With coverage
pytest tests/ -v --cov=app

# Load testing
locust -f load_tests/locustfile.py --host http://localhost:8080
```

---

## Deployment Guide

### Prerequisites

- GCP account with billing enabled
- `gcloud` CLI installed
- `terraform` >= 1.5 installed

### Step 1: GCP Project Setup

```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
```

### Step 2: Terraform Deploy

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your project_id, region, github_repo

terraform init
terraform plan -var="groq_api_key=gsk_YOUR_KEY"
terraform apply -var="groq_api_key=gsk_YOUR_KEY"
```

### Step 3: Build & Push Docker Image

```bash
cd ..
REGISTRY=$(cd terraform && terraform output -raw registry_url)
gcloud auth configure-docker us-central1-docker.pkg.dev
docker build -t $REGISTRY/cyndx-langgraph-api:latest .
docker push $REGISTRY/cyndx-langgraph-api:latest
```

### Step 4: Deploy to Cloud Run

```bash
cd terraform
terraform apply -var="groq_api_key=gsk_YOUR_KEY" -var="image_tag=latest"
echo "Live URL: $(terraform output -raw service_url)"
echo "Swagger:  $(terraform output -raw swagger_url)"
```

### Step 5: Setup CI/CD (GitHub Actions)

Add these GitHub repository secrets:

| Secret | Value (from terraform output) |
|--------|-------------------------------|
| `GCP_PROJECT_ID` | Your GCP project ID |
| `GCP_REGION` | `us-central1` |
| `WIF_PROVIDER` | `terraform output -raw wif_provider` |
| `GCP_SA_EMAIL` | `terraform output -raw cicd_sa_email` |

After setup, every PR runs lint → test → build → terraform plan, and every merge to main auto-deploys.

---

## Infrastructure

### GCP Resources (Terraform)

| Resource | Purpose |
|----------|---------|
| Cloud Run | Serverless compute (auto-scaling 0→10) |
| Artifact Registry | Docker image storage |
| Secret Manager | Secure API key storage |
| Cloud Logging | Structured JSON logs |
| Cloud Monitoring | Custom metrics + alert policies |
| IAM Service Accounts | Least-privilege access |
| Workload Identity Federation | Keyless GitHub Actions auth |

### IAM — Least Privilege

**API Service Account** (3 roles only):
- `roles/secretmanager.secretAccessor` — read API keys
- `roles/logging.logWriter` — write structured logs
- `roles/monitoring.metricWriter` — push custom metrics

**CI/CD Service Account** (4 roles only):
- `roles/run.developer` — deploy Cloud Run
- `roles/artifactregistry.writer` — push Docker images
- `roles/iam.serviceAccountUser` — act as API SA during deploy
- `roles/secretmanager.admin` — manage secrets via Terraform

No `roles/editor`, `roles/owner`, or wildcard `*` policies.

### Custom Metrics

| Metric | Type | Purpose |
|--------|------|---------|
| `request_latency_ms` | Histogram | P50/P95/P99 per endpoint |
| `llm_token_usage` | Counter | Token cost monitoring |
| `active_sessions` | Gauge | Current session count |
| `tool_call_duration_ms` | Histogram | Tool execution time |

### Alert Policies

- **Error rate > 5%** over 5-minute window
- **P99 latency > 10s** sustained

---

## Design Decisions

### Why LangGraph with 4 Nodes?

A simple LLM passthrough would just forward prompts and return responses. The 4-node architecture demonstrates genuine multi-step reasoning: the **Router** classifies intent to avoid unnecessary tool calls for simple chat, the **Tool Executor** handles real external API calls, the **Synthesizer** produces coherent responses from tool results, and the **Quality Gate** enables iterative research loops (capped at 3 to prevent runaway costs).

### Why Multi-LLM Support?

A factory pattern with model-prefix detection (`gpt-` → OpenAI, `claude-` → Anthropic, etc.) lets users switch providers per-session without code changes. This demonstrates understanding of LLM abstraction patterns and avoids vendor lock-in.

### Why Cloud Run over ECS Fargate?

Cloud Run provides a public HTTPS URL with zero networking configuration (no VPC, ALB, security groups). The Terraform is ~50 lines vs. ~200+ for ECS. For a demo service that needs to be publicly accessible for 48 hours, this simplicity is a significant advantage.

### Why Workload Identity Federation?

Static service account JSON keys are a security anti-pattern. WIF lets GitHub Actions authenticate to GCP via OIDC — no long-lived credentials stored anywhere. This is Google's recommended approach.

### Why MemorySaver for Checkpointing?

For the assessment scope, in-memory checkpointing is sufficient and avoids external database dependencies. In production, this would be swapped for `PostgresSaver` or a Firestore-backed checkpointer via a one-line change in `graph.py`.

### Why Lazy Tool Initialization?

The Tavily search tool validates its API key on instantiation. Lazy loading (only initializing on first actual tool call) means the app starts and tests run without requiring all API keys upfront.

---

## Trade-offs & Limitations

### What I'd Do Differently With More Time

- **PostgreSQL checkpointing** — MemorySaver loses state on restart. A Postgres-backed checkpointer would enable true persistence across deploys.
- **Terraform remote state** — Currently uses local state. Production should use GCS backend with state locking.
- **Multi-environment** — Terraform workspaces or separate tfvars for staging vs. production.
- **Comprehensive integration tests** — Current tests mock the agent. Full integration tests with a cheap LLM (Groq) would catch more edge cases.
- **Response caching** — Frequently asked questions could be cached to reduce LLM costs and latency.

### Known Limitations

- **In-memory state** — Sessions are lost on restart/redeploy. Acceptable for assessment but not production.
- **Single instance state** — MemorySaver doesn't share state across Cloud Run instances. With `max_instances > 1`, a user could hit different instances. Fix: external checkpointer.
- **No authentication on live demo** — Public access is enabled for reviewer testing. Production would require API key auth (already implemented but disabled by default).
- **Tool error handling** — If Tavily is down, the agent falls back to LLM knowledge but doesn't explicitly tell the user the tool failed.

---

## Cost Estimation

| Traffic | Cloud Run | Secret Manager | Logging | Monitoring | Total |
|---------|-----------|----------------|---------|------------|-------|
| ~100 req/day | ~$0 (free tier) | ~$0.06 | ~$0 | ~$0 | **~$1-2/mo** |
| ~5K req/day | ~$15-25 | ~$3 | ~$5 | ~$5 | **~$28-38/mo** |
| ~50K req/day | ~$150-250 | ~$15 | ~$30 | ~$20 | **~$215-315/mo** |

*Excludes LLM API costs which scale linearly with usage.*

---

## Repository Structure

```
cyndx-langgraph-api/
├── .github/workflows/        # CI/CD pipelines
│   ├── ci.yml                # PR: lint → test → build → plan
│   └── cd.yml                # Merge: build → push → apply → smoke test
├── app/                      # Application source code
│   ├── main.py               # FastAPI app factory
│   ├── config.py             # Pydantic Settings
│   ├── agent/                # LangGraph agent
│   │   ├── graph.py          # Graph definition & wiring
│   │   ├── state.py          # AgentState TypedDict
│   │   ├── providers.py      # Multi-LLM factory
│   │   ├── nodes/            # 4 graph nodes
│   │   └── tools/            # Tool integrations
│   ├── api/                  # API layer
│   │   ├── routes/           # Endpoint handlers
│   │   ├── schemas/          # Pydantic models
│   │   └── middleware/       # Request ID, rate limiter, auth, logging
│   ├── services/             # Business logic
│   └── core/                 # Exceptions, logging config
├── terraform/                # Infrastructure-as-code
├── tests/                    # Unit tests (pytest)
├── load_tests/               # Locust load test
├── Dockerfile                # Multi-stage, non-root
├── docker-compose.yml        # Local dev
├── .env.example              # Documented env vars
└── pyproject.toml            # Dependencies
```

---

## Bonus Features Implemented

- ✅ **SSE Streaming** — `POST /sessions/{id}/messages/stream` for real-time token streaming
- ✅ **Rate Limiting** — Per-IP/API-key token bucket via slowapi
- ✅ **API Key Auth** — Optional `X-API-Key` header validation
- ✅ **OpenTelemetry Metrics** — 4 custom metrics exported to Cloud Monitoring
- ✅ **Cost Estimation** — See table above
- ✅ **Load Testing** — Locust script with multi-turn conversation scenarios
- ✅ **Alerting** — Error rate and P99 latency alert policies in Terraform
>>>>>>> b23e0c7 (Initial commit: LangGraph API with Cloud Run deployment)

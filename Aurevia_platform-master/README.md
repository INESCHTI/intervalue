# Aurevia - Agentic Wealth Intelligence

A production-grade AI platform for private banking / wealth management built as a fleet of specialist AI agents communicating over the **A2A protocol**, orchestrated by **LangGraph**, and secured by **Keycloak PKCE**.

A conversational private-banking assistant covering AUM queries, TWR, IRR, Sharpe ratio, geographic/sector breakdowns, document RAG, email actions, and a voice callbot.

---

## Architecture

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                      Traefik Gateway                        â”‚
â”‚         JWT forward-auth â†’ /api/* (orchestrator)           â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                         â”‚
              â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
              â”‚   LangGraph         â”‚
              â”‚   Orchestrator :8000â”‚
              â”‚   (supervisor graph)â”‚
              â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                     â”‚  A2A HTTP/JSON fan-out
        â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
        â–¼            â–¼            â–¼               â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚Financial â”‚  â”‚ Market   â”‚  â”‚  Docs    â”‚  â”‚  Action  â”‚
â”‚ Agent    â”‚  â”‚ Agent    â”‚  â”‚  Agent   â”‚  â”‚  Agent   â”‚
â”‚  :8001   â”‚  â”‚  :8002   â”‚  â”‚  :8003   â”‚  â”‚  :8004   â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
        â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
        â”‚  QA      â”‚  â”‚  Voice   â”‚
        â”‚ Agent    â”‚  â”‚ Callbot  â”‚
        â”‚  :8005   â”‚  â”‚  :8006   â”‚
        â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

### Tech Stack

| Layer | Technology |
|-------|-----------|
| LLM | Qwen2.5:3b via Ollama (local, RTX 2050) |
| Orchestration | LangGraph supervisor graph, SSE streaming |
| Agent protocol | A2A (HTTP/JSON task envelopes) |
| Tool protocol | MCP (Model Context Protocol) base classes |
| Auth | Keycloak 24 â€” PKCE for web/mobile, bearer for backend |
| Gateway | Traefik v3 â€” forward-auth middleware |
| Database | PostgreSQL 16 + SQLAlchemy async + Alembic |
| Cache | Redis 7 |
| Vector store | Qdrant |
| Tracing | Langfuse (spans per agent call) |
| Eval | MLflow + LLM-as-judge golden dataset |
| Voice | faster-whisper STT + Piper TTS |
| Email | MailHog (dev SMTP sandbox) |
| Web frontend | React + Vite + Tailwind CSS |
| Mobile | React Native / Expo |
| Container | Docker Compose (dev) / Kubernetes + Helm (prod) |
| Python tooling | uv workspace, ruff, mypy, pytest-asyncio |

---

## Services

| Service | Port | Description |
|---------|------|-------------|
| orchestrator | 8000 | LangGraph supervisor + auth/verify + GDPR endpoints |
| agent-financial | 8001 | AUM, TWR, IRR, Sharpe, geo/sector breakdowns |
| agent-market | 8002 | Market quotes, economic indicators |
| agent-docs | 8003 | Chunking, Ollama embeddings, and Qdrant semantic search |
| agent-action | 8004 | Report generation, email (MailHog), WhatsApp stub |
| agent-qa | 8005 | AI-SDLC: LLM-generated pytest tests + sandboxed runner |
| voice | 8006 | STT (faster-whisper) + TTS (Piper) + voice-to-voice |

---

## Quick Start

### Prerequisites

- Python 3.12+ and [uv](https://docs.astral.sh/uv/)
- Docker Desktop
- [Ollama](https://ollama.ai/) running on host

```bash
# Pull the LLM
ollama pull qwen2.5:3b
ollama pull nomic-embed-text

# Install Python dependencies
uv sync

# Start all infrastructure + services
docker compose -f docker-compose.dev.yml up -d

# Run tests
uv run pytest services/ libs/ -q
```

### Document RAG

The docs agent chunks document text, embeds it with `nomic-embed-text`, and stores the
vectors and source payloads in Qdrant. In local development, start Qdrant and point the
host-run agent at it:

```bash
docker compose -f docker-compose.dev.yml up -d qdrant
QDRANT_URL=http://localhost:6333 uv run uvicorn agent_docs.main:app --port 8003
```

If Qdrant or Ollama is unavailable, ingestion and search continue with the in-memory
lexical fallback.

### Authentication

Two modes, controlled by environment:

- **Dev bypass (default, no Keycloak):** when `KEYCLOAK_URL` is unset, `get_current_user()` returns a hardcoded dev advisor context so all endpoints work immediately. The web app uses `VITE_DEV_AUTH=true`.
- **Real Keycloak (login-only, no self-registration):** RS256 JWTs are verified against the realm JWKS, expected issuer, and an allowed `azp` client (`web,mobile,backend` by default; override with `KEYCLOAK_ALLOWED_CLIENTS`). Pre-seeded users: `advisor@aurevia.local / advisor123` and `client@aurevia.local / client123`. The client login maps to its portfolio via a fixed `keycloak_id`.

Turn it on:

```bash
# 1. Start identity + db
docker compose -f docker-compose.dev.yml up -d postgres keycloak   # realm auto-imported

# 2. Start the backend with Keycloak enabled
KEYCLOAK_URL=http://localhost:8180 uv run uvicorn orchestrator.main:app --port 8000

# 3. Build/run the web app with real login (uses frontend/.env.production)
cd frontend && npm run build && npm run preview
```

JWT enforcement is covered by `libs/agentkit/tests/test_auth_jwt.py` (valid token â†’ 200, missing/tampered â†’ 401) â€” no Keycloak server required to run those tests.

---

## API Examples

```bash
# Chat (SSE stream)
curl -N http://localhost:8000/api/chat \
  -H "Authorization: Bearer dev-token" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is my portfolio AUM?"}'

# GDPR delete-my-data
curl -X DELETE http://localhost:8000/api/gdpr/delete-my-data \
  -H "Authorization: Bearer dev-token"

# Direct A2A call to financial agent
curl http://localhost:8001/a2a/tasks/send \
  -H "Content-Type: application/json" \
  -d '{"task_id":"t1","messages":[{"role":"user","content":"Show sector breakdown"}]}'
```

---

## Demo

Reproduces a full private-banking conversation (9 turns: AUM â†’ TWR â†’ geography â†’ deals â†’ S&P â†’ Fed rate â†’ document â†’ report â†’ email):

```bash
# Start services first, then:
uv run python scripts/demo.py --url http://localhost:8000
```

---

## Eval Harness

```bash
# Run golden dataset (14 Q/A pairs, keyword + LLM-as-judge scoring)
uv run python evals/eval_harness.py --no-llm-judge

# With MLflow logging
MLFLOW_TRACKING_URI=http://localhost:5000 \
  uv run python evals/eval_harness.py --run-name baseline
```

## Agentic Testing With Playwright / DOM / OCR

The `qa-swarm/` package implements the autonomous testing pipeline described in
the project brief:

- Generator Agent: creates Aurevia API/Web/Mobile scenarios
- Executor Agent: runs API calls and Playwright browser flows
- Evaluator Agent: scores expected vs actual evidence
- Reporter Agent: writes Markdown, JSON, and CSV reports

Run against local Aurevia:

```bash
uv run aurevia-qa-swarm
```

Run against the Minikube deployment:

```bash
AUREVIA_TARGET=minikube uv run aurevia-qa-swarm
```

Reports are written to `reports/qa-swarm/`.

---

## Kubernetes / Helm Deployment

```bash
# Start minikube and deploy everything
./scripts/minikube-start.sh

# Or deploy to existing cluster
helm upgrade --install wealthmesh helm/wealthmesh \
  --namespace wealthmesh --create-namespace

# Build all images
./scripts/build-images.sh 1.0.0
```

---

## Compliance

### GDPR (EU 2016/679)
- `DELETE /api/gdpr/delete-my-data` â€” Right to Erasure (Article 17)
- Audit log with 90-day retention
- Voice audio: in-memory transcription only, never persisted
- Redis conversation TTL: 24 hours

### EU AI Act (Regulation 2024/1689)
- Risk classification: **Limited Risk** (AI assistant, human oversight enforced)
- All LLMs run locally â€” no personal data sent to third parties
- Model register: [`docs/ai-act-model-register.json`](docs/ai-act-model-register.json)
- Transparency: users are always informed they are interacting with AI

### Prompt Injection Guardrails
All messages are validated by `agentkit.guardrails.check_message()` before reaching agents:
- Injection patterns: "ignore previous instructions", "act as", system tags
- PII extraction patterns: "dump database", "show all passwords"
- Max message length: 4000 characters

---

## Project Structure

```
project/
â”œâ”€â”€ libs/
â”‚   â”œâ”€â”€ agentkit/          # Shared library: A2A, MCP, LLM, tracing, guardrails
â”‚   â””â”€â”€ db/                # SQLAlchemy models, Alembic migrations
â”œâ”€â”€ services/
â”‚   â”œâ”€â”€ orchestrator/      # LangGraph supervisor
â”‚   â”œâ”€â”€ agent-financial/   # Portfolio metrics
â”‚   â”œâ”€â”€ agent-market/      # Market data
â”‚   â”œâ”€â”€ agent-docs/        # Document RAG
â”‚   â”œâ”€â”€ agent-action/      # Email / report / WhatsApp
â”‚   â”œâ”€â”€ agent-qa/          # AI-SDLC test generation
â”‚   â””â”€â”€ voice/             # STT + TTS callbot
â”œâ”€â”€ frontend/              # React + Vite + Tailwind web app
â”œâ”€â”€ mobile/                # React Native / Expo mobile app
â”œâ”€â”€ evals/                 # Golden dataset + eval harness
â”œâ”€â”€ infra/
â”‚   â”œâ”€â”€ traefik/           # Gateway config
â”‚   â”œâ”€â”€ keycloak/          # Realm export
â”‚   â”œâ”€â”€ postgres/          # Init SQL
â”‚   â””â”€â”€ k8s/               # Kustomize base + overlays
â”œâ”€â”€ helm/wealthmesh/       # Helm chart
â”œâ”€â”€ scripts/               # Demo, build-images, minikube-start
â””â”€â”€ docs/                  # AI Act model register
```

---

## Hardware Notes

Built and benchmarked on **RTX 2050 (4GB VRAM)**:
- One LLM loaded at a time via Ollama on host
- All agents use LLM fallback gracefully when Ollama is unavailable
- Minikube limited to 6 GB RAM to leave headroom for Ollama

---

## Phases Completed

| Phase | Description | Tests |
|-------|-------------|-------|
| 0 | Monorepo scaffold | â€” |
| 1 | RTX 2050 LLM benchmark | â€” |
| 2 | agentkit shared library | 12 |
| 3 | SQLAlchemy models + Alembic + finance metrics | 14 |
| 4 | Traefik gateway + Keycloak realm | 3 |
| 5 | LangGraph supervisor graph | 8 |
| 6 | Financial Assistant agent | 14 |
| 7 | Market Data agent | 6 |
| 8 | Document / RAG agent | 5 |
| 9 | Action agent (email / report / WhatsApp) | 6 |
| 10 | QA / Tester agent | 3 |
| 11 | Voice callbot (STT + TTS) | 6 |
| 12 | Observability (Langfuse + MLflow eval) | 4 |
| 13 | React web frontend | â€” |
| 14 | React Native / Expo mobile | â€” |
| 15 | Kubernetes + Helm + Dockerfiles | â€” |
| 16 | Compliance + GDPR + guardrails + demo | 16 |
| **Total** | | **121 tests** |


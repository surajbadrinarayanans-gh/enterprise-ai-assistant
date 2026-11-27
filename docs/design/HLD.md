# HLD: Enterprise Knowledge Assistant

| Field | Value |
|---|---|
| Status | Draft v1.0 |
| Date | 2026-11-27 |
| Author | Claude (documents) · Suraj (engineering owner) |
| Implements | `docs/requirements/PRD.md` v1.0 |
| Next documents | ADRs in `docs/adr/`, then an LLD per slice |

> **How to read this document**
> The PRD said **what** and **why**. The HLD (High-Level Design) says **how, at the level of boxes and arrows**:
> which components exist, what each one owns, how data flows between them, and which technologies we use.
> It does **not** contain code or function-level detail. That goes in an LLD (Low-Level Design) per feature.
> In interviews, "system design" rounds are basically you producing an HLD on a whiteboard in 45 minutes.

---

## 1. Design principles
*Why this section exists: principles settle arguments before they start. When two options look equal, the principles decide.*

| # | Principle | What it means for us |
|---|---|---|
| P1 | **API-first** | The versioned REST API (US-05) is designed before the internals. The UI, the agent and third-party apps are all just API clients. |
| P2 | **Vertical slices** | Build thin features end to end (API → logic → database → test) one at a time, instead of finishing one whole layer first. Something works from week one. |
| P3 | **Ports and adapters** | Business logic depends on interfaces ("I need an LLM", "I need embeddings"), never on a vendor. Vendors plug in as adapters. |
| P4 | **Tenant-aware from day one** | Every table has a `tenant_id`. Costs almost nothing now; retrofitting it later is painful. |
| P5 | **Secure by default** | Auth on every endpoint except health checks; least privilege; no secrets in Git; no prompts in logs. |
| P6 | **Observable by default** | Every component exposes health, metrics and structured logs from its first version. |
| P7 | **Everything as code** | App, infrastructure, dashboards, alerts and docs live in Git. |

## 2. System context
*Why this section exists: before the inside, show what is outside. Who uses the system, and what does it depend on?*

```
   Employees ──(browser)──> [ Web UI ] ─┐
                                        │  HTTPS + API key
   Internal apps / third parties ───────┼──────────────────> ┌──────────────────────────────┐
                                        │                     │  ENTERPRISE KNOWLEDGE        │
   Knowledge admins (upload docs) ──────┘                     │  ASSISTANT (our system)      │
                                                              └──────┬──────────────┬────────┘
                                                                     │              │
                                                     External LLM API│              │Company databases
                                                     (paid, fallback)│              │(read-only, sample data)
   On-call SRE <── alerts, dashboards (Grafana) ─────────────────────┘
```

## 3. Component view
*Why this section exists: names each building block and its single responsibility. If a box does two unrelated jobs, split it.*

```
                         ┌────────────────────────────── API service (FastAPI) ──────────────────────────────┐
 Client ── /v1/... ────> │  Auth + rate limit  →  Routers: documents | ask | chat  →  Problem-details errors   │
                         └───────┬─────────────────────────┬───────────────────────────┬──────────────────────┘
                                 │ upload                  │ ask (RAG)                 │ chat (agent)
                                 ▼                         ▼                           ▼
                      ┌──────────────────┐     ┌───────────────────┐        ┌────────────────────┐
                      │ Ingestion worker │     │ Retrieval service │◄───────│ Agent (LangGraph)  │
                      │ parse → chunk →  │     │ hybrid search     │  tool  │ plan → tool → answer│
                      │ embed → store    │     │ (vector+keyword)  │        │ tool: read-only SQL │
                      └────────┬─────────┘     └─────────┬─────────┘        └─────────┬──────────┘
                               │ Embeddings port         │                            │ LLM port
                               ▼                         ▼                            ▼
                      ┌─────────────────────────────────────────┐      ┌──────────────────────────────┐
                      │ Postgres 16 + pgvector                  │      │ LLM Gateway                  │
                      │ tenants, api_keys, documents, chunks,   │      │ adapters: self-hosted model, │
                      │ audit_log, sample business tables       │      │ external API; failover, PII  │
                      └─────────────────────────────────────────┘      │ redaction, tokens, cost      │
                                                                       └──────────────────────────────┘
        Cross-cutting: Prometheus metrics · OpenTelemetry traces · JSON logs · Grafana · Alertmanager
```

| Component | Responsibility | Requirements |
|---|---|---|
| **API service** | Single entry point: auth, rate limits, validation, versioned routes, errors | FR-12, FR-13, US-05 |
| **Ingestion worker** | Turn an uploaded file into searchable chunks, asynchronously | FR-01–03 |
| **Retrieval service** | Given a question, return the best chunks with metadata | FR-04, NFR-03 |
| **Answering (RAG)** | Build a prompt from chunks, call the LLM port, return answer + citations or "I don't know" | FR-05, US-01 |
| **Agent** | Multi-step questions; chooses between `search_documents` and `query_database` | FR-06–08 |
| **LLM Gateway** | One interface for all LLM calls; provider failover; redaction; usage metering | FR-09–11, FR-14 |
| **Postgres + pgvector** | System of record for metadata **and** vectors in one database | A2, ADR-003 |
| **Observability stack** | Metrics, traces, logs, dashboards, alerts | FR-18, NFR-08 |

> **Design choice to notice:** in the beginning, API, ingestion, retrieval and answering live in **one deployable Python app**
> (a *modular monolith*: one service, clean internal modules). We split out the ingestion worker when it needs to scale on its own.
> Starting with microservices on day one is a classic mistake. Being able to say *why* you didn't is a strong interview answer.

## 4. Key flows
*Why this section exists: arrows on a component diagram hide the order of events. Flows show it, step by step.*

### 4.1 Ingest a document (US-04)
```
Admin → POST /v1/documents (file)
  1. API: authenticate key → find tenant
  2. API: compute file hash (skip if same file already ingested) → save file → insert documents row (status=processing)
  3. API: respond 202 Accepted + document_id        ← client doesn't wait for slow work
  4. Worker: parse text → split into chunks (~500 tokens, small overlap)
  5. Worker: embeddings port → one vector per chunk
  6. Worker: insert chunks (text, vector, page/section, tenant_id) → status=ready  (or failed + reason)
Admin → GET /v1/documents/{id} → {"status": "ready", "chunks": 42}
```

### 4.2 Ask a question (US-01)
```
Employee → POST /v1/ask {"question": "What is our refund policy?"}
  1. API: authenticate → tenant
  2. Retrieval: embed the question → vector search + keyword search **filtered by tenant_id** → merge → top 5 chunks
  3. If best score below threshold → answer "I don't know" (no LLM call, saves cost)
  4. Answering: prompt = rules ("answer only from sources, cite them") + numbered chunks + question
  5. LLM port → answer text containing [1], [2] markers
  6. API: map markers to document names/sections → return answer + citations (+ usage: tokens, latency)
```

### 4.3 Agent question (US-02, later slice)
```
"Refund policy, and how many refund tickets last week?"
  plan → tool search_documents("refund policy") → tool query_database("SELECT count(*) ... WHERE category='refund' AND created_at > now()-7d")
       → combine → answer with citations + list of tools used
```

## 5. API design (v1)
*Why this section exists: the API is the product's contract with the outside world (P1). Changing it breaks clients, so it is designed deliberately.*

| Method | Path | Purpose | Success |
|---|---|---|---|
| GET | `/healthz` | Liveness: is the process alive? | 200 |
| GET | `/readyz` | Readiness: can it serve (DB reachable)? | 200 / 503 |
| POST | `/v1/documents` | Upload a document | 202 + `id` |
| GET | `/v1/documents` | List documents (paginated) | 200 |
| GET | `/v1/documents/{id}` | Status and details | 200 / 404 |
| DELETE | `/v1/documents/{id}` | Remove document and its chunks | 204 |
| POST | `/v1/ask` | RAG answer with citations (streaming option) | 200 |
| POST | `/v1/chat/completions` | OpenAI-compatible chat via agent (later slice) | 200 |
| GET | `/metrics` | Prometheus metrics (internal network only) | 200 |

**Conventions**
- Versioning in the path (`/v1`). Breaking changes go to `/v2`; `/v1` keeps working for a deprecation period.
- Auth header: `Authorization: Bearer <api_key>`.
- Errors use one shape everywhere (RFC 9457 "problem details"): `{"type", "title", "status", "detail", "request_id"}`.
- Every response carries an `X-Request-ID` header, the thread that ties logs and traces together.
- Pagination: `?limit=20&cursor=...` (cursor-based, stable under inserts).
- OpenAPI docs generated automatically by FastAPI at `/docs`; the OpenAPI file is what **contract tests** check in CI.

## 6. Data model (first version)
*Why this section exists: data outlives code. Getting the core tables right early saves painful migrations later.*

```
tenants      (id, name, created_at)
api_keys     (id, tenant_id → tenants, key_hash, name, created_at, revoked_at)
documents    (id, tenant_id, filename, content_sha256, status, error, created_at, updated_at)
chunks       (id, tenant_id, document_id → documents ON DELETE CASCADE, ordinal, text,
              embedding vector(N), page, section, created_at)
audit_log    (id, tenant_id, actor_key_id, action, resource, created_at)          -- later slice
tickets      (id, tenant_id, category, status, created_at, ...)                     -- sample data for the agent
```
- API keys are stored **hashed**, like passwords. A database leak must not leak usable keys.
- `chunks.embedding` gets an approximate-nearest-neighbour index (HNSW) so search stays fast as data grows.
- `N` (vector size) depends on the embedding model chosen (ADR-008), e.g. 384 for a small local model.
- Every query filters on `tenant_id`. Later, Postgres **row-level security** enforces it even if code forgets.

## 7. Technology choices
*Why this section exists: one place to see the stack. Big or debatable choices get an ADR; obvious ones just get a reason.*

| Concern | Choice | Reason | ADR |
|---|---|---|---|
| Language | Python 3.12 | Target JDs; AI ecosystem | — |
| Project/package tool | **uv** | One fast tool for Python versions, virtualenvs, dependencies and lockfile; becoming the industry default | — |
| Web framework | FastAPI + Pydantic | Async, type-validated, auto OpenAPI docs | — |
| Database access | SQLAlchemy 2 + Alembic migrations | Industry standard ORM; versioned schema changes | — |
| Database | Postgres 16 + pgvector | One DB for metadata and vectors; SQL skills reused | ADR-003 |
| Embeddings | Small local open model first; API model as an adapter | Free, private, runs on CPU | ADR-008 |
| LLM (answers) | External API first (e.g. Claude Haiku), self-hosted model added in the gateway slice | Quality early; self-hosting when we have K8s | ADR-005 |
| Agent | LangGraph | Named in Apple/Visa JDs; explicit state graph | ADR-004 |
| Background jobs | FastAPI background task → Redis queue → Kafka/Redpanda (evolves) | Simplest thing first, upgrade with need | ADR-009 |
| Tests | pytest, httpx test client, testcontainers (real Postgres in tests), schemathesis (contract) | Full test pyramid | — |
| Quality checks | ruff (lint + format), mypy (types), pre-commit | Catches mistakes before review | — |
| Containers / platform | Docker → kind → Helm → Terraform → GKE/EKS → Argo CD | Per PRD milestones | ADR-006, 007 |
| Observability | Prometheus, Grafana, OpenTelemetry, Loki | Industry standard, open source | — |

## 8. Repository layout
*Why this section exists: a predictable layout lets any engineer find anything. It also shows the architecture in folder form.*

```
DevOps-SRE/
├── app/                        # the Python service (one uv project)
│   ├── pyproject.toml          # dependencies and tool settings
│   ├── src/eka/                # "eka" = Enterprise Knowledge Assistant (our package)
│   │   ├── main.py             # creates the FastAPI app
│   │   ├── api/                # routers: health, documents, ask (HTTP only, no business logic)
│   │   ├── core/               # config, logging, errors, security
│   │   ├── domain/             # business logic + ports (interfaces); no FastAPI, no vendors
│   │   ├── adapters/           # implementations: postgres, embeddings, llm providers
│   │   └── ingestion/          # parse, chunk, embed pipeline
│   └── tests/                  # unit/, integration/, contract/
├── ui/                         # later
├── k8s/                        # manifests / Helm chart
├── infra/                      # Terraform
└── docs/                       # requirements/, design/, adr/, runbooks/, interview-prep/
```
The `api → domain ← adapters` direction **is** the hexagonal architecture: the domain in the middle knows nothing about the web or vendors.

## 9. Cross-cutting concerns
*Why this section exists: some concerns touch every component. Deciding them once avoids each module inventing its own.*

- **Security:** API keys hashed; TLS at the ingress; secrets from environment/secret manager; SQL tool uses a read-only DB role; uploaded files size- and type-limited; dependency and image scanning in CI.
- **Multi-tenancy:** `tenant_id` on every row and every query; row-level security later; per-tenant rate limits.
- **Observability:** RED metrics per endpoint (**R**ate, **E**rrors, **D**uration); LLM metrics (tokens, TTFT, cost, provider, fallback count); trace spans for retrieve → generate; JSON logs with `request_id`, never prompt text.
- **Configuration:** 12-factor style. All settings from environment variables, validated at startup; app refuses to start with bad config.
- **Errors and resilience:** timeouts on every external call; retries with backoff only for safe operations; fallback provider in the gateway; graceful degradation ("search is slow" never takes down `/healthz`).

## 10. Failure modes
*Why this section exists: SRE thinking means designing for failure before it happens. Each row becomes a test, an alert or a runbook later.*

| Failure | Effect | Detection | Response |
|---|---|---|---|
| Postgres down | No ingest, no answers | `/readyz` 503, error-rate alert | Pod stops receiving traffic; runbook: check DB |
| External LLM slow/down | Answers fail or slow | TTFT and error metrics by provider | Gateway fails over to other provider |
| Embedding model OOM (out of memory) | Ingestion stalls | Worker restarts, queue age grows | Resource limits; smaller batches |
| Poisoned document (prompt injection) | Wrong or manipulated answers | Eval set includes injection cases | Read-only tools; system prompt rules; output treated as untrusted |
| Tenant filter bug | Data leak across customers | Integration test per endpoint with two tenants | Row-level security as a second safety net |
| Cost spike | Budget blown | Cost metric + alert | Per-tenant token budget; rate limits |

## 11. Build order: vertical slices
*Why this section exists: turns the design into an order of work. Each slice ends working, tested and committed.*

| Slice | Delivers | Stories |
|---|---|---|
| **S0** | Walking skeleton: uv project, FastAPI app, `/healthz`, first pytest, ruff | foundation |
| **S1** | Postgres in Docker, SQLAlchemy, Alembic, `documents` table, upload API returning 202 | US-04, US-05 |
| **S2** | Parse + chunk + embed + store in pgvector; status becomes `ready` | US-04 |
| **S3** | `/v1/ask`: retrieval + LLM answer + citations + "I don't know" | US-01 |
| **S4** | Golden-set evaluation runnable in CI | FR-16 |
| **S5** | API keys, tenants, rate limiting, problem-details errors | US-06 |
| **S6** | Streaming answers; metrics; Dockerfile | US-03, FR-18 |
| **S7** | Agent with SQL tool | US-02 |
| **S8** | LLM gateway: self-hosted model + failover + PII redaction | US-07, US-09 |

Then platform work (K8s, CI/CD, Terraform, GitOps, SRE) per the PRD milestones.

## 12. ADRs to write
ADR-001 serverless vs Kubernetes · ADR-002 ports and adapters · ADR-003 pgvector vs dedicated vector DB ·
ADR-004 LangGraph vs hand-written agent loop · ADR-005 self-hosted model server · ADR-006 kind vs k3d ·
ADR-007 first cloud · **ADR-008 embedding model** · **ADR-009 background job mechanism** (new in this HLD).

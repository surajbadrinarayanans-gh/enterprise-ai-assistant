# PRD: Enterprise Knowledge Assistant

| Field | Value |
|---|---|
| Status | Draft v1.0 |
| Date | 2026-11-26 |
| Author | Claude (documents) · Suraj (engineering, owner, on-call) |
| Reviewers | Suraj |
| Next document | `docs/design/HLD.md` (High-Level Design) |

> **How to read this document**
> A PRD (Product Requirements Document) answers *what* we build and *why*, never *how*. The *how* goes in the design docs.
> Each section starts with **Why this section exists**, which is the lesson to remember for every future PRD.
> Every item has an ID (G1, US-03, FR-12, NFR-04). Design docs, tickets, tests and dashboards refer back to these IDs.
> That chain is called **traceability**: from any line of code you can trace back to the requirement that justified it.

---

## 1. Problem statement
*Why this section exists: if the team doesn't agree on the problem, it builds the wrong thing very well.*

In a large company, knowledge is scattered across two kinds of place:
- **Unstructured data:** policies, design docs, runbooks, PDFs and wikis. People search them by hand and still miss things.
- **Structured data:** databases of tickets, orders and incidents. Only people who know SQL can query them.

Employees want to ask questions in plain English, for example *"What is our refund policy, and how many refund tickets did we get last week?"*.
Public AI tools are not allowed, because the data is confidential. Demo-quality AI is not acceptable either: it makes things up,
can't show sources, leaks sensitive data into logs, breaks under load, and nobody notices when it is down.

**We will build an Enterprise Knowledge Assistant.** It answers questions from internal documents *and* databases, with sources,
inside the company's own infrastructure. It is built and operated like a production service: tested, deployed by GitOps, observable, and held to SLOs.

> **Key terms**
> - **LLM:** large language model. It predicts text, one token (word-piece) at a time.
> - **Inference:** running a finished model on a new input. **Training** (changing the model) is not part of this project.
> - **Embedding:** a list of numbers representing the meaning of a piece of text. Similar meanings give nearby numbers.
> - **RAG (retrieval-augmented generation):** find the relevant text first (retrieval), then give it to the LLM as context to answer from (generation).
> - **Agent:** an LLM in a loop that plans, chooses a **tool** (search, SQL), reads the result, and repeats until it can answer.

## 2. Goals and non-goals
*Why this section exists: goals focus the effort. Non-goals stop scope creep. Saying "no" in writing is a senior skill.*

### Goals
| ID | Goal |
|---|---|
| G1 | Answer questions over internal **documents** with **citations** (RAG). |
| G2 | Answer questions that need **documents + database data** using an **agent** with tools. |
| G3 | Route LLM calls through a **gateway**: self-hosted model by default, external API as fallback; tracks tokens and cost. |
| G4 | **Govern** AI use: access control, PII redaction, audit log, answer-quality evaluation. |
| G5 | Run it as a **production platform**: containers, Kubernetes, Terraform, CI/CD with a full test pyramid, GitOps, on two clouds. |
| G6 | Make it **observable and reliable**: metrics, traces, logs, SLOs, alerts, runbooks, load and chaos tests. |
| G7 | Provide a **small web UI** to demo the product end to end. |

### Non-goals
| ID | Non-goal | Reason |
|---|---|---|
| NG1 | Training or fine-tuning models | Needs GPUs and weeks. Our value is building and operating the system around the model. |
| NG2 | GPU serving | No GPUs on the laptop or free tiers. We design so a GPU server can be swapped in later. |
| NG3 | Agent actions that **change** data | Tools are **read-only**. Write actions need human approval flows, which is a separate project. |
| NG4 | Real company data | We use synthetic or public sample data only. No confidential data ever enters this repo. |
| NG5 | Polished UI or mobile app | The UI exists to demo the product, not to win design awards. |
| NG6 | Billing customers | We estimate cost; we don't invoice anyone. |

## 3. Personas
*Why this section exists: every requirement must serve a real person. If no one benefits, delete the requirement.*

| Persona | Who | Needs |
|---|---|---|
| **Employee** | Any staff member | Fast, trustworthy answers with sources |
| **App developer** | Builds internal tools on our API | A stable, documented, versioned API |
| **Knowledge admin** | Owns a set of documents | Upload, update and remove documents; know they are searchable |
| **Platform admin** | Manages access and budget | Issue/revoke API keys, set limits, see usage and cost |
| **On-call SRE** | Keeps it running | Alerts, dashboards, runbooks, safe deploys and rollbacks |
| **Executive** | Funds the platform | Adoption, cost, quality and reliability at a glance |

## 4. User stories
*Why this section exists: stories state needs in the user's language. Acceptance criteria say how we will **test** that a story is done.*

Format: **As a** *persona*, **I want** *capability*, **so that** *benefit*.

| ID | Story | Acceptance criteria |
|---|---|---|
| US-01 | As an **employee**, I want to ask a question about company documents and get an answer with sources, so that I can trust and check it. | Every answer lists source document + section. If no source supports an answer, it says "I don't know". |
| US-02 | As an **employee**, I want to ask questions that combine documents and data, so that I don't need SQL skills. | Example question in §1 answered correctly; answer shows which tools were used. |
| US-03 | As an **employee**, I want the answer to stream in as it is written, so that I'm not staring at a blank screen. | First token within the NFR-02 limit. |
| US-04 | As a **knowledge admin**, I want to upload a document and have it searchable shortly after, so that answers stay current. | Status shows *processing → ready*; ready within NFR-04 limit. Deleting a document removes it from answers. |
| US-05 | As an **app developer**, I want a versioned REST API with OpenAPI docs, so that I can integrate safely. | `/v1/...` paths; auto-generated docs; breaking changes only in a new version; contract tests in CI. |
| US-06 | As a **platform admin**, I want per-team API keys and rate limits, so that access is controlled and fair. | Invalid/revoked key → 401; over limit → 429 with retry hint; keys never appear in logs. |
| US-07 | As a **platform admin**, I want personal data masked before it reaches any external LLM, so that we stay compliant. | Emails, phone numbers and card-like numbers are redacted in prompts sent to external providers; tested. |
| US-08 | As an **on-call SRE**, I want alerts tied to SLOs with runbooks, so that I fix problems before users notice. | Alert fires within 5 min of SLO burn; each alert links to a runbook. |
| US-09 | As an **on-call SRE**, I want automatic fallback when the self-hosted model fails, so that a model outage isn't a user outage. | Self-hosted model stopped → requests still succeed via fallback; fallback counted in a metric. |
| US-10 | As an **SRE**, I want every change deployed from Git with one-step rollback, so that releases are safe and auditable. | Merged PR reaches the cluster with no manual `kubectl`; `git revert` restores the previous version. |
| US-11 | As an **executive**, I want a dashboard of usage, cost, quality and reliability, so that I can decide on investment. | Grafana dashboard with weekly requests, tokens, cost, eval score, SLO status. |

## 5. Functional requirements
*Why this section exists: the concrete behaviours the system must have. Priority uses **MoSCoW**: Must, Should, Could, Won't (this release).*

| ID | Area | Requirement | Pri | Story |
|---|---|---|---|---|
| FR-01 | Ingestion | Upload documents (PDF, Markdown, text) via API | M | US-04 |
| FR-02 | Ingestion | Split documents into chunks, create embeddings, store in Postgres + pgvector | M | US-04 |
| FR-03 | Ingestion | Process uploads asynchronously with a status (`processing`, `ready`, `failed`) | M | US-04 |
| FR-04 | Retrieval | Hybrid search: semantic (embeddings) + keyword, returning top-k chunks with metadata | M | US-01 |
| FR-05 | Answering | Generate answers only from retrieved context, with citations; refuse when unsupported | M | US-01 |
| FR-06 | Agent | Agent plans and calls tools: `search_documents`, `query_database` (read-only SQL) | M | US-02 |
| FR-07 | Agent | SQL tool uses a read-only database role, query timeout, and row limit | M | US-02, NG3 |
| FR-08 | Agent | Conversation memory within a session | S | US-02 |
| FR-09 | Gateway | All LLM calls go through one gateway interface (ports and adapters) | M | G3 |
| FR-10 | Gateway | Self-hosted model by default; external provider on timeout/error | M | US-09 |
| FR-11 | Gateway | Record tokens in/out, latency, provider, estimated cost per request | M | US-11 |
| FR-12 | API | Versioned REST API (`/v1`), OpenAPI docs, streaming responses | M | US-03, 05 |
| FR-13 | Security | API-key authentication and per-key rate limiting | M | US-06 |
| FR-14 | Governance | PII redaction before external LLM calls | M | US-07 |
| FR-15 | Governance | Audit log of who asked what category of question and which tools ran (no raw prompts) | S | G4 |
| FR-16 | Quality | Evaluation suite: golden question set, scored in CI on every change | M | G4 |
| FR-17 | Ops | `/healthz` and `/readyz` endpoints | M | US-10 |
| FR-18 | Ops | Prometheus metrics, OpenTelemetry traces, structured JSON logs with request ID | M | US-08 |
| FR-19 | Ingestion | Event queue (Kafka/Redpanda) between upload and processing | C | US-04 |
| FR-20 | UI | Web page to chat, see sources, upload documents | S | G7 |
| FR-21 | Agent | Tools that write or change data | W | NG3 |

## 6. Non-functional requirements
*Why this section exists: NFRs define **how well** the system works. Without numbers, "fast" and "reliable" can't be tested.
These are starting targets. We measure in May and adjust with evidence. Changing a target based on data is normal.*

| ID | Category | Requirement |
|---|---|---|
| NFR-01 | Availability | 99.5% of API requests succeed over 30 days (fallback successes count as success). |
| NFR-02 | Latency | Time to first token < 3 s for 95% of requests. |
| NFR-03 | Latency | Retrieval (search step alone) < 300 ms for 95% of requests. |
| NFR-04 | Freshness | A 50-page document is searchable within 2 minutes of upload. |
| NFR-05 | Quality | On the golden set: ≥ 80% answers judged correct and faithful to sources; 100% include citations. |
| NFR-06 | Security | TLS in transit; secrets only in secret managers; least-privilege IAM; images scanned; no prompts, answers or keys in logs. |
| NFR-07 | Scalability | API scales 2 → 6 replicas automatically; load test documents behaviour at 5x normal traffic. |
| NFR-08 | Observability | Every SLI visible on a dashboard; every request traceable end to end by request ID. |
| NFR-09 | Recoverability | Entire environment rebuilt from Git + Terraform in < 60 min (RTO). Documents re-indexable from storage. |
| NFR-10 | Cost | LLM API spend < US$10/month; cloud resources destroyed after each session; billing alerts set before first use. |
| NFR-11 | Portability | Runs on any Kubernetes; no hard lock-in to one cloud or one LLM vendor. |
| NFR-12 | Testability | Unit, integration, contract and end-to-end tests run in CI; main branch always green. |

## 7. Success metrics: SLIs, SLOs and error budget
*Why this section exists: SRE turns "is it good?" into numbers.
An **SLI** is what we measure. An **SLO** is our internal target. An **SLA** is a promise to customers with penalties (we have none).
The **error budget** is the failure we are allowed. Budget left means we ship features; budget gone means we stop and fix reliability.*

| SLI | SLO | Window |
|---|---|---|
| Successful requests / all requests | ≥ 99.5% | 30 days |
| Time to first token, p95 | < 3 s | 30 days |
| Golden-set answer quality | ≥ 80% | per release |

**Error budget:** 30 days × 24 h = 720 h. 0.5% × 720 h = **3.6 hours** of failure allowed per month.

**Product metrics (for the executive):** weekly active users, questions per day, % answers with citations, cost per 1,000 questions.

## 8. Constraints
*Why this section exists: constraints are fixed facts. They explain many design choices before anyone asks.*

- **Time:** 1 hour/day for about 8 months (Dec 2026 – Jul 2027).
- **Hardware:** MacBook M3 Pro, 18 GB RAM, arm64. Local cluster + database + model + monitoring must fit.
- **Money:** free cloud credits + about US$10/month of LLM API usage.
- **Language:** Python for all application code.
- **People:** one engineer playing every role, so automation and documentation matter more, not less.

## 9. Assumptions
*Why this section exists: an assumption is believed but not proven. Writing it down tells us what to check early.*

| ID | Assumption | If false |
|---|---|---|
| A1 | A small quantized model (0.5–3B parameters) on CPU gives usable answers for simple questions. | Use the external API as primary; self-hosted becomes the fallback. |
| A2 | Postgres + pgvector is fast enough for our document volume (thousands of chunks). | Evaluate a dedicated vector DB (ADR-003). |
| A3 | Free credits cover short sessions of managed Kubernetes on two clouds. | Use k3s on small VMs instead. |
| A4 | Synthetic sample data is realistic enough to demonstrate value. | Use public datasets (e.g. open policy documents). |

## 10. Risks
*Why this section exists: risks are things that might happen. Each has a planned response (mitigation).*

| ID | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Hallucinated answers | High | High | Answer-from-context only; citations; refusal; evaluation in CI. |
| R2 | Prompt injection (text in a document tries to give the model orders) | Medium | High | Read-only tools; treat model output as untrusted; injection test cases in the golden set. |
| R3 | Agent generates harmful SQL | Medium | High | Read-only DB role; allow-listed tables; timeout; row limit. |
| R4 | Secret leaked to GitHub | Medium | High | `.gitignore`; secret scanning in CI; rotate immediately. |
| R5 | Cloud bill surprise | Medium | High | Billing alerts first; destroy after each session. |
| R6 | Laptop runs out of RAM | High | Medium | Small model; resource limits; run only what the session needs. |
| R7 | Schedule slip (1 h/day) | High | Medium | Monthly milestones; cut "Could" items first; second cloud is optional if behind. |

## 11. Milestones
*Why this section exists: it turns the plan into dated checkpoints that can be tracked and reviewed.*

| Month | Milestone | SDLC focus |
|---|---|---|
| Dec 2026 | PRD, HLD, ADRs; Python, FastAPI, Postgres, pytest; first API live locally | Requirements, design, development |
| Jan 2027 | Ingestion + RAG with citations + evaluation; Docker | Development, testing |
| Feb 2027 | Agent with tools; LLM gateway with failover; PII redaction | Development, security |
| Mar 2027 | Kubernetes, Helm; CI with test pyramid and image scanning | Build, test automation |
| Apr 2027 | Terraform; first cloud; Argo CD GitOps | Infrastructure, release |
| May 2027 | Metrics, traces, logs; SLOs, alerts, runbooks; load + chaos tests; queue | Operate |
| Jun 2027 | UI; second cloud; security hardening; README, diagrams, blog post | Polish |
| Jul 2027 | Incident drill + postmortem, retrospective, mock interviews | Review |

## 12. Open decisions
*Why this section exists: big choices are recorded as **ADRs** (Architecture Decision Records) in `docs/adr/`: context, options, decision, consequences.*

| ADR | Question |
|---|---|
| ADR-001 | Serverless (e.g. AWS Lambda, which you use at work with SAM) vs Kubernetes for each component |
| ADR-002 | Hexagonal (ports and adapters) structure for LLM providers |
| ADR-003 | Vector store: pgvector vs a dedicated vector DB (Qdrant) |
| ADR-004 | Agent framework: LangGraph vs a hand-written loop |
| ADR-005 | Self-hosted model server: llama.cpp vs Ollama |
| ADR-006 | Local cluster: kind vs k3d |
| ADR-007 | First cloud: GCP vs AWS |

## 13. Definition of Done
*Why this section exists: one shared checklist for "done", so nothing ships half-finished.*

A feature is done when it is: built on a branch, reviewed in a PR, covered by tests that pass in CI, scanned, deployed by GitOps,
visible on a dashboard (metric added), backed by a runbook if it adds an alert, and documented.

## 14. Glossary
- **API:** a contract that lets programs talk to each other.
- **Chunk:** a small piece of a document, sized so search is precise.
- **Citation:** a reference to the source chunk an answer came from.
- **Golden set:** a fixed list of questions with known good answers, used to test quality.
- **GitOps:** Git is the single source of truth for what runs; a controller makes the cluster match Git.
- **p95:** the value that 95% of requests are faster than.
- **PII:** personally identifiable information (names, emails, phone numbers).
- **RTO:** recovery time objective, the maximum time allowed to restore service.
- **Token:** a word-piece; models read and write tokens, and providers bill by them.

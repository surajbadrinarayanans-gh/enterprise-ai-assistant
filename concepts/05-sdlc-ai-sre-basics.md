# 05 · SDLC, AI and SRE basics

## SDLC documents
| Doc | Answers | Ours |
|---|---|---|
| **PRD** (Product Requirements) | **What** and **why**: problem, goals, non-goals, personas, stories, requirements | `docs/requirements/PRD.md` |
| **HLD** (High-Level Design) | **How**, as boxes and arrows: components, flows, API, data, tech choices | `docs/design/HLD.md` |
| **LLD** (Low-Level Design) | How, per feature: classes, functions, edge cases | later |
| **ADR** (Architecture Decision Record) | One decision: context, options, choice, consequences | `docs/adr/` |
| **Runbook** | What to do when an alert fires | `docs/runbooks/` |
| **Postmortem** | What broke, why, how we prevent it (blameless) | later |

- **Traceability:** IDs (US-01, FR-05, NFR-02) link code, tests and dashboards back to requirements.
- **User story:** *As a <who>, I want <what>, so that <why>*, plus acceptance criteria (how we test it).
- **Functional** = what it does. **Non-functional** = how well (latency, availability, security, cost), always with numbers.
- **Non-goals** stop scope creep. **MoSCoW** = Must / Should / Could / Won't.
- **Definition of Done:** one shared checklist for "finished".

## Design ideas
- **API-first:** design the contract before the internals; UI, agent and partners are all API clients.
- **Vertical slice:** build one thin feature end to end (API → logic → DB → test) before the next.
- **Modular monolith first:** one deployable with clean modules; split into services only when needed.
- **Hexagonal / ports and adapters:** business logic depends on interfaces; vendors plug in as adapters. Enables swapping LLM providers and failover.

## AI terms
| Term | Meaning |
|---|---|
| **LLM** | Model that predicts text one **token** (word-piece) at a time |
| **Training** | Changing model weights by learning from data (not our job) |
| **Inference** | Running a finished model on new input to get output |
| **Embedding** | Numbers representing meaning; similar meaning → nearby numbers |
| **RAG** | Retrieve relevant chunks first, then give them to the LLM as context to answer from |
| **Chunk** | Small piece of a document, sized so search is precise |
| **Agent** | LLM in a loop: plan → call a tool → read result → repeat → answer |
| **Hallucination** | Confident, wrong output. Countered with citations, refusal and evaluation |
| **Prompt injection** | Text (e.g. in a document) that tries to give the model orders |

Most companies don't train models; they use open-weights or API models plus RAG over their own data.

## SRE numbers
- **SLI:** what we measure (e.g. successful requests / all requests).
- **SLO:** our target for it (e.g. ≥ 99.5% over 30 days).
- **SLA:** promise to customers with penalties.
- **Error budget:** allowed failure. 30 days × 24 h = 720 h; 0.5% of 720 h = **3.6 h/month**. Budget left → ship features; budget spent → freeze and fix reliability.
- **p95:** the value 95% of requests are faster than.
- **TTFT:** time to first token. A key LLM latency metric.
- **RTO:** maximum time allowed to restore service.

## Interview questions
1. PRD vs HLD vs ADR: what does each answer?
2. Why write non-goals?
3. Training vs inference? Why do most companies not train models?
4. Explain RAG to a non-technical manager in two sentences.
5. Calculate the monthly error budget for a 99.9% SLO.
6. Why start with a modular monolith instead of microservices?

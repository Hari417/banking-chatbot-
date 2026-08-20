# Banking RAG Chatbot — Documentation Outline

**Version:** 1.1
**Date:** 2026-08-20
**Author:** Scribe (Documentation)
**Status:** Current — documentation tree written and verified against the implemented
source under `src/` on 2026-08-20 (task t_1547ebb4). Each deliverable file now carries
its own front-matter `Status` field as the source of truth; the outline map below is
updated to reflect which files exist. See `docs/STATUS.md` for the rolled-up status.

---

## Purpose

This outline defines the full set of documentation deliverables for the Banking RAG
Chatbot v1, the owner of each deliverable, the source material it is grounded in, and
its current status. It is the map the `scribe` profile works against once the
implementation stabilizes.

The project documentation follows the lifecycle defined in the triage card:

```
RESEARCH → ARCHITECTURE → IMPLEMENTATION → VERIFICATION → FIXES → VERIFICATION → DOCUMENTATION → DONE
```

Scribe documents the **actual implementation** rather than the originally planned
architecture whenever the two diverge. Drafted documents that describe planned (not
yet implemented) behavior are marked `Status: Planned` and re-verified against code
before being marked `Status: Current`.

---

## Source Artifacts

All current documentation is grounded in the following artifacts already produced
upstream in the triage pipeline:

| Artifact | Author | Role |
|----------|--------|------|
| `ARCHITECTURE.md` | Archer | High-level architecture, component summary, data flow |
| `component-specification.md` | Archer | Detailed component definitions and API/endpoint specs |
| `technology-rationale.md` | Archer | Technology selection with alternatives and trade-offs |
| `risk-analysis.md` | Archer | Risk register (16 risks) and mitigations |
| `MODULE_BREAKDOWN.md` | Archer | 13 core modules, interfaces, delivery milestones |
| `DEPENDENCY_GRAPH.md` | Archer | Module dependencies and execution flow diagrams |
| `SPRINT_TASK_OUTLINE.md` | Archer | 4 sprints, 15 tasks, acceptance criteria |
| `ROADMAP_SUMMARY.md` | Archer | Roadmap summary and acceptance criteria |
| `architecture-diagram.html` | Archer | Interactive SVG architecture diagram |

These artifacts are the authoritative source for planned architecture. Each
documentation deliverable below cites the specific source(s) it derives from.

---

## Documentation Tree

```
Banking/
├── README.md                              (project front door — Scribe)
├── docs/
│   ├── DOCUMENTATION_OUTLINE.md            (this file — Scribe)
│   ├── STYLE_GUIDE.md                      (documentation + code standards — Scribe)
│   ├── ARCHITECTURE.md                     ← exists (Archer) — kept in sync by Scribe
│   ├── architecture/                       (architecture overview — Scribe, after impl)
│   │   └── overview.md                     (narrative architecture walkthrough)
│   ├── api/                                (API specs — Scribe, after impl)
│   │   ├── chat-endpoint.md                (POST /chat)
│   │   ├── ingest-endpoint.md              (POST /ingest)
│   │   ├── health-endpoint.md              (GET /health)
│   │   └── config-endpoint.md              (GET/POST /config)
│   ├── setup/                              (setup guide — Scribe, after impl)
│   │   ├── prerequisites.md                (Python version, OS, API keys)
│   │   ├── installation.md                 (clone, venv, pip install, .env)
│   │   ├── configuration.md                (config.yaml schema, env vars)
│   │   ├── document-ingestion.md           (loading PDF/HTML/TXT into the index)
│   │   ├── running-locally.md               (start backend + Streamlit UI)
│   │   └── troubleshooting.md              (common errors and fixes)
│   ├── user-guide/                         (user manual — Scribe, after impl)
│   │   ├── getting-started.md              (launching the chat UI)
│   │   ├── asking-questions.md             (how to phrase queries for best results)
│   │   ├── understanding-citations.md      (reading source citations [1], [2])
│   │   ├── session-management.md           (new session, session expiry, history)
│   │   └── limitations-and-scope.md        (what the bot will and will NOT answer)
│   ├── runbook/                            (maintenance runbook — Scribe, after hardening)
│   │   ├── reindexing.md                   (how to rebuild the FAISS index)
│   │   ├── index-corruption-recovery.md    (checksum verify, backup restore, rebuild)
│   │   ├── llm-provider-swap.md            (OpenAI ↔ Ollama switch, config changes)
│   │   ├── embedding-model-change.md      (version pinning, full re-index procedure)
│   │   ├── log-rotation-and-retention.md   (structured-log lifecycle, audit retention)
│   │   ├── session-cleanup.md              (in-memory TTL, v2 SQLite cleanup)
│   │   └── incident-response.md            (prompt-injection / PII-leak handling)
│   ├── compliance/                         (auditability & compliance — Scribe)
│   │   ├── audit-trail.md                  (what is logged, for how long, who can read)
│   │   ├── pii-handling.md                 (detection, redaction, storage, edge cases)
│   │   ├── scope-enforcement.md            (how out-of-scope queries are rejected)
│   │   └── disclaimer.md                   (prototype-not-for-production notices)
│   ├── evaluation/                         (evaluation & limitations — Scribe, after Sentinel)
│   │   ├── metrics.md                      (Recall@K, MRR, Answer F1, hallucination rate)
│   │   ├── test-datasets.md                (JSONL evaluation dataset spec)
│   │   └── known-limitations.md            (v1 constraints, accepted risks, v2 path)
│   └── decisions/                          (decision records — Scribe, as decisions are made)
│       └── adr-NNNN-template.md            (ADR template)
└── (implementation source follows MODULE_BREAKDOWN.md tree)
```

---

## Deliverable Details

### 1. README.md (Project Front Door)

**Owner:** Scribe
**Status:** Planned (draft after implementation skeleton exists)
**Sources:** `ARCHITECTURE.md`, `MODULE_BREAKDOWN.md`, `SPRINT_TASK_OUTLINE.md`

**Contents:**
- One-paragraph project description (banking FAQ RAG chatbot, local-first prototype)
- In-scope / out-of-scope statement (FAQ only; NO transactions, balances, auth, real customer data)
- Quick-start (prerequisites → install → configure → ingest → run)
- Architecture overview link → `docs/architecture/overview.md`
- Tech stack summary table (from `technology-rationale.md`)
- v1 limitations summary (single user, in-memory session, no production compliance)
- Links to setup, user guide, runbook, and compliance docs
- "Not for production use" disclaimer

---

### 2. Architecture Overview

**Owner:** Scribe (writing), Archer (architecture authority)
**Status:** Planned (the narrative is written after implementation; the existing
`ARCHITECTURE.md` written by Archer remains the reference until then)
**Sources:** `ARCHITECTURE.md`, `component-specification.md`, `DEPENDENCY_GRAPH.md`

**Files:**
- `docs/architecture/overview.md` — narrative walkthrough that complements, not
  replaces, the existing `ARCHITECTURE.md`. Covers:
  - Layer diagram (presentation → orchestration → retrieval → indexing → storage → LLM)
  - Component responsibilities, one paragraph each, cross-linked to component-specification
  - Data flow for a query (security check → intent classification → hybrid retrieval
    → fusion → rerank → assemble → prompt → LLM → validate → cite → respond)
  - Data flow for ingestion (load → clean → chunk → embed → index → persist)
  - Integration points (LLM provider, document sources, session storage)
  - Scalability boundaries and v1 → v2 evolution path

---

### 3. API Specifications

**Owner:** Scribe (after implementation)
**Status:** Planned
**Sources:** `component-specification.md` §2.1, `ARCHITECTURE.md` §3

**One file per endpoint.** Each spec contains:
- Method and path
- Purpose
- Request schema (Pydantic model → JSON example)
- Response schema (JSON example)
- Error responses and HTTP status codes
- Rate-limit behavior (10/minute default from `security.rate_limit`)
- Streaming behavior (where applicable, for `/chat`)
- Security pre-checks applied (PII detection, injection filter, input length)
- Audit-log entry produced (see `docs/compliance/audit-trail.md`)
- Example `curl` invocation

**Endpoints covered:**
| Endpoint | Method | Doc file |
|----------|--------|----------|
| `/chat` | POST | `docs/api/chat-endpoint.md` |
| `/ingest` | POST | `docs/api/ingest-endpoint.md` |
| `/health` | GET | `docs/api/health-endpoint.md` |
| `/config` | GET / POST | `docs/api/config-endpoint.md` |

---

### 4. Setup Guide

**Owner:** Scribe (after implementation skeleton)
**Status:** Planned
**Sources:** `component-specification.md` §8 (config schema), `technology-rationale.md`
§5 (dependencies), `MODULE_BREAKDOWN.md` (module delivery)

**Files:**
- `prerequisites.md` — Python 3.9+, OS notes (local-first, no Postgres), OpenAI API key
  OR Ollama install (configurable provider)
- `installation.md` — clone repo, create venv (PEP 668 noted), `pip install -r
  requirements.txt`, optional deps (`presidio-analyzer`, `ollama`), venv size note (~1.5
  GB with model downloads)
- `configuration.md` — full `config.yaml` schema with every field explained, `.env`
  variables (`OPENAI_API_KEY`, `OLLAMA_HOST`), config fallback chain
  (config.yaml → .env → defaults)
- `document-ingestion.md` — supported formats (PDF/HTML/TXT v1), how to place
  documents, how to trigger ingestion via `/ingest`, what metadata is extracted,
  how long indexing takes per the non-functional target (< 10 min for 100-page PDF)
- `running-locally.md` — start FastAPI (`uvicorn`, port 8000), start Streamlit
  (port 8501), health-check command, first query walkthrough
- `troubleshooting.md` — common errors: missing API key, index file not found, FAISS
  dimension mismatch, embedding model drift, Ollama unreachable, rate-limit hits

---

### 5. User Manual

**Owner:** Scribe (after UI is functional)
**Status:** Planned
**Sources:** `component-specification.md` §1.1 (UI features), §4.7–4.8 (response
validation, citations), §5 (session), `risk-analysis.md` R004 (scope control), R016
(compliance)

**Files:**
- `getting-started.md` — how to open the Streamlit UI, what you see, first question
- `asking-questions.md` — best practices for banking-FAQ queries, the system prompt's
  rules (concise, only from documents, cite with [1][2], never transaction advice)
- `understanding-citations.md` — what [1], [2] markers mean, collapsible source panel,
  excerpt + source filename + page, confidence score
- `session-management.md` — "New Session" button behavior, 30-minute TTL (in-memory v1),
  what is lost on restart, what happens if you continue an expired session
- `limitations-and-scope.md` — what the bot will NOT answer (account balances,
  transactions, other customers' data, internal systems), standard abstinence message,
  how to know abstention was triggered vs. an error

---

### 6. Maintenance Runbook

**Owner:** Scribe (after hardening sprint)
**Status:** Planned
**Sources:** `risk-analysis.md` R006–R013, `component-specification.md` §6–7, §10–11
(error handling, deployment)

**Files:**
- `reindexing.md` — when to re-index (new documents, embedding model change, FAISS
  upgrade), the exact command sequence, how to verify the new index loads
- `index-corruption-recovery.md` — R008 mitigation: checksum (SHA-256) verify on
  startup, restore from backup (previous index version kept), automated rebuild
  trigger, how to detect via `/health`
- `llm-provider-swap.md` — switch `llm.provider` in `config.yaml`, change API key or
  Ollama host, no code change required (OpenAI-compatible interface), fallback chain
- `embedding-model-change.md` — R009 mitigation: pin exact version in
  `requirements.txt`, store model info with index metadata, verify embedding dimensions
  match at load, MUST re-index the entire corpus (documented full re-index procedure)
- `log-rotation-and-retention.md` — structured-log file location (`./logs`), JSON
  format, rotation policy, retention aligned with compliance requirements in
  `docs/compliance/audit-trail.md`
- `session-cleanup.md` — v1 in-memory TTL (30 min idle auto-cleanup), v2 SQLite
  cleanup procedure, when sessions are lost (process restart — R007 accepted for v1)
- `incident-response.md` — handling suspected prompt injection (R002), PII leakage
  (R003), scope-creep queries (R004), how to read the audit log, who to escalate to

---

### 7. Compliance & Auditability

**Owner:** Scribe
**Status:** Planned (standards defined now in `STYLE_GUIDE.md`; documents written as
implementation lands)
**Sources:** `risk-analysis.md` R002, R003, R004, R016, `component-specification.md`
§3 (security), §10 (error handling)

This cluster aligns documentation with the auditability requirement on the task
card. Every document in this section is referenced from the Style Guide's audit
section so that a reviewer or auditor can trace a logged event back to the
documented behavior.

**Files:**
- `audit-trail.md` — what is logged at each pipeline stage (query received, security
  pre-check result, intent classification, retrieval scores, prompt sent to LLM,
  response generated, validation result, citation mapping, abstention triggers),
  log schema (JSON, fields defined in Style Guide), retention period, who can read
  logs, how logs are anonymized for PII (R003 mitigation 5)
- `pii-handling.md` — detection mechanism (Presidio or regex, from
  `component-specification.md` §3.1), what constitutes PII in banking context
  (account numbers, SSN, card numbers), redaction procedure, what is stored vs.
  not stored, how vectorized PII is treated (R003: "less retrievable" — documented
  honestly as a residual risk), no-real-data stance for v1
- `scope-enforcement.md` — how out-of-scope queries are detected (intent classifier,
  `FAQ_QUERY` vs `IRRELEVANT`), standard rejection messages (e.g., "I can't access
  individual account information."), what is logged when a scope violation is
  attempted, link to R004 mitigations
- `disclaimer.md` — "Not for production use" notice placement (README, UI sidebar,
  every API response footer), v1 scope limitation, v2 compliance path (R016
  mitigation 4: engage compliance before production)

---

### 8. Evaluation & Limitations

**Owner:** Scribe (after Sentinel verification passes)
**Status:** Planned
**Sources:** `component-specification.md` §9 (evaluation architecture, metrics),
`risk-analysis.md` R014, R015 (accepted limitations)

**Files:**
- `metrics.md` — the five metrics from §9.2 with targets:
  Recall@K (>0.8 @K=5), MRR (>0.7), Answer F1 (>0.6), Hallucination Rate (<0.05),
  Abstention Accuracy (>0.9); how each is computed; how to run the evaluation suite
- `test-datasets.md` — JSONL format `(question, expected_chunks, acceptable_answers)`,
  four categories (retrieval accuracy, answer relevance, hallucination detection,
  abstention correctness), how to extend the dataset
- `known-limitations.md` — v1 constraints honestly listed: single-user local, FAISS
  single-process, in-memory sessions (lost on restart), no PII in real-data mode
  is a residual risk, no production compliance, scanned-PDF OCR is a v2 feature
  (R015), scaling ceiling (R014 accepted by design), v2 migration path from
  `ROADMAP_SUMMARY.md` / `technology-rationale.md` §7

---

### 9. Decision Records (ADRs)

**Owner:** Scribe (records decisions; Archer owns the decisions themselves)
**Status:** Template ready; records written as decisions are ratified

**Files:**
- `adr-NNNN-template.md` — ADR template capturing: decision, status (proposed /
  accepted / superseded), context, alternatives considered, rationale, consequences,
  source references. Aligns with the `decision → rationale → relevant evidence →
  consequences` structure required by the Scribe charter.
- Decisions to record (from upstream artifacts):
  - ADR-0001: FAISS over PostgreSQL / Chroma (constraint: no Postgres)
  - ADR-0002: LangGraph single-workflow over multi-agent (constraint: no
    multi-agent)
  - ADR-0003: Standard RAG over CAG (constraint: no CAG)
  - ADR-0004: OpenAI-compatible LLM interface (provider-agnostic)
  - ADR-0005: all-MiniLM-L6-v2 for v1 embeddings (speed; upgrade path documented)
  - ADR-0006: Hybrid retrieval (dense + BM25 + RRF) as v1 default
  - ADR-0007: In-memory session store for v1 (accepted risk R007)
  - ADR-0008: File-based persistence (no Postgres; upgrade to SQLite v2)

---

## Status Conventions

Every documentation file carries a front-matter block:

```
**Version:** <semver>
**Status:** Planned | Draft | Current | Superseded
**Last Verified:** <date> against <commit / artifact>
**Sources:** <list of upstream artifacts>
```

- **Planned** — file is listed in this outline but not yet written, or written only
  against planned architecture that implementation has not yet caught up to.
- **Draft** — written but not yet verified against the running implementation.
- **Current** — verified against the implementation at the stated commit / date.
- **Superseded** — replaced; the replacement file is linked.

Scribe updates `Status: Current` only after verifying against code. A document
that drifts from implementation reverts to `Draft` until re-verified.

---

## Writing Order

Documentation is written in the same order Forge delivers modules, per the sprint
plan in `SPRINT_TASK_OUTLINE.md`:

1. **Sprint 0 →** `setup/prerequisites.md`, `setup/installation.md`,
   `setup/configuration.md` (after Config + LLM interface exist)
2. **Sprint 1 →** `setup/document-ingestion.md`, `runbook/reindexing.md`,
   `runbook/embedding-model-change.md` (after ingestion + FAISS persistence)
3. **Sprint 2 →** `api/chat-endpoint.md`, `user-guide/asking-questions.md`,
   `user-guide/understanding-citations.md`, `architecture/overview.md`
   (after LangGraph + grounded generation)
4. **Sprint 3 →** `user-guide/session-management.md`, `setup/running-locally.md`
   (after Streamlit UI + session management)
5. **Sprint 4 →** `runbook/*` (remaining), `evaluation/*`, `compliance/*`,
   `README.md` (after hardening + Sentinel verification)

ADR records are written as decisions are ratified, not in a final batch.

---

## Open Questions

These are gaps the current source artifacts do not answer. They are flagged here
rather than guessed at, per the Scribe charter ("identify the gap rather than
guessing"). Updated 2026-08-20 after implementation (t_1547ebb4):

1. **Research notes artifact (`research_notes.md`)** is referenced in the t_811b9295
   handoff metadata as an audit/compliance research deliverable but is not present
   in the workspace `/home/hari/Desktop/Banking/`. The compliance section is
   derived from the risk analysis and component specification instead. If the
   research notes exist elsewhere, they should be re-surfaced and cross-referenced
   from `docs/compliance/audit-trail.md`. **Still open.**
2. **Audit-log retention period** is not specified in any current artifact. R016
   mitigation 3 says "Document all queries (auditability)" but no retention duration
   is given. Furthermore, v1 does **not implement** a structured audit log at all
   (see `docs/compliance/audit-trail.md`). The retention decision must be made
   (likely by Archer or a compliance owner) before `audit-trail.md` can be marked
   fully Current, and structured logging must be implemented first.
   **Still open.**
3. **PII detection library** is listed as "Presidio (Microsoft) or regex patterns"
   — a choice, not a decision. **Resolved by the v1 implementation in favor of
   regex** (standard-library `re` patterns in `ingestion.py::PIIDetector`); see
   `docs/compliance/pii-handling.md`. Presidio remains a v2 option if coverage gaps
   bite. **Resolved for v1.**

Additional gaps surfaced during implementation-aligned documentation (see
`docs/evaluation/known-limitations.md` for the full list): no Streamlit UI (A1);
`/ingest` is a stub (A4); fusion is normalized-weighted, not RRF as documented (A3);
no query-side PII/injection/rate-limit despite config flags (B1–B3); `RAGWorkflow`
is not LangGraph (A2).

---

*End of Documentation Outline — Version 1.0*

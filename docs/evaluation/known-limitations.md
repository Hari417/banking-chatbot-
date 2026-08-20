# Known Limitations (v1)

**Version:** 1.0
**Status:** Current
**Last Verified:** 2026-08-20 against the implemented source under `src/`
**Sources:** `src/banking_rag/*.py`, `src/api.py`, `src/cli.py`, `config.yaml`, `risk-analysis.md`, `ROADMAP_SUMMARY.md`
**Owner:** Scribe

---

This file is the exhaustive, honest list of v1 constraints, accepted risks, and
divergences between the **implemented** system and the **planned** architecture. Each
item was verified against source code. Items are grouped: divergences (planned-but-not),
accepted risks, and genuine bugs.

See `docs/compliance/disclaimer.md` for the user-facing summary and `docs/compliance/` for the
security posture detail.

---

## A. Architecture divergences (planned vs. implemented)

### A1. No Streamlit UI
- **Plan:** `technology-rationale.md` / `component-specification.md` specify a Streamlit UI on port 8501; `config.yaml` has `presentation.streamlit_port: 8501` and `enable_streamlit: true`.
- **Actual:** No Streamlit code exists. Only the CLI (`src/cli.py`) and the FastAPI API (`src/api.py`) are implemented.
- **Impact:** There is no graphical human interface; users interact via terminal or HTTP.
- **Pointer:** `docs/setup/running-locally.md`, `docs/architecture/overview.md` §Front-ends.

### A2. RAG workflow is not LangGraph
- **Plan:** `rag_workflow.py` docstring and the architecture describe "LangGraph-based orchestration"; a "single LangGraph workflow" was a project constraint.
- **Actual:** No `langgraph` import. `RAGWorkflow` is a plain class with a sequential `run()` method. The "no multi-agent / single workflow" **constraint is satisfied in spirit** (one linear pipeline), but not via the LangGraph library.
- **Impact:** No graph visualization, no conditional edges, no checkpointing benefits. Functionally equivalent for v1.
- **Pointer:** `docs/architecture/overview.md` §RAG Workflow.

### A3. Retrieval uses weighted normalized fusion, not RRF
- **Plan:** `retrieval.py` docstring and the `_reciprocal_rank_fusion` method describe Reciprocal Rank Fusion (`1/(k+rank)`).
- **Actual:** `retrieve()` calls `_score_fusion`, which min-max normalizes dense/sparse scores and combines with hardcoded weights `0.7 * dense + 0.3 * sparse`. The RRF method is **dead code**.
- **Impact:** Fusion behavior differs from the documented RRF; tuning requires code changes (weights are not in `config.yaml`).
- **Pointer:** `docs/architecture/overview.md` §Retrieval, `docs/setup/troubleshooting.md`.

### A4. `/ingest` is a stub
- **Plan:** Ingest documents via `POST /ingest`.
- **Actual:** The endpoint returns a fixed placeholder (`document_id: doc_001, chunks_ingested: 1`) for every request. It does not call `DocumentIngestionPipeline`. Real ingestion is via Python only.
- **Impact:** API-driven ingestion is non-functional. The pipeline itself works fully.
- **Pointer:** `docs/api/ingest-endpoint.md`, `docs/setup/document-ingestion.md`.

### A5. `/config` is read-only; `/query` is an undocumented alias; `/sessions` was undocumented
- **Plan:** Outline listed `/config` as GET/POST.
- **Actual:** `/config` is GET-only. `/query` exists as an alias of `/chat`. `/sessions` (GET/DELETE) exists but was not in the outline.
- **Pointer:** `docs/api/overview.md`, `docs/api/config-endpoint.md`, `docs/api/sessions-endpoint.md`.

### A6. No streaming on `/chat`
- **Plan:** Architecture mentions streaming SSE responses.
- **Actual:** `LLMClient` supports streaming at the LLM layer, but `/chat` returns a single JSON response. Streaming is a v2 item.
- **Pointer:** `docs/api/chat-endpoint.md` §Streaming.

---

## B. Security & compliance gaps (config flags exist, behavior absent)

### B1. No query-side PII detection
- **Flag:** `security.pii_detection_enabled: true`.
- **Actual:** `PIIDetector` runs only during document ingestion (stage 4). User queries typed into `/chat` are never scanned for PII. A user pasting an account number is not blocked.
- **Risk:** R003 (PII leakage) mitigations 2–3 not implemented on the query path.
- **Pointer:** `docs/compliance/pii-handling.md`, `docs/compliance/scope-enforcement.md`.

### B2. No prompt-injection filter
- **Flag:** `security.prompt_injection_check_enabled: true` and `security.input_guard_enabled: true`.
- **Actual:** No input-side keyword/pattern filter runs. R002 mitigation 1 absent. Scope control relies on the system prompt + post-hoc abstention phrase scan.
- **Risk:** A scope-violating response that does not use the trigger phrases will reach the user.
- **Pointer:** `docs/compliance/scope-enforcement.md`, `docs/runbook/incident-response.md`.

### B3. No rate limiting
- **Flag:** `security.rate_limit_enabled: true`, `rate_limit_requests: 10`, `rate_limit_window: 60`.
- **Actual:** No rate limiter on the API or CLI. R002 mitigation 4 absent.
- **Pointer:** `docs/api/overview.md`, `docs/setup/configuration.md` §security.

### B4. `features.enable_transactions` is documentation-only
- **Actual:** Hardcoded `false`, but **no code reads it**. It is not an enforcement point; the real scope guard is the system prompt + `_should_abstain`. A bug removing the system prompt would not be caught by this flag.
- **Pointer:** `docs/compliance/scope-enforcement.md`.

### B5. No structured audit trail
- **Plan:** `STYLE_GUIDE.md` §2 specifies JSON logging, event taxonomy, `request_id` correlation.
- **Actual:** Stdlib text logs to stderr only. No `request_id`, no events, no retention enforcement. R016 mitigation 3 only partially satisfied (no query-level trail exists).
- **Pointer:** `docs/compliance/audit-trail.md`, `docs/runbook/log-rotation-and-retention.md`.

### B6. `/health` returns hardcoded probes
- **Actual:** `vector_store_ready` and `model_available` are always `true`. The endpoint does not verify the FAISS index loaded or the LLM endpoint is reachable.
- **Impact:** A 200 does not guarantee the system can answer queries.
- **Pointer:** `docs/api/health-endpoint.md`.

### B7. Open audit-log retention decision
- **Actual:** R016 mitigation 3 asks for a retention period; none decided. Moot without structured logging, but must be decided before v2 carries real data.
- **Pointer:** `docs/compliance/audit-trail.md`, `docs/DOCUMENTATION_OUTLINE.md` open questions.

---

## C. Functional gaps

### C1. Non-reject PII is not auto-redacted
- **Actual:** `stage_4_pii_validation` checks `pii_result.redacted_content`, but `PIIDetector.detect()` never sets it. Email/phone PII passes into the index unredacted. `PIIDetector.redact()` exists but is not invoked by the pipeline.
- **Pointer:** `docs/setup/document-ingestion.md`, `docs/compliance/pii-handling.md`.

### C2. Sessions are not multi-turn
- **Actual:** `/sessions/{id}` stores a transcript, but `RAGWorkflow.run()` takes only the current query — prior turns are not fed into retrieval or the prompt. Each `/chat` call is independent.
- **Impact:** The bot has no conversational memory; follow-up questions like "tell me more" retrieve/generate without the earlier context.
- **Pointer:** `docs/api/sessions-endpoint.md`.

### C3. Session TTL / memory cap / persistence all ignored
- **Flags:** `session.ttl_minutes`, `session.memory_limit`, `session.persistence`.
- **Actual:** The API uses an unbounded in-memory dict with no TTL sweeper and no SQLite persistence. R007 accepted for v1.
- **Pointer:** `docs/runbook/session-cleanup.md`, `docs/api/sessions-endpoint.md`.

### C4. Grounding validation is a lexical heuristic
- **Actual:** `_validate_grounding` computes `overlap / len(response_tokens) > 0.2` plus a banned-phrase list and a >500-word cap. Not a semantic grounded-claim check.
- **Impact:** Can both miss subtle hallucinations (fluent fabrication with vocabulary overlap) and false-positive on legitimate answers. `metadata.grounded` should not be treated as a strong signal.
- **Risk:** R001 (hallucination) mitigation 3 is weak.
- **Pointer:** `docs/architecture/overview.md` §Query Flow, `docs/compliance/scope-enforcement.md`.

### C5. Sparse (BM25) retrieval optional and silent
- **Actual:** `rank-bm25` is commented out in `requirements.txt`. If not installed, `HybridRetriever` logs a warning and degrades to dense-only. Users may not notice.
- **Pointer:** `docs/setup/installation.md`, `docs/setup/troubleshooting.md`.

### C6. `score_threshold` / `rerank_enabled` / `rerank_model` unused
- **Actual:** `retrieval.score_threshold`, `retrieval.rerank_enabled`, `retrieval.rerank_model` are in `config.yaml` but `HybridRetriever` does not apply a threshold or invoke a reranker. v2 placeholders.
- **Pointer:** `docs/setup/configuration.md` §retrieval.

### C7. No FAISS index integrity verification
- **Actual:** No SHA-256 checksum stored/verified at load (R008 "Partially Mitigated"). `delete_chunk` removes metadata only, not the vector (append-only index). Corruption detected only on request failure.
- **Pointer:** `docs/runbook/index-corruption-recovery.md`, `docs/runbook/reindexing.md`.

### C8. CORS fully open on the API
- **Actual:** `allow_origins=["*"]`, all methods/headers. Fine for local use; unsafe for any shared exposure.
- **Pointer:** `docs/api/overview.md`, `docs/compliance/disclaimer.md`.

### C9. No API authentication
- **Actual:** No authn/authz on any endpoint. Any client can read/delete any session. Unacceptable beyond local single-user.
- **Pointer:** `docs/compliance/disclaimer.md`.

### C10. Streaming parser uses `eval()`
- **Actual:** `LLMClient._stream_chat` parses SSE payloads via `eval(data)`. Unsafe if pointed at an untrusted endpoint; also brittle for non-Strict-OpenAI SSE framing. Prefer non-streaming mode in v1.
- **Pointer:** `docs/setup/troubleshooting.md` LLM section, `docs/runbook/llm-provider-swap.md`.

### C11. `Ollama HOST`/`ollama_model` confusion
- **Actual:** `LLMClient` sends `llm.model` (not `ollama_model`) to Ollama. The `ollama_model` field is vestigial for the client path. Misconfiguration leads to "model not found" from Ollama.
- **Pointer:** `docs/setup/configuration.md` §llm, `docs/runbook/llm-provider-swap.md`.

---

## D. Bugs (minor)

### D1. `ingested_at` stores the model name, not a timestamp
- **Location:** `ingestion.py::stage_5_metadata_enrichment`: `chunk.metadata['ingested_at'] = str(self.config.embedding.model)`.
- Copy-paste bug; `ingested_at` is unusable for ordering. Fix to `datetime.now(timezone.utc).isoformat()` in a follow-up.

### D2. `tests/verify.py` hardcodes `/home/hari/Desktop/Banking/src`
- Not portable to other clone locations. Use `PYTHONPATH=src` or edit the path.

### D3. `routing_number` false-positive risk for `account_number`
- `\b\d{8,20}\b` flags any 8–20 digit number as account PII. Routing numbers (9 digits) and some aggregate figures will be quarantined. Over-inclusive on the safe side, but expect some good chunks to be rejected from numeric-heavy documents.

---

## E. Accepted v1 scope (by design, not bugs)

- **Single-user, local** — no multi-tenant isolation, no auth, no horizontal scaling.
- **FAISS in-process** — `IndexFlatIP` brute-force on one machine; no distributed GPU search.
- **No real customer data** — only `sample_data.py` or sanitized public FAQs.
- **No scanned-PDF OCR** — `PyPDF2` extracts the text layer only; image PDFs yield no text (R015 accepted).
- **No production compliance certification** — engage compliance before any deployment (R016).
- **No evaluation harness shipped** — `metrics.md` / `test-datasets.md` in the outline are planned but not implemented; no Recall@K / MRR / Answer-F1 / Hallucination-Rate / Abstention-Accuracy suite exists in v1.

See `ROADMAP_SUMMARY.md` for the v1 → v2 migration path addressing the security
(B1–B5), functional (C1–C7), and compliance (B7) gaps above.

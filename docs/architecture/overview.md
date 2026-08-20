# Architecture Overview

**Version:** 1.0
**Status:** Current
**Last Verified:** 2026-08-20 against the implemented source under `src/banking_rag/`
**Sources:** `ARCHITECTURE.md`, `component-specification.md`, `src/banking_rag/*.py`, `src/api.py`, `src/cli.py`, `config.yaml`
**Owner:** Scribe

---

## Purpose

This document is a narrative walkthrough of the **implemented** Banking RAG Chatbot v1.
It complements — and where necessary corrects — the upstream `ARCHITECTURE.md`, which was
written before implementation. Where the two disagree, the code is authoritative and the
disagreement is flagged inline as a **Divergence**.

---

## System at a Glance

The system is a **local-first, FAQ-only** Retrieval-Augmented Generation chatbot for
banking product and policy questions. It runs as a Python package (`banking_rag`)
with two front-ends: a CLI (`src/cli.py`) and a FastAPI REST API (`src/api.py`).

```
                 ┌─────────────────────────────────────────┐
   User ────►    │  CLI (src/cli.py)   or   API (src/api.py)│
                 └────────────────────┬────────────────────┘
                                      │  query
                       ┌──────────────▼──────────────┐
                       │     RAGWorkflow.run()        │  (src/banking_rag/rag_workflow.py)
                       │  1. embed query              │
                       │  2. retrieve docs            │
                       │  3. build context            │
                       │  4. build prompt             │
                       │  5. call LLM                 │
                       │  6. validate grounding       │
                       │  7. abstention check         │
                       │  8. generate citations        │
                       └───┬──────────┬─────────┬──────┘
                           │          │         │
              ┌────────────▼──┐ ┌─────▼─────┐ ┌─▼────────────┐
              │ EmbeddingModel │ │Retriever  │ │  LLMClient    │
              │ (local/OpenAI) │ │(hybrid)   │ │ OpenAI/Ollama │
              └────────────────┘ └─────┬─────┘ └───────────────┘
                                       │ dense + sparse
                                ┌──────▼──────┐
                                │  VectorStore│  FAISS index + metadata JSON
                                │  (FAISS)    │  persisted to ./data/index/
                                └─────────────┘
```

Ingestion is a separate offline path that loads documents, chunks them, validates for
PII, embeds, and persists to the FAISS index (see [Ingestion flow](#ingestion-flow)).

---

## Component Responsibilities

Each component below is one module under `src/banking_rag/`.

### Configuration — `config.py`
Loads `config.yaml` into a tree of Pydantic `BaseModel` sub-configs
(`LLMConfig`, `EmbeddingConfig`, `VectorStoreConfig`, `RetrievalConfig`,
`SecurityConfig`, `ChunkingConfig`, `SessionConfig`, `FeatureConfig`) aggregated by the
`AppConfig` dataclass. A process-global singleton is exposed via `get_config()` /
`reload_config()`. If `config.yaml` is missing, defaults are returned.

### LLM Interface — `llm.py`
`LLMClient` wraps OpenAI-compatible `/chat/completions` endpoints. It supports three
providers declared in `llm.provider`:
- `openai` — calls `api_base` with a bearer token from the env var named by `api_key_env`.
- `openai_compatible` — same wire format, custom `api_base`.
- `ollama` — calls `ollama_base_url` (Ollama exposes an OpenAI-compatible endpoint).

Both non-streaming and streaming (`stream=True`) chat are supported. A `MockLLMClient`
exists for tests. **Note:** `generate()` hardcodes the system message `"You are a
helpful banking assistant."`; the full banking system prompt with scope/grounding rules
is applied only inside `RAGWorkflow._build_prompt()`.

### Embeddings — `embeddings.py`
`EmbeddingModel` generates query and chunk embeddings. Providers:
- `local` — `sentence-transformers` (`all-MiniLM-L6-v2` by default, 384 dims), loaded
  eagerly on construction.
- `openai` / `openai_compatible` — calls `<api_base>/embeddings` per text.

Batch embedding is supported for the local provider (sized by `embedding.batch_size`);
the API providers loop one request per text. A `MockEmbeddingModel` is used in tests.

### Chunking — `chunking.py`
`DocumentChunker` splits text into `Document` chunks. Three strategies:
- `recursive` — split by paragraphs, then sentences, then words/chars for oversized
  paragraphs, with approximate overlap.
- `faq_preserved` — each Q/A pair becomes one chunk; oversize pairs fall back to
  recursive.
- `table_aware` — Markdown pipe-tables and ASCII tables kept as whole chunks.

### Vector Store — `vector_store.py`
`VectorStore` wraps FAISS. Index types: `IndexFlatIP` (default, brute-force inner
product) and `IndexIVFFlat`. The index, a chunk-metadata JSON map, and a
document-registry JSON are persisted under `vector_store.persist_path` /
`metadata_path` / `registry_path` (default `./data/index/`). `faiss` and `numpy` are
imported lazily so the package imports without them; `add_chunks` /
`search` / `delete_chunk` / `clear` are the main operations.

### Retrieval — `retrieval.py`
`HybridRetriever` runs dense retrieval (`VectorStore.search`) and, when `rank-bm25` is
installed, sparse BM25 retrieval over the dense candidates. Scores are combined and
truncated to `retrieval.final_k`.
- **Divergence:** The docstring and the `_reciprocal_rank_fusion` method describe RRF,
  but the path actually exercised by `retrieve()` is `_score_fusion`, which uses
  **min-max normalized weighted combination** (hardcoded `0.7 * dense + 0.3 * sparse`).
  RRF is dead code as shipped.
- BM25 is optional. If `rank-bm25` is not installed, retrieval silently degrades to
  dense-only.

### RAG Workflow — `rag_workflow.py`
`RAGWorkflow` orchestrates the per-query pipeline (see [Query flow](#query-flow)). The
`RAGState` `TypedDict` carries `query`, `query_embedding`, `retrieved_docs`, `context`,
`messages`, `response`, `citations`, `confidence`, `abstained`, `metadata`.
- **Divergence:** The module docstring says it "Implements LangGraph-based
  orchestration," but no LangGraph is imported or used. The workflow is a plain Python
  class with a sequential `run()` method. The "single LangGraph workflow" constraint is
  satisfied in spirit (one linear pipeline, no multi-agent) but not via the LangGraph
  library.

### Ingestion — `ingestion.py`
`DocumentIngestionPipeline` is an 8-stage offline pipeline (see
[Ingestion flow](#ingestion-flow)) that produces the FAISS index. It also contains
`PIIDetector`, `DocumentLoader` (txt/md/pdf/html), and the `PIIResult` /
`IngestionResult` dataclasses.

### Front-ends — `src/cli.py`, `src/api.py`
- **CLI** — `python3 src/cli.py chat` (interactive REPL) or `python3 src/cli.py query
  "<q>"` (single shot, optional `--json`). Both accept `--mock` to use the mock
  components.
- **API** — FastAPI app exposing the endpoints documented under `docs/api/`.
  - **Divergence:** The architecture specifies a Streamlit UI. **No Streamlit UI is
    implemented.** Only CLI and API exist.

---

## Query Flow

For a single `/chat` request or CLI query, `RAGWorkflow.run(query)` executes:

1. **Embed query** — `_embed_query()` calls `EmbeddingModel.generate(query)`.
2. **Retrieve** — `_retrieve()` calls `HybridRetriever.retrieve(query, query_embedding)`.
   If no documents are retrieved, the workflow short-circuits to an abstention response
   and returns early.
3. **Build context** — `_build_context()` formats each retrieved document as
   `DOCUMENT [i]: <content>`.
4. **Build prompt** — `_build_prompt()` assembles the static system prompt (banking
   assistant rules + context markers + user query). The system prompt enforces:
   answer only from context, say "I don't know" when uncertain, cite sources, never
   provide transactional/personal-account services.
5. **Generate** — `LLMClient.generate(prompt)` returns the raw LLM response.
6. **Validate grounding** — `_validate_grounding()` returns `(is_grounded, confidence)`
   using a **string-token overlap heuristic**: it flags known ungrounded phrases
   ("based on my knowledge", "I believe", …), caps overlong responses (>500 words),
   and computes `overlap / len(response_tokens) > 0.2` as a grounding score.
   - **Divergence:** This is a lexical proxy, not a semantic grounding check. It will
     both miss subtle hallucinations and false-positive on vocabulary overlap. It is
     documented honestly as a v1 limitation.
7. **Abstention check** — `_should_abstain()` scans the response for triggers
   (`"i don't know"`, `"transactional"`, `"account-specific"`, `"personal
   information"`, …). If matched, the response is replaced with a fixed scope-refusal
   message, `abstained=True`, `confidence=0.0`, and the workflow returns early.
8. **Citations** — `_generate_citations()` emits `[i]: <source> (chunk: <chunk_id>)`
   for each retrieved doc.
9. **Metadata** — records embedding model, retrieval strategy, doc counts, response
   token count, confidence, and `grounded` flag.

On any exception, the workflow returns a generic error message with `abstained=True`.

- **Divergence:** The planned architecture puts a security pre-check (PII detection +
  injection filter + rate limiting) **before** retrieval on the query path. In the
  implementation, **no query-side PII detection, injection filter, or rate limiter
  runs**. `config.yaml` exposes `security.*` flags, but they are not read on the query
  path. Scope control relies solely on the system prompt and the post-hoc abstention
  trigger scan. See `docs/compliance/scope-enforcement.md`.

---

## Ingestion Flow

`DocumentIngestionPipeline.ingest_file(path)` runs the 8 stages:

1. **Format detection** — `stage_1_format_detection()` maps the file extension to a
   format (`txt`, `markdown`, `pdf`, `html`, `docx`; `docx` falls back to the text
   loader).
2. **Content extraction** — `stage_2_content_extraction()` delegates to
   `DocumentLoader` (`PyPDF2` for PDF, `BeautifulSoup` for HTML, plain read for
   txt/markdown). Missing optional libraries raise `ImportError`.
3. **Chunking** — `stage_3_chunking()` uses the strategy in `chunking.strategy`
   (default `recursive`).
4. **PII validation** — `stage_4_pii_validation()` runs `PIIDetector.detect()` on each
   chunk. Chunks containing reject-list PII (`ssn`, `account_number`, `credit_card`)
   are written to `./data/quarantine/` and excluded from the index. Non-reject PII
   (e.g., email, phone) is accept-listed; redaction is available
   (`PIIDetector.redact()`) but **not automatically applied** in stage 4 — only set
   on the chunk when `pii_result.redacted_content` is non-null, which `detect()` does
   not populate. See `docs/compliance/pii-handling.md`.
5. **Metadata enrichment** — adds `token_count`, `embedding_model`, `ingested_at`,
   `format`.
6. **Embedding generation** — `stage_6_embedding_generation()` batch-embeds chunk text.
7. **Persistence** — `stage_7_persistence()` calls `VectorStore.add_chunks()`,
   persisting the FAISS index, metadata JSON, and document registry.
8. **Validation** — `stage_8_validation()` confirms chunk count and chunk presence.

`ingest_directory()` walks a directory for `.txt/.md/.pdf/.html`.

- **Divergence:** The `/ingest` REST endpoint does **not** invoke this pipeline. It
  returns a fixed placeholder response (see `docs/api/ingest-endpoint.md`). To ingest
  documents you must instantiate `DocumentIngestionPipeline` in Python (or run
  `src/banking_rag/ingestion.py` as a script).

---

## Integration Points

| Boundary | What connects | Notes |
|----------|---------------|-------|
| LLM provider | OpenAI / OpenAI-compatible / Ollama HTTP `/chat/completions` | Provider-agnostic via `LLMClient`; switch in `config.yaml` |
| Embedding provider | `sentence-transformers` (local) or OpenAI-compatible embeddings API | Switch in `config.yaml` |
| Vector store | FAISS index file + JSON metadata on local disk | No external DB |
| Document sources | Local files (txt/md/pdf/html) via `DocumentIngestionPipeline` | No web crawlers |
| Session store | In-process Python dict in `src/api.py` | Lost on restart; no TTL sweeper implemented |

---

## Security Boundaries

The system enforces a **FAQ-only** scope through, in order of strength:

1. **System prompt** — explicit rules: answer only from provided context, refuse
   transactional/personal-account requests, cite sources.
2. **Post-hoc abstention trigger scan** — `_should_abstain()` rewrites responses
   containing scope-violation phrases to a fixed refusal.
3. **Ingestion-time PII rejection** — `PIIDetector` quarantines chunks containing
   `ssn`/`account_number`/`credit_card` before they enter the index.
4. **Feature flag** — `features.enable_transactions: false` in `config.yaml`
   (hardcoded false; **no code reads it**, so it is documentation-only, not an
   enforcement point — see `docs/compliance/scope-enforcement.md`).

**Not implemented in v1 (despite config flags):** query-side PII detection, prompt
injection filtering, request rate limiting, structured/JSON audit logging. These are
documented as accepted limitations in `docs/evaluation/known-limitations.md` and the
`docs/compliance/` cluster.

---

## Scalability Boundaries and v1 → v2 Path

v1 is explicitly a **local, single-user prototype**:

- FAISS runs in-process (single-machine, no distribution).
- Sessions are in-memory and lost on process restart (no SQLite persistence — see
  R007).
- No concurrent-request hardening (the API is async but shares one workflow instance).
- No production compliance, no real customer data. Use only the sample data in
  `sample_data.py`.

The v2 migration path (from `ROADMAP_SUMMARY.md` / `technology-rationale.md`) includes:
SQLite-backed sessions, a real query-side security layer, structured JSON audit logging,
a genuine grounding validator, and a Streamlit UI. None of these are present in v1.

---

## Cross-references

- Upstream planned architecture: `ARCHITECTURE.md`
- Component-level spec: `component-specification.md`
- Risk register: `risk-analysis.md` (R001 hallucination, R002 injection, R003 PII,
  R004 scope, R005–R009 retrieval/perf/session/FAISS/embedding, R016 regulatory)
- API details: `docs/api/`
- Setup: `docs/setup/`
- Limitations (exhaustive): `docs/evaluation/known-limitations.md`
- Compliance posture: `docs/compliance/`

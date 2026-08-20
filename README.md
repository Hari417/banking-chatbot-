# Banking RAG Chatbot

A local-first, FAQ-only Retrieval-Augmented Generation chatbot for general banking
questions. It answers from a loaded knowledge base of banking policies, products, fees,
loans, interest rates, and procedures — using FAISS for local vector search and an
OpenAI-compatible or Ollama LLM for generation.

> **Prototype — Not for production.** See `docs/compliance/disclaimer.md`. FAQ/knowledge
> system only; never transactional. No query-side PII protection, no structured audit
> trail, no auth. Do not feed it real customer data.

---

## What this is (and is not)

- **In scope:** general banking FAQs, policies, products, fees, loans, eligibility,
  procedures, interest rates, penalties, repayment policies.
- **Out of scope (refused):** account balances, transactions, card operations, real
  customer authentication, private customer data, any transactional banking.
- **Local-first:** FAISS on disk, no PostgreSQL, no external vector DB.
- **Two interfaces shipped in v1:** a CLI (`src/cli.py`) and a FastAPI REST API
  (`src/api.py`). **No Streamlit UI** (see `docs/evaluation/known-limitations.md`).

## Quick start

```bash
# 1. venv + deps (see docs/setup/installation.md)
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY="sk-..."          # or use Ollama — see config.yaml

# 2. Smoke test (mock path, no key needed)
python3 tests/verify.py                 # expect: ALL TESTS PASSED!

# 3. (Optional) ingest documents — see docs/setup/document-ingestion.md
#    Without ingestion, every query abstains with "no documents found".

# 4. Run it
python3 src/cli.py chat                 # interactive CLI
python3 src/api.py                      # REST API on http://localhost:8000
```

Example query via the API:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What are your banking hours?"}'
```

## Architecture (high level)

```
CLI / API  →  RAGWorkflow.run()  →  embed → retrieve (dense + sparse) → build context
                                   → build prompt → LLM → validate grounding → abstain check → cite
        Retrieval uses FAISS (IndexFlatIP) + optional BM25 (rank-bm25)
```

For the full narrative, including divergences from the upstream `ARCHITECTURE.md`, see
[`docs/architecture/overview.md`](docs/architecture/overview.md).

## Tech stack

| Layer | Choice | Swap path |
|-------|--------|-----------|
| LLM | OpenAI / OpenAI-compatible / Ollama (HTTP) | `llm.provider` in `config.yaml` |
| Embeddings | `all-MiniLM-L6-v2` (local, 384d) or OpenAI API | `embedding.provider` |
| Vector store | FAISS (`IndexFlatIP` / `IndexIVFFlat`) on local disk | — |
| Retrieval | hybrid dense + optional BM25 (fused, normalized weighted) | — |
| Workflow | single linear `RAGWorkflow` (LangGraph absent in v1) | — |
| API | FastAPI | — |

## Project structure

```
Banking/
├── config.yaml              #.configuration
├── requirements.txt
├── sample_data.py           # sample FAQ/policy/product/loan data
├── src/
│   ├── banking_rag/         # core package
│   │   ├── config.py llm.py embeddings.py chunking.py
│   │   ├── vector_store.py retrieval.py rag_workflow.py ingestion.py
│   ├── cli.py               # CLI interface
│   └── api.py               # FastAPI REST API
├── tests/                   # verify.py (mock smoke test) + test_rag.py
└── docs/                    # full documentation (below)
```

## Documentation map

| You want to… | Read |
|--------------|------|
| Understand the system | `docs/architecture/overview.md` |
| Set it up | `docs/setup/prerequisites.md` → `installation.md` → `configuration.md` → `running-locally.md` |
| Load documents | `docs/setup/document-ingestion.md` (note: the `/ingest` API is a stub) |
| Use the API | `docs/api/overview.md` and per-endpoint docs under `docs/api/` |
| Ask questions well | `docs/user-guide/asking-questions.md`, `understanding-citations.md` |
| Know what it won't answer | `docs/user-guide/limitations-and-scope.md` |
| Operate / maintain it | `docs/runbook/README.md` and runbooks under `docs/runbook/` |
| Understand security/compliance posture | `docs/compliance/` (scope-enforcement, pii-handling, audit-trail, disclaimer) |
| See v1's gaps honestly | `docs/evaluation/known-limitations.md` |
| Standards (comments/logs/changes) | `docs/STYLE_GUIDE.md` |
| Documentation index | `docs/DOCUMENTATION_OUTLINE.md` |

## Security & limitations (summary)

v1 enforces FAQ-only scope via the **system prompt** and a **post-hoc abstention phrase
scan**, plus **ingestion-time PII rejection** (regex) for `ssn`/`credit_card`/
`account_number`. The following are **declared in `config.yaml` but not implemented** and
are accepted v1 limitations (full list in `docs/evaluation/known-limitations.md`):

- No query-side PII detection or redaction.
- No prompt-injection input filter.
- No request rate limiting.
- No structured/JSON audit log (`request_id`, event taxonomy).
- Grounding validation is a lexical token-overlap heuristic, not semantic.
- `/ingest` REST endpoint is a stub — use the Python ingestion pipeline.
- Sessions are in-memory and not multi-turn; lost on restart.

## Configuration

Key `config.yaml` sections: `llm`, `embedding`, `vector_store`, `retrieval`, `security`,
`chunking`, `session`, `features`. Every field is documented in
`docs/setup/configuration.md`. Environment overrides: `OPENAI_API_KEY`,
`BANKING_RAG_CONFIG`, `BANKING_RAG_MOCK`, `BANKING_RAG_API_HOST`, `BANKING_RAG_API_PORT`,
`BANKING_RAG_DEBUG`.

## Testing

```bash
python3 tests/verify.py            # mock-path smoke test (no key, no model)
python3 -m pytest tests/ -v         # full suite (needs pytest)
```

> `tests/verify.py` hardcodes `/home/hari/Desktop/Banking/src` in `sys.path`; if you
> cloned elsewhere, edit that line or run with `PYTHONPATH=src`. See `docs/setup/troubleshooting.md`.

## License

MIT License — see `LICENSE` for details (no `LICENSE` file shipped in v1; the upstream
README references one).

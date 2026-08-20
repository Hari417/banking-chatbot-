# AGENTS.md — Banking RAG Chatbot

## Quick Commands

```bash
# Smoke test (no key needed)
python3 tests/verify.py

# Full test suite
python3 -m pytest tests/ -v

# Run CLI
python3 src/cli.py chat
python3 src/cli.py query "What are your banking hours?" --json

# Run API
python3 src/api.py
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What are your banking hours?"}'

# Mock mode (no LLM/embeddings needed)
BANKING_RAG_MOCK=true python3 src/api.py
python3 src/cli.py chat --mock
```

## Critical Gotchas

- `tests/verify.py` hardcodes `/home/hari/Desktop/Banking/src` in `sys.path` (line 5). If cloned elsewhere, use `PYTHONPATH=src` or edit that line.
- `config.yaml` sets `vector_store.persist_path` to an absolute path `/home/hari/Desktop/Banking/data/index/faiss.index`. This breaks on other machines — override via env or edit `config.yaml`.
- The `.env` file contains dummy API keys (`sk-1234...`). Never use these for real OpenAI calls. Set `OPENAI_API_KEY` in your shell.
- `rank-bm25` is commented out in `requirements.txt`. Sparse retrieval silently degrades to dense-only if not installed.
- The `/ingest` endpoint is a **stub** — it returns fixed placeholder data and never calls `DocumentIngestionPipeline`. Use Python ingestion directly.
- `features.enable_transactions: false` in `config.yaml` is documentation-only — no code reads it. The real scope guard is the system prompt + `_should_abstain`.
- Ollama uses `llm.model` (not `llm.ollama_model`) when calling Ollama. Misconfiguration causes "model not found".

## Architecture

```
src/
├── banking_rag/       # Core package (config, llm, embeddings, chunking, vector_store, retrieval, rag_workflow, ingestion)
├── cli.py             # CLI interface (argparse, subcommands: chat, query)
└── api.py             # FastAPI REST API (uvicorn on port 8000)

tests/
├── verify.py          # Mock-path smoke test (no key/model needed)
└── test_rag.py        # Full pytest suite
```

**Flow:** CLI/API → `RAGWorkflow.run()` → embed → retrieve (dense + optional BM25) → context assembly → LLM → grounding validation → abstain check → cite

**RAG pipeline is NOT LangGraph** — `RAGWorkflow` is a plain class with sequential `run()`. No graph, no conditional edges.

## Testing

- `tests/verify.py` is the safe fast-path — uses `Mock*` classes, no model download, no API key.
- `test_rag.py` uses `unittest.mock.patch` for LLM calls but creates real FAISS indexes in `./data/test_vector_store/`. Cleaned between tests.
- No lint/typecheck tooling is configured in the repo.

## Config & Environment

- `config.yaml` — single source of truth for all settings. Loaded by `banking_rag.config.load_config()`.
- Env overrides: `OPENAI_API_KEY`, `BANKING_RAG_CONFIG`, `BANKING_RAG_MOCK`, `BANKING_RAG_API_HOST`, `BANKING_RAG_API_PORT`, `BANKING_RAG_DEBUG`.
- Default LLM: `ollama` provider, `qwen3:4b` model. Default embedding: `all-MiniLM-L6-v2` (local, 384d).

## Scope Rules

This is an **FAQ-only** chatbot. It must refuse:
- Account balances, transactions, card operations
- Real customer authentication, private customer data
- Anything transactional

Enforced by: system prompt + post-hoc abstention phrase scan in `_should_abstain`. No query-side PII detection, no prompt-injection filter, no rate limiting — these are declared config flags but not implemented in v1.

## v1 Known Limitations (abbreviated)

- No query-side PII detection or redaction
- No prompt-injection input filter  
- No rate limiting
- No structured audit trail (JSON logging not implemented)
- Grounding validation is lexical token-overlap heuristic, not semantic
- Sessions are in-memory, not multi-turn, lost on restart
- `/health` returns hardcoded `true` for all probes
- No API authentication, CORS wide open (`*`)

Full list: `docs/evaluation/known-limitations.md`

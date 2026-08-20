# Prerequisites

**Version:** 1.0
**Status:** Current
**Last Verified:** 2026-08-20 against `requirements.txt`, `config.yaml`, `src/`
**Sources:** `requirements.txt`, `config.yaml`, `technology-rationale.md`
**Owner:** Scribe

---

## Audience

This guide is for **developers and operators** setting up the Banking RAG Chatbot on a
single machine. v1 is a local-first prototype; there is no managed/cloud deployment mode.

---

## Operating system

- **Linux** (tested), **macOS**, or **Windows**.
- FAISS (`faiss-cpu`) and `sentence-transformers` work on all three, but Windows users
  should prefer a Conda/WSL2 environment for `faiss-cpu` wheel availability.

## Python

- **Python 3.9 or newer.** The codebase uses `from typing import ...` constructs and
  Pydantic v2; it has not been tested below 3.9.
- On systems with PEP 668 (Debian/Ubuntu 24.04+), do not install into the system
  interpreter. Use a **virtualenv** or **uv** (see `installation.md`).

## Hardware

- CPU-only inference is the default. The local embedding model
  (`all-MiniLM-L6-v2`, ~90 MB) runs on commodity CPUs.
- RAM: ~2 GB free is comfortable for small corpora. FAISS `IndexFlatIP` holds the
  full index in memory.
- Disk: ~1.5 GB for the venv including the embedding model download; plus space for
  your index and quarantine folder.

## LLM backend (choose one)

You need exactly one of:

| Option | What you need | Config setting |
|--------|---------------|----------------|
| OpenAI API | An `OPENAI_API_KEY` env var; network egress to `api.openai.com` | `llm.provider: openai` |
| OpenAI-compatible endpoint | A base URL + optional bearer token | `llm.provider: openai_compatible`, `llm.api_base`, `llm.api_key_env` |
| Local LLM via Ollama | [Ollama](https://ollama.com) installed and a pulled model (e.g. `ollama pull llama3`) | `llm.provider: ollama`, `llm.ollama_base_url`, `llm.ollama_model` |

The default `config.yaml` ships with `llm.provider: openai` and `llm.model: gpt-4o-mini`.

## Optional dependencies

The following are **not** required for the default install or for the mock test path,
but enable features you may want:

| Library | Enables | Install |
|---------|---------|---------|
| `rank-bm25` | Sparse (BM25) retrieval — without it, retrieval silently degrades to dense-only | `pip install rank-bm25` |
| `PyPDF2` | PDF document loading during ingestion | `pip install PyPDF2` |
| `beautifulsoup4` | HTML document loading during ingestion | `pip install beautifulsoup4` |
| `fastapi` + `uvicorn` | The REST API server | `pip install fastapi uvicorn` |
| `pytest` | The test suite | `pip install pytest` |

> **Note:** `fastapi`, `uvicorn`, `rank-bm25`, `PyPDF2`, `beautifulsoup4`, and `pytest`
> are **commented out** in `requirements.txt`. Uncomment the lines you need or install
> individually. The core package (`banking_rag`) imports without them.

## What you do NOT need

- No PostgreSQL or any external database. The store is FAISS on local disk.
- No Streamlit. The architecture mentions a Streamlit UI, but **v1 does not implement
  one**. Use the CLI or the API.
- No GPU (CPU inference works for the default embedding model).
- No real banking data. v1 is FAQ-only and uses the sample data in `sample_data.py`.

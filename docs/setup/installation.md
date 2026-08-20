# Installation

**Version:** 1.0
**Status:** Current
**Last Verified:** 2026-08-20 against `requirements.txt`, `config.yaml`, `src/`
**Sources:** `requirements.txt`, `technology-rationale.md`, `MODULE_BREAKDOWN.md`
**Owner:** Scribe

---

## 1. Clone / locate the project

The workspace is the `Banking/` directory. If you are reading this in-repo, you are
already there. Otherwise:

```bash
git clone <repo-url> Banking
cd Banking
```

## 2. Create and activate a virtual environment

Avoid installing into the system interpreter (PEP 668 on modern Debian/Ubuntu). Use
either `venv` or `uv`.

**Option A — stdlib `venv`:**

```bash
python3 -m venv .venv
source .venv/bin/activate        # Linux / macOS
# .venv\Scripts\activate         # Windows
```

**Option B — `uv` (faster, smaller):**

```bash
uv venv .venv
source .venv/bin/activate
```

Verify the interpreter is the venv's:

```bash
which python3        # should point inside .venv
python3 --version    # 3.9+
```

## 3. Install core dependencies

```bash
pip install -r requirements.txt
```

Core installs: `pyyaml`, `pydantic>=2.0`, `requests`, `sentence-transformers>=2.2.0`,
`faiss-cpu>=1.7.4`, `numpy>=1.24.0`.

> **Disk size:** the embedding model download plus `sentence-transformers` /
> `faiss-cpu` / `numpy` / torch-CPU bring the venv to **~1.5 GB**. Plan disk accordingly.

## 4. Install optional dependencies you need

`requirements.txt` ships the optional dependencies commented out. Uncomment and reinstall,
or install directly:

```bash
# Sparse retrieval (enables BM25 hybrid search):
pip install rank-bm25

# Document ingestion from PDF / HTML:
pip install PyPDF2 beautifulsoup4

# REST API server:
pip install fastapi uvicorn

# Test suite:
pip install pytest
```

## 5. Set environment variables

The only commonly-required secret is the OpenAI API key (only if
`llm.provider: openai`):

```bash
export OPENAI_API_KEY="sk-..."
```

For Ollama, no key is required; instead ensure the Ollama daemon is running and the
model is pulled:

```bash
ollama serve            # if not already running
ollama pull llama3      # or whichever model you configured
```

For an OpenAI-compatible endpoint, set whatever env var `llm.api_key_env` names (default
`OPENAI_API_KEY`) and set `llm.api_base` in `config.yaml`.

## 6. Verify the install

Run the mock-path verification script — it exercises every module against mock
implementations and requires **no API key and no model download**:

```bash
python3 tests/verify.py
```

Expected: seven `PASS` lines ending in `ALL TESTS PASSED!`.

To run the full pytest suite (if `pytest` is installed):

```bash
python3 -m pytest tests/ -v
```

> **Note on `verify.py`:** it hardcodes `sys.path.insert(0, '/home/hari/Desktop/Banking/src')`.
> If you cloned the repo elsewhere, either edit that path or set `PYTHONPATH=src` and
> invoke the module via `python3 -c "import sys; sys.path.insert(0,'src'); import tests.verify"`
> — or simplest, just run it in place from the workspace root.

## 7. Next steps

- Configure providers and retrieval in `config.yaml` — see `configuration.md`.
- Load documents into the index — see `document-ingestion.md`.
- Run the chatbot — see `running-locally.md`.
- If something fails — see `troubleshooting.md`.

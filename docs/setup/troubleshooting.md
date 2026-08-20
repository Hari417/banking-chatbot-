# Troubleshooting

**Version:** 1.0
**Status:** Current
**Last Verified:** 2026-08-20 against `src/banking_rag/*.py`, `src/cli.py`, `src/api.py`
**Sources:** `src/banking_rag/llm.py`, `src/banking_rag/vector_store.py`, `src/banking_rag/embeddings.py`, `src/banking_rag/retrieval.py`
**Owner:** Scribe

---

How to diagnose the most common v1 failures. For deeper procedures
(re-indexing, provider swaps, model changes), see `docs/runbook/`.

## General first steps

1. Run the mock smoke test to isolate wiring from environment issues:

   ```bash
   python3 tests/verify.py
   ```
   If this passes, the package is correctly installed; the problem is your
   provider/key/model/index.

2. Add `--debug` (CLI) or set `BANKING_RAG_DEBUG=true` (API) for verbose logging.

3. Confirm your config is being read: `python3 -c "import sys; sys.path.insert(0,'.
   src'); from banking_rag.config import load_config; c=load_config('config.yaml'); print(c.llm.provider, c.embedding.provider)"`.

---

## 1. LLM / provider errors

### `OPENAI_API_KEY not set - LLM calls will fail` (warning)
- The env var named by `llm.api_key_env` is unset. `export OPENAI_API_KEY="sk-..."`.
- If you intended local mode, set `llm.provider: ollama` (or `openai_compatible`) in
  `config.yaml` instead.

### `requests.exceptions.ConnectionError` / timeout calling `.../chat/completions`
- OpenAI/OpenAI-compatible: check `llm.api_base` and network egress.
- Ollama: `ollama list` (is the daemon up?) and `ollama show <model>` (is the model
  present?). Local LLMs are slower — raise `llm.timeout`.
- For Ollama, confirm `llm.model` matches a pulled model. The separate
  `ollama_model` field is **not** used by `LLMClient` (see `configuration.md`).

### `Unsupported LLM provider: <x>`
- `llm.provider` must be one of `openai`, `openai_compatible`, `ollama` (enforced in
  `LLMClient._validate_config`).

### Streaming returns nothing / `Failed to parse stream chunk`
- The streaming parser uses `eval()` on SSE `data:` payloads (see the limitation in
  `docs/evaluation/known-limitations.md`). Non-OpenAI servers with different SSE
  framing may fail. Prefer non-streaming (`stream: false`) for v1.

---

## 2. Embedding errors

### `faiss-cpu is required but not installed` (or `sentence-transformers not installed`)
- Reinstall core deps: `pip install -r requirements.txt` inside your venv. The venv may
  be unactivated — `which python3` should point inside `.venv`.

### Local model fails to download (`all-MiniLM-L6-v2`)
- Requires network egress to HuggingFace Hub on first load. For an air-gapped host,
  pre-download the model into the HF cache, or switch to an OpenAI-compatible
  embedding provider.

### Embedding and index dimension mismatch
- The FAISS index is created with `embedding.dimensions` (default 384). If you change
  `embedding.model` to one with a different dimension, existing index load or search
  will fail. Rebuild the index — see `docs/runbook/embedding-model-change.md`.

---

## 3. Vector store / index errors

### `FileNotFoundError: ./data/index/faiss.index` / index never loads
- On first run a fresh empty index is created; this is normal. The error indicates the
  `data/index/` directory could not be created — check permissions on `data_dir`.

### Search returns no results / always abstains
- The index is empty or below `score_threshold` expectations. Confirm ingestion ran and
  `metadata.json` has entries: `python3 -c "import json; print(len(json.load(open('data/index/metadata.json'))))"`.
- Remember `score_threshold` is **not enforced** in v1 retrieval; empty results mean the
  index is empty, not that scores were filtered out.

### Adding chunks does not increase `VectorStore.count()` / delete has no effect
- `VectorStore.delete_chunk()` removes metadata only, not the FAISS vector (append-only
  index). To truly remove content, `vs.clear()` and re-ingest.

### Index corruption / persisted index won't load
- FAISS `read_index` will raise. Restore from a backup of `data/index/` or rebuild with
  `vs.clear()` + re-ingest. v1 does not implement the SHA-256 checksum verification
  described in the risk register (R008 is "Partially Mitigated"). See
  `docs/runbook/index-corruption-recovery.md`.

---

## 4. Retrieval behavior surprises

### Sparse (BM25) not contributing
- `rank-bm25` is not installed. The retriever logs
  `"rank-bm25 not installed, using dense-only retrieval"` and proceeds with dense only.
  Install it: `pip install rank-bm25`.

### Retrieval scores "wrong" vs. expected RRF behavior
- The retriever's `retrieve()` calls `_score_fusion` (normalized weighted combine,
  hardcoded `0.7` dense : `0.3` sparse), **not** the `_reciprocal_rank_fusion` method
  described in its docstring. RRF is dead code in v1. See
  `docs/architecture/overview.md` §Retrieval.

---

## 5. API errors

### `ImportError: cannot import name 'FastAPI'`
- The API is optional. `pip install fastapi uvicorn`, then restart.

### 500 on `/chat`
- Most often a provider/credential issue surfacing through `workflow.run()`. Tail the
  server logs (set `BANKING_RAG_DEBUG=true`) — the exception message is returned in the
  `detail` field. Run the same query through the CLI for a cleaner traceback.

### `/ingest` "succeeds" but the document is not searchable
- This is expected in v1: `/ingest` is a stub and does not ingest. Use the Python
  `DocumentIngestionPipeline` (see `document-ingestion.md`).

### Sessions vanish after restart
- Expected: the API uses an in-memory dict; sessions are not persisted (R007, accepted
  for v1). See `docs/runbook/session-cleanup.md`.

---

## 6. Out-of-scope / abstention confusion

### Every question returns a refusal
- Either the index is empty (ingestion hasn't run), or the response tripped the
  `_should_abstain()` trigger scan. The scan flags any response containing phrases like
  `"i don't know"`, `"transactional"`, `"account-specific"`, `"personal information"`,
  `"outside my knowledge"`. If your LLM tends to include such hedges, it will be
  rewritten to the fixed refusal. Try a lower `temperature` or a different model.

### Response is clearly hallucinated but `grounded: true`
- The grounding validator is a token-overlap heuristic (`overlap / len > 0.2`), not a
  semantic check. Lexical overlap can pass fabricated content. This is an accepted v1
  limitation — see `docs/evaluation/known-limitations.md`.

---

## 7. `tests/verify.py` path error

`verify.py` hardcodes `/home/hari/Desktop/Banking/src` in `sys.path`. If you cloned
elsewhere, edit that line to your `src` path, or run from the workspace root with
`PYTHONPATH=src python3 tests/verify.py` after replacing the hardcoded path.

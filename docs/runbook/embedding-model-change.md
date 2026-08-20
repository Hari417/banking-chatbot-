# Runbook: Embedding Model Change

**Version:** 1.0
**Status:** Current
**Last Verified:** 2026-08-20 against `src/banking_rag/embeddings.py`, `src/banking_rag/vector_store.py`
**Sources:** `src/banking_rag/embeddings.py`, `src/banking_rag/vector_store.py`, `risk-analysis.md` R009
**Owner:** Scribe

---

## Critical fact

Changing the embedding model changes the **vector space**. Existing vectors in the
FAISS index are meaningless in the new space. You **must fully re-index** the entire
corpus. There is no incremental path. (R009.)

The FAISS index is created with `embedding.dimensions`; if the new model has a different
dimension, the existing index will fail to load or search.

## When to change the embedding model

- Upgrading from `all-MiniLM-L6-v2` (384d) to a stronger model (e.g.
  `bge-base-en-v1.5`, 768d) for better retrieval.
- Switching from local sentence-transformers to an API embedding provider (or back).

## Pre-flight

1. **Pin the exact version** of the new model in `requirements.txt` / your deployment
   notes so future reinstalls pick the same model. R009 mitigations 1–2.

2. Confirm the new model loads and its dimension:

   ```bash
   python3 -c "from sentence_transformers import SentenceTransformer; \
   m=SentenceTransformer('<new-model>'); print('dim=', m.get_sentence_embedding_dimension())"
   ```

3. **Back up the index directory** and the config:

   ```bash
   cp -r data/index "data/index.bak.$(date +%Y%m%d-%H%M%S)"
   cp config.yaml config.yaml.bak
   ```

## Procedure

1. **Change `embedding:` in `config.yaml`:**

   ```yaml
   embedding:
     provider: "local"
     model: "<new-model>"
     dimensions: <new-dimension>   # must match the model
     batch_size: 32
     timeout: 60
   ```

   For an API embedding provider, set `provider: openai` (or `openai_compatible`) and
   the matching `model` / `api_base` / `api_key_env`. Note: the API embedding path loops
   one request per text; large corpora will be slow and costly.

2. **Stop the API/CLI** so nothing queries a mismatched index.

3. **Wipe and re-index.** Use the same `reindex.py` as in `reindexing.md`; `vs.clear()`
   recreates the index with the new `dimensions`, then `ingest_directory()` re-embeds
   everything:

   ```python
   # scripts/reindex.py — same as docs/runbook/reindexing.md
   # 1. vs.clear()      -> creates fresh index with new dimensions
   # 2. ingest_directory("path/to/corpus")
   # 3. print(vs.count())
   ```

4. **Verify dimension agreement.** After re-index, confirm the index dimension matches
   the model:

   ```bash
   python3 -c "import sys; sys.path.insert(0,'src'); \
   from banking_rag.config import load_config; from banking_rag.vector_store import VectorStore; \
   c=load_config(); vs=VectorStore(c); \
   print('config dim=', c.embedding.dimensions, 'index ntotal=', vs.index.ntotal, 'd=', vs.index.d)"
   ```

   `vs.index.d` must equal `c.embedding.dimensions`.

5. **Restart and smoke-test** with a known query.

## Stored model metadata

Stage 5 of ingestion writes `embedding_model` and `ingested_at` into each chunk's
metadata. After the change, new chunks carry the new model name — but old chunks (if any
survived) would carry the old one. Because you wipe with `vs.clear()`, this is moot
after a full re-index. If you ever need to detect stranded old-model chunks, grep
`metadata.json` for the old model name.

> **Limitation:** `ingested_at` is set to the model name string (a copy-paste bug in
> stage 5), not a timestamp. You cannot rely on it for ordering — see
> `docs/evaluation/known-limitations.md`.

## Rollback

If retrieval quality regresses with the new model, restore config + index backup and
restart:

```bash
rm -rf data/index
mv data/index.bak.<timestamp> data/index
mv config.yaml.bak config.yaml
python3 src/api.py &
```

## v1 caveat: no automatic dimension guard

`VectorStore._create_index()` uses `config.embedding.dimensions` blindly; there is no
runtime check that loaded vectors match. A dimension mismatch will surface as a FAISS
error on `add` or `search`, not a friendly message. The `get_dimension()` helper exists
on `EmbeddingModel` but is not consulted at index load. Verify dimensions manually
(step 4) before trusting the new index.

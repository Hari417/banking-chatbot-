# Runbook: Reindexing

**Version:** 1.0
**Status:** Current
**Last Verified:** 2026-08-20 against `src/banking_rag/vector_store.py`, `src/banking_rag/ingestion.py`
**Sources:** `src/banking_rag/vector_store.py`, `src/banking_rag/ingestion.py`, `risk-analysis.md` R008
**Owner:** Scribe

---

## When to re-index

- You added or removed documents and want the change reflected in retrieval.
- You changed `chunking.chunk_size` / `chunk_overlap` / `chunking.strategy`.
- The index is corrupt (see `index-corruption-recovery.md`).
- You are about to change the embedding model (follow `embedding-model-change.md`
  instead — it includes re-indexing).
- FAISS library major version upgrade that breaks index compatibility.

> **v1 nuance:** `VectorStore.delete_chunk()` removes a chunk from `metadata.json` but
> not its vector from the FAISS index (the index is append-only in this impl). So partial
> updates are unreliable — prefer a full rebuild.

## Before you start

1. **Back up the existing index** so you can roll back:

   ```bash
   cp -r data/index "data/index.bak.$(date +%Y%m%d-%H%M%S)"
   ```

2. Stop the API process so no queries hit a half-rebuilt index:

   ```bash
   # Ctrl+C the python3 src/api.py process in its terminal,
   # or find and stop it. No systemd unit exists for v1.
   ```

## Rebuild procedure

Create `scripts/reindex.py` in the project root:

```python
import sys, os
sys.path.insert(0, "src")
from banking_rag.config import load_config
from banking_rag.vector_store import VectorStore
from banking_rag.ingestion import create_ingestion_pipeline

config = load_config("config.yaml")
vs = VectorStore(config)

# 1. Wipe the existing index, metadata, and registry.
vs.clear()
print(f"Cleared. count={vs.count()}")

# 2. Re-ingest every document from your corpus directory.
pipeline = create_ingestion_pipeline(vs, config)
result = pipeline.ingest_directory("path/to/your/corpus")
print(f"chunks={result.chunks} embeddings={result.embeddings} failed={result.failed}")
for err in result.errors:
    print("ERROR:", err)

# 3. Verify counts.
print(f"Final count={vs.count()}")
```

Run it:

```bash
python3 scripts/reindex.py
```

## Verify the new index loads

On a clean interpreter, re-open the store and confirm the count matches:

```bash
python3 -c "import sys; sys.path.insert(0,'src'); \
from banking_rag.config import load_config; from banking_rag.vector_store import VectorStore; \
vs=VectorStore(load_config()); print('count=', vs.count())"
```

Then restart the API and send a known query:

```bash
python3 src/api.py &
sleep 3
curl -s -X POST http://localhost:8000/chat -H 'Content-Type: application/json' \
  -d '{"query":"What are your banking hours?"}' | python3 -m json.tool
```

If the response abstains with "I couldn't find any relevant information," the index is
empty or the corpus didn't include that topic — check `result.errors` and the
`metadata.json` file size.

## Rollback

If the rebuild fails or retrieval quality regresses, stop the API, restore the backup,
restart:

```bash
rm -rf data/index
mv data/index.bak.<timestamp> data/index
python3 src/api.py &
```

## Expected duration

- The dominant cost is embedding generation. For `all-MiniLM-L6-v2` on CPU, expect
  roughly a few hundred chunks/second after the model is warm.
- A 100-page PDF (a few hundred chunks) re-indexes in well under a minute on a modern
  laptop; the project's stated target is <10 min for a 100-page PDF, which v1 meets
  comfortably on CPU.

# Runbook: Index Corruption Recovery

**Version:** 1.0
**Status:** Current
**Last Verified:** 2026-08-20 against `src/banking_rag/vector_store.py`
**Sources:** `src/banking_rag/vector_store.py`, `risk-analysis.md` R008
**Owner:** Scribe

---

## Symptom

On startup or first query, `VectorStore._load_index()` raises a FAISS error
(`faiss.read_index` fails), or `metadata.json` is missing/malformed so `search()`
returns wrong/empty results. APIs see a 500 on `/chat`; the CLI prints a traceback.

## v1 reality (important)

R008 lists "SHA-256 checksum verification" and "automated rebuild trigger" as
mitigations. **Neither is implemented in v1** (R008 is "Partially Mitigated"). There is:

- no checksum file alongside the index,
- no startup integrity check beyond `read_index`,
- no `/health` probe that detects index failure (the endpoint returns hardcoded booleans
  — see `docs/api/health-endpoint.md`).

So you detect corruption only when a request fails. Keep backups; they are your only
repair mechanism in v1.

## Recovery procedure

1. **Stop the API/CLI** to prevent further writes to a damaged store.

2. **Inspect the damage:**

   ```bash
   ls -la data/index/
   # Look for: faiss.index, metadata.json, document_registry.json
   python3 - <<'PY'
   import json, sys
   try:
       m=json.load(open("data/index/metadata.json"))
       print("metadata entries:", len(m))
   except Exception as e:
       print("metadata.json broken:", e)
   PY
   ```

3. **Restore from the most recent backup** (you create one on every re-index per
   `reindexing.md` — if you skipped that, take a manual snapshot before destructive
   work next time):

   ```bash
   ls data/ | grep index.bak       # list available backups
   rm -rf data/index
   cp -r data/index.bak.<most-recent> data/index
   ```

4. **Verify the restored index loads:**

   ```bash
   python3 -c "import sys; sys.path.insert(0,'src'); \
   from banking_rag.config import load_config; from banking_rag.vector_store import VectorStore; \
   vs=VectorStore(load_config()); print('count=', vs.count(), 'ntotal=', vs.index.ntotal)"
   ```

   A successful load means `read_index` succeeded; `count` should match the backup.

5. **Restart and smoke-test** with a known query.

## If no backup exists

There is no recovery path other than a full rebuild from source documents. Follow
`reindexing.md` from step "Rebuild procedure," omitting the `cp` backup step (the index
is already lost). Re-ingest your corpus directory from scratch.

## Preventive measures (v1)

- Snapshot `data/index/` before any re-index, model change, or `vs.clear()`.
- Keep at least the two most recent backups; rotate older ones.
- Treat any `read_index` failure as a P1: the system cannot serve answers until the
  index is restored or rebuilt.

## v2 path (not implemented)

Per R008 mitigations 3–4, the v2 plan is: (a) write a SHA-256 checksum next to the
index and verify it in `_load_or_create_index`; (b) on mismatch, automatically trigger
a rebuild from the corpus directory; (c) surface index health through a real `/health`
probe. None of this exists in v1.

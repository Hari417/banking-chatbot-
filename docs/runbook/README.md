# Maintenance Runbook

**Version:** 1.0
**Status:** Current
**Last Verified:** 2026-08-20 against `src/banking_rag/`
**Sources:** `risk-analysis.md`, `src/banking_rag/vector_store.py`, `src/banking_rag/ingestion.py`
**Owner:** Scribe

---

Operator procedures for keeping the Banking RAG Chatbot v1 healthy. v1 is a local
single-user prototype, so these are manual, copy-pasteable Python/shell sequences rather
than automated runbooks.

| Procedure | Doc | Trigger |
|-----------|-----|---------|
| Rebuild the FAISS index | `reindexing.md` | New documents, corrupt index, config change |
| Recover from index corruption | `index-corruption-recovery.md` | FAISS load failure, missing metadata |
| Swap LLM provider (OpenAI ↔ Ollama) | `llm-provider-swap.md` | Cost/latency/air-gap change |
| Change the embedding model | `embedding-model-change.md` | Model upgrade; **requires full re-index** |
| Log rotation & retention | `log-rotation-and-retention.md` | Disk pressure, audit retention |
| Session cleanup | `session-cleanup.md` | Restart hygiene, memory growth |
| Incident response (injection/PII leak) | `incident-response.md` | Suspected security event |

## Guiding facts for v1

- The FAISS index and its metadata/registry JSON live under `./data/index/`. Back this
  directory up before any destructive operation.
- `VectorStore.delete_chunk()` removes metadata only, not the vector. Full removal or
  any embedding/index change ⇒ `vs.clear()` + re-ingest.
- There is **no SHA-256 checksum verification** of the index on load (R008 partially
  mitigated). Backups are your safety net.
- Logging is stdlib text, not structured JSON — there is no audit trail to query. See
  `log-rotation-and-retention.md` and `docs/compliance/audit-trail.md`.
- Sessions are in-memory; process restart clears them. Plan around restart windows.

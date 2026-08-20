# GET /config

**Version:** 1.0
**Status:** Current
**Last Verified:** 2026-08-20 against `src/api.py` lines 252–275
**Sources:** `src/api.py`, `src/banking_rag/config.py`, `config.yaml`
**Owner:** Scribe

---

## Method & path

`GET /config`  *(read-only. The planned `POST /config` is **not implemented**.)*

## Purpose

Return a curated, non-secret subset of the currently-loaded configuration. Useful for
clients to learn which LLM/embedding provider and index path the server is using.

## Request

No parameters, no body.

```bash
curl http://localhost:8000/config
```

## Response schema (HTTP 200)

The handler returns a plain dict (no Pydantic response model):

| Field | Type | Description |
|-------|------|-------------|
| `llm` | `{provider, model}` | Current LLM provider and model id. |
| `embedding` | `{provider, model, dimensions}` | Embedding provider, model, dimension. |
| `vector_store` | `{index_type, persist_path}` | FAISS index type and on-disk path. |
| `security` | `{pii_detection_enabled, rate_limit_enabled}` | The two security flags surfaced (note: both are largely unenforced on the query path — see `docs/compliance/`). |

Example:

```json
{
  "llm": { "provider": "openai", "model": "gpt-4o-mini" },
  "embedding": { "provider": "local", "model": "all-MiniLM-L6-v2", "dimensions": 384 },
  "vector_store": { "index_type": "IndexFlatIP", "persist_path": "./data/index/faiss.index" },
  "security": { "pii_detection_enabled": true, "rate_limit_enabled": true }
}
```

## What is NOT returned

- API keys, env var names, base URLs, Ollama URLs — secrets and endpoints are omitted.
- Retrieval, chunking, session, and feature-flag sections — omitted (only `llm`,
  `embedding`, `vector_store`, `security` are surfaced).
- The full path resolution — `persist_path` is returned verbatim from config.

## Error responses

| Status | When |
|--------|------|
| 500 | `get_config()` loading fails (rare — defaults apply on missing file). |

## Changing configuration

`POST /config` was planned but is **not implemented**. There is no live-reload endpoint.
To change configuration:

1. Edit `config.yaml` (or set `BANKING_RAG_CONFIG` to point at another file).
2. Restart the API process. The workflow singleton is rebuilt on the next request after
   restart; there is no in-process reload. (`reload_config()` exists in
   `config.py` but is not wired to any endpoint.)

`docs/runbook/llm-provider-swap.md` documents the provider-swap procedure, including
the restart step.

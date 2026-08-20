# GET /health

**Version:** 1.0
**Status:** Current
**Last Verified:** 2026-08-20 against `src/api.py` lines 136–146
**Sources:** `src/api.py`, `component-specification.md`
**Owner:** Scribe

---

## Method & path

`GET /health`

## Purpose

Liveness/readiness check. Returns a static "ready" status plus version and component
flags. Used to verify the API process is up and the workflow singleton initialized.

## Request

No parameters, no body.

```bash
curl http://localhost:8000/health
```

## Response schema — `HealthResponse` (HTTP 200)

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Always `"ready"` in v1 (hardcoded). |
| `version` | string | API version, `"0.1.0"`. |
| `vector_store_ready` | bool | Always `true` in v1 (hardcoded — not a real probe). |
| `model_available` | bool | Always `true` in v1 (hardcoded — not a real probe). |

Example:

```json
{
  "status": "ready",
  "version": "0.1.0",
  "vector_store_ready": true,
  "model_available": true
}
```

## Implementation note (limitation)

The handler calls `get_workflow()` (which constructs the singleton if absent) and then
returns hardcoded flags. It does **not** verify the FAISS index loaded, the embedding
model is in memory, or the LLM endpoint is reachable. A 200 from `/health` only
confirms the process started and the workflow object instantiated, not that the system
can actually answer queries. For a functional probe, issue a trivial `/chat` query in
mock mode. Tracked in `docs/evaluation/known-limitations.md`.

## Error responses

A 500 indicates the workflow singleton failed to construct (bad config, missing index
directory). Tail server logs for the underlying exception.

# API Reference Overview

**Version:** 1.0
**Status:** Current
**Last Verified:** 2026-08-20 against `src/api.py`
**Sources:** `src/api.py`, `config.yaml`, `component-specification.md`
**Owner:** Scribe

---

## Server

The API is a FastAPI app in `src/api.py`. Start it with:

```bash
python3 src/api.py        # binds 0.0.0.0:8000 by default
```

Host, port, mock-mode, and config path are read from environment variables — see
`docs/setup/configuration.md` §Deployment env vars. Interactive OpenAPI docs are
available at `/docs` (FastAPI auto-generates them) once the server is running.

A single `RAGWorkflow` instance is constructed on first request and reused for all
subsequent requests (process-global singleton). In mock mode
(`BANKING_RAG_MOCK=true`) it uses `MockRAGWorkflow`, which returns canned responses
without any model or key.

## Endpoints actually implemented

| Method | Path | Doc |
|--------|------|-----|
| POST | `/chat` | `chat-endpoint.md` |
| POST | `/query` | alias of `/chat` (no separate doc) |
| GET | `/health` | `health-endpoint.md` |
| POST | `/ingest` | `ingest-endpoint.md` |
| GET | `/config` | `config-endpoint.md` |
| GET | `/sessions` | `sessions-endpoint.md` |
| GET | `/sessions/{session_id}` | `sessions-endpoint.md` |
| DELETE | `/sessions/{session_id}` | `sessions-endpoint.md` |

> **Plan vs. implementation:** The documentation outline listed four endpoints
> (`/chat`, `/ingest`, `/health`, `/config`) with `/config` as GET **and** POST. In the
> implementation, `/config` is **GET-only** (read-only), `/query` is an extra alias of
> `/chat`, and a `/sessions` resource (list/get/delete) exists but was not in the
> outline. There is no live `/config` POST and no streaming `/chat` in v1.

## Cross-cutting behavior

- **CORS** — open (`allow_origins=["*"]`, all methods/headers). Appropriate for a local
  prototype; tighten before any non-local exposure.
- **Sessions** — in-process Python dict keyed by the client-supplied `session_id`. Lost
  on process restart. No TTL enforcement. See `sessions-endpoint.md`.
- **Rate limiting** — **not implemented** despite `security.rate_limit_*` config flags.
- **Query-side security** — **not implemented** (no PII detection, no injection filter
  on `/chat` input). Scope control is enforced inside the workflow via the system
  prompt and the abstention trigger scan. See `docs/compliance/scope-enforcement.md`.
- **Audit logging** — stdlib text logging only; no structured JSON audit trail in v1.
  See `docs/compliance/audit-trail.md`.
- **Errors** — unhandled exceptions on `/chat` and `/ingest` return HTTP 500 with the
  exception string in `detail` (via the route handler) or a generic message (via the
  global `@app.exception_handler(500)`). Not-found session endpoints return 404.
- **Auth** — none. The API has no authentication or authorization layer in v1.

See each endpoint's doc for request/response schemas and curl examples.

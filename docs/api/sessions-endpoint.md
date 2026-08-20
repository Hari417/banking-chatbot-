# /sessions — Session Management

**Version:** 1.0
**Status:** Current
**Last Verified:** 2026-08-20 against `src/api.py` lines 43–44, 149–221
**Sources:** `src/api.py`, `config.yaml` (`session.*`), `risk-analysis.md` R007
**Owner:** Scribe

---

## Overview

The API keeps an **in-process, in-memory** Python dict `session_store` mapping a
client-supplied `session_id` to a list of message records. Sessions are populated as a
side-effect of `POST /chat` and read/deleted via the endpoints below.

> **Implementation divergence:** The documentation outline did not list session
> endpoints, but they exist in `src/api.py`. Conversely, the planned `session.ttl_minutes`
> / `session.memory_limit` / `session.persistence` config fields are **not enforced**
> here — the store is an unbounded dict with no TTL sweeper and no SQLite persistence.

## Endpoints

### `GET /sessions`

List all active session ids.

```bash
curl http://localhost:8000/sessions
# ["sess-1", "sess-2"]
```

Response: `List[string]` (HTTP 200).

### `GET /sessions/{session_id}`

Fetch a session's message history.

```bash
curl http://localhost:8000/sessions/sess-1
```

Response — `SessionResponse` (HTTP 200):

| Field | Type | Description |
|-------|------|-------------|
| `session_id` | string | The session id. |
| `messages` | `List[{role, content, citations?}]` | Appended user/assistant turns. |
| `count` | int | Number of message records. |

| Status | When |
|--------|------|
| 404 | Unknown `session_id`. |

### `DELETE /sessions/{session_id}`

Delete a session.

```bash
curl -X DELETE http://localhost:8000/sessions/sess-1
# {"message": "Session sess-1 deleted"}
```

Response (HTTP 200): `{"message": "Session <id> deleted"}`. 404 if unknown.

## How sessions are populated

When `POST /chat` is called with a non-null `session_id`, the handler appends **two**
records to `session_store[session_id]`:

1. `{"role": "user", "content": <query>}`
2. `{"role": "assistant", "content": <response>, "citations": <citations list>}`

If the `session_id` is new, the list is created on first use. There is no explicit
`POST /sessions` create endpoint; sessions are created implicitly by the first `/chat`
call that references them.

## What is NOT implemented

- **TTL** — `session.ttl_minutes` (default 30) is ignored. Sessions live until the
  process exits or you `DELETE` them.
- **Memory cap** — `session.memory_limit` (default 100) is ignored. The dict grows
  unbounded; long-running processes accumulate sessions.
- **Persistence** — `session.persistence` (default false) is ignored even if set
  `true`. SQLite persistence was planned for v2 and is not implemented. All sessions
  are lost on process restart (accepted risk R007).
- **Multi-turn context** — the stored history is **not** fed back into the RAG
  workflow. Each `/chat` call runs `workflow.run(query)` independently; prior turns
  do not influence retrieval or generation. The session store is a transcript log, not
  a conversational memory. This is an important functional limitation — see
  `docs/evaluation/known-limitations.md`.

## Security note

Session ids are client-chosen strings with no validation, no auth, and no
access control. Any client can read or delete any session id. Acceptable for a local
single-user prototype; unacceptable for any shared deployment.

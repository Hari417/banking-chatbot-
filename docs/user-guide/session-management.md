# Session Management

**Version:** 1.0
**Status:** Current
**Last Verified:** 2026-08-20 against `src/api.py`, `src/cli.py`
**Sources:** `src/api.py`, `config.yaml`, `risk-analysis.md` R007
**Owner:** Scribe

---

## What sessions are in v1

Sessions exist **only on the REST API** path (`src/api.py`), as an in-memory dict keyed
by a client-supplied `session_id`. The **CLI does not use sessions** — each CLI query is
independent and no history is kept between turns.

## On the API

- **Creating a session:** pass a `session_id` in your `POST /chat` request. If it is
  new, the session is created implicitly. There is no `POST /sessions` create endpoint.
- **Reading history:** `GET /sessions/{session_id}` returns the stored user/assistant
  turns.
- **Listing:** `GET /sessions` returns all current session ids.
- **Deleting:** `DELETE /sessions/{session_id}`.

See `docs/api/sessions-endpoint.md` for schemas and curl examples.

## v1 session constraints (be aware)

- **Not multi-turn.** Stored history is a transcript only; it is **not** fed back into
  retrieval or the prompt. Each `/chat` call is answered independently. See
  `docs/evaluation/known-limitations.md` C2.
- **Lost on restart.** Sessions live in process memory. Stopping/restarting the API
  clears all of them (R007, accepted for v1). There is no SQLite persistence in v1.
- **No expiry.** `session.ttl_minutes` is ignored; sessions never auto-expire.
- **No memory cap.** `session.memory_limit` is ignored; the dict grows unbounded.
- **No auth.** Any client can read or delete any session id.

## On the CLI

The CLI `chat` mode keeps an interactive loop in the terminal but does not persist or
reload any session. Quitting the CLI discards everything.

## What this means in practice

- Treat sessions as **ephemeral transcripts**, not as conversational memory. If you need
  the bot to consider earlier turns, include the relevant context in each query.
- For operator cleanup/restart hygiene, see `docs/runbook/session-cleanup.md`.

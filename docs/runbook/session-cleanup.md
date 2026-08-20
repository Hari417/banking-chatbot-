# Runbook: Session Cleanup

**Version:** 1.0
**Status:** Current
**Last Verified:** 2026-08-20 against `src/api.py`
**Sources:** `src/api.py`, `config.yaml` (`session.*`), `risk-analysis.md` R007
**Owner:** Scribe

---

## v1 reality

Sessions live in an in-process Python dict (`session_store` in `src/api.py`). Key facts:

- **No TTL sweeper.** `session.ttl_minutes` (default 30) is **ignored**. Sessions never
  expire on their own.
- **No memory cap.** `session.memory_limit` (default 100) is **ignored**. The dict grows
  without bound.
- **No persistence.** `session.persistence` is **ignored even if set `true`**. SQLite
  persistence is a v2 item not implemented.
- **Lost on restart.** Process exit clears all sessions (R007, accepted for v1).
- **Not multi-turn.** Stored history is a transcript log only — it is not fed back into
  the RAG workflow. Each `/chat` call is independent (see `docs/api/sessions-endpoint.md`).

## Manual cleanup

### Delete a single session

```bash
curl -X DELETE http://localhost:8000/sessions/<session_id>
# {"message": "Session <session_id> deleted"}  (404 if unknown)
```

### List all sessions (then delete as needed)

```bash
curl -s http://localhost:8000/sessions | python3 -m json.tool
# ["sess-1", "sess-2", ...]
```

### Clear all sessions (requires a restart, since there is no "clear-all" endpoint)

The simplest reset is to restart the process:

```bash
# stop python3 src/api.py (Ctrl+C in its terminal), then:
python3 src/api.py &
```

All sessions are gone. This is the only "nuke" path in v1.

## Freeing memory on a long-running instance

Because nothing auto-expires, a long-running API accumulates sessions and their message
lists in memory. To bound memory:

1. Periodically `GET /sessions`; for each id you no longer need, `DELETE /sessions/<id>`.
2. Or schedule process restarts during a maintenance window (sessions are expected to be
   ephemeral — R007).

There is no metric/API for total session size; estimate from the number of sessions ×
average messages.

## v2 path (not implemented)

The planned v2 session store:

- SQLite-backed (honoring `session.persistence: true`).
- A background TTL sweeper enforcing `session.ttl_minutes`.
- An `memory_limit`-based eviction policy.
- Multi-turn context fed into retrieval (today each turn is independent).

None of this is present in v1; the config flags are placeholders. The honest v1 contract
is: sessions are an append-only in-memory transcript, cleared on restart, no expiry.

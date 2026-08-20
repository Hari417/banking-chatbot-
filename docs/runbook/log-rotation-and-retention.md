# Runbook: Log Rotation & Retention

**Version:** 1.0
**Status:** Current
**Last Verified:** 2026-08-20 against `src/cli.py`, `src/api.py`, `src/banking_rag/*.py`
**Sources:** `src/cli.py`, `src/api.py`, `docs/STYLE_GUIDE.md` §2, `risk-analysis.md` R003/R016
**Owner:** Scribe

---

## v1 reality (read this first)

The `STYLE_GUIDE.md` §2 specifies structured JSON logging with `python-json-logger`,
field schemas, event taxonomy, and an audit trail keyed by `request_id`. **None of this
is implemented in v1.** What exists is:

- `logging.basicConfig(level=..., format='%(asctime)s - %(name)s - %(levelname)s -
  %(message)s')` in `src/cli.py::setup_logging()`.
- Module-level `logger = logging.getLogger(__name__)` across `banking_rag` modules,
  emitting plain-text INFO/WARNING/ERROR lines to stderr.
- No JSON formatter, no `request_id`, no event taxonomy, no `session_id` in logs, no
  PII redaction in logs (because nothing structural is logged about queries).
- No log file — output goes to the process's stderr. There is no `./logs/` directory in
  use, despite the Style Guide reference.
- The `config.yaml` `system.log_level` is read by the CLI's `--debug` toggle in spirit
  but the API does not consult `log_level` (it relies on uvicorn's default logging).

This runbook therefore documents (a) what little you can do today and (b) the v2 target.

## What you can do in v1

### Capture logs to a file

Since the app does not write a log file, redirect stderr at launch:

```bash
# CLI
python3 src/cli.py chat 2>> logs/cli.log

# API (uvicorn logs go to stderr too)
mkdir -p logs
python3 src/api.py >> logs/api.stdout.log 2>> logs/api.stderr.log &
```

Caveat: stdlib `basicConfig` and uvicorn both write to stderr; mixing them is messy but
functional for a prototype.

### Rotate with `logrotate` (Linux)

Since the app does not rotate, use the OS:

```bash
# /etc/logrotate.d/banking-rag (adjust paths)
/home/hari/Desktop/Banking/logs/*.log {
    daily
    rotate 14
    compress
    missingok
    notifempty
    copytruncate
}
```

`copytruncate` avoids needing to signal the app (which has no log-reopen handler).

### Adjust verbosity

- CLI: add `--debug`.
- API: set `BANKING_RAG_DEBUG=true` (enables uvicorn reload and DEBUG-level uvicorn
  logs). Verbosity of the `banking_rag` loggers themselves is INFO by default; there is
  no env var to raise it without a code change to `setup_logging`.

## Retention guidance (v1)

The registry (`risk-analysis.md` R016 mitigation 3) asks for a query audit trail with a
retention period. v1 has no such trail. The only durable artifacts are:

| Artifact | Path | Retention guidance (v1) |
|----------|------|--------------------------|
| FAISS index + metadata + registry | `./data/index/` | Keep + back up (your knowledge base). |
| Quarantined PII chunks | `./data/quarantine/` | Review and delete; do not keep PII. |
| Captured logs (if you redirect) | `./logs/*.log` | Rotate daily; 7–14 days is ample for a local prototype. |

There is no PII in the v1 logs (because queries are not logged in detail), but stderr
lines may include chunk content in DEBUG-level messages from `ingestion.py` /
`rag_workflow.py`. If you raise verbosity, redact or restrict access to `logs/`.

> **Open decision:** the audit-log retention period (R016 mitigation 3) was never
> decided. For a non-production prototype default to the life of the v1 instance; for
> any deployment, decide a retention period and write it into `docs/compliance/audit-trail.md`
> before carrying real data.

## v2 path (not implemented)

The Style Guide's §2 spec is the v2 target: structured JSON one-event-per-line in
`./logs/`, fields (`timestamp`, `level`, `event`, `module`, `session_id`,
`request_id`, `duration_ms`, `pii_flag`, `abstained`, `risk_ref`), event taxonomy
(`query.*`, `security.*`, `retrieval.*`, `generation.*`, …), and the audit-trail
sequence. Wiring this requires: a JSON formatter in a `setup_logging()` call that the
API and CLI both call, a `request_id` middleware, and event-emitting calls at each
pipeline stage. None exist in v1 — see `docs/compliance/audit-trail.md`.

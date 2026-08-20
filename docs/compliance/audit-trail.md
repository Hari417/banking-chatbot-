# Audit Trail

**Version:** 1.0
**Status:** Current
**Last Verified:** 2026-08-20 against `src/cli.py`, `src/api.py`, `src/banking_rag/*.py`
**Sources:** `docs/STYLE_GUIDE.md` §2 & §5, `risk-analysis.md` R003/R016, `component-specification.md` §3/§10
**Owner:** Scribe

---

## v1 reality (read first)

The `STYLE_GUIDE.md` §2 describes a structured-JSON audit trail keyed by `request_id`,
emitting events like `query.received → security.* → retrieval.* → generation.* →
response.sent`. **This audit trail is not implemented in v1.**

What v1 actually produces:

- **Stdlib text logs** via `logging.basicConfig(format='%(asctime)s - %(name)s -
  %(levelname)s - %(message)s')` in the CLI's `setup_logging()`.
- **No `request_id`**, no `session_id` in log lines, no event taxonomy, no JSON output,
  no log file (logs go to stderr).
- **No per-request audit sequence.** The `RAGWorkflow.run()` path emits INFO lines like
  `"Embedding query: <first 50 chars>..."`, `"Retrieving documents..."`, `"Building
  context..."`, `"Generating response..."`, `"Validating grounding..."`,
  `"Generating citations..."`, `"RAG workflow completed successfully"`. These are
  progress markers, not compliance audit events — they do not include session id,
  request id, scores, or chunk ids.
- **No `risk_ref` fields** on log events.
- **No PII in logs by construction** (queries are not logged verbatim beyond the first
  50 characters in the INFO line, which can still include PII the user typed). R003
  mitigation 5 (log anonymization) is **not formally satisfied**.

## What is reconstructable today (v1)

Given a specific failed/incident request, an operator can reconstruct **only** by
reproducing it with `--debug` / `BANKING_RAG_DEBUG=true` and tailing stderr. There is
no way to query the history of a past `request_id` — none was ever generated.

| STYLE_GUIDE §5.1 audit claim | v1 status |
|-------------------------------|-----------|
| What was asked (session_id + query hash) | Partial: first 50 chars of the query is logged in INFO; no hash, no session_id |
| Whether it was safe to answer (security.*) | Not logged — no security events exist |
| What the system decided it was (`query.classified`) | Not logged — no intent classifier |
| What evidence was retrieved (chunk_ids + scores) | Not logged |
| What was sent to the LLM (`generation.prompt_built`) | Not logged |
| What was returned (`generation.validated` / `citation_built`) | Not logged |
| Whether abstention fired (`abstained`) | Returned in the API response; not logged as an event |
| Why (`risk_ref`) | Not logged |

## Retention period (open decision)

R016 mitigation 3 requires documenting a retention period for audit logs. **No retention
period is decided for v1.** Because v1 has no audit log to retain, this is moot in
practice, but the decision must be made before any non-local use:

- Default (local prototype): retain captured stderr redirections (if any) for the life
  of the v1 instance.
- Any deployment scenario: decide an explicit retention (e.g., 90 days) and formalize
  it in this document once structured logging is implemented. See open question in
  `docs/DOCUMENTATION_OUTLINE.md`.

## What an auditor can actually inspect in v1

| Artifact | Where | What it shows |
|----------|-------|---------------|
| `metadata.json` | `./data/index/` | All indexed chunks (chunk_id → content + metadata). An auditor can see what was ingested, when (via the model-name `ingested_at` bug — not a real timestamp), and from what source. |
| `document_registry.json` | `./data/index/` | Document → chunk_ids map. Source/format per document. |
| `quarantine/` | `./data/quarantine/` | Chunks rejected for PII, with content + metadata. An auditor can verify PII was quarantined (not silently dropped). |
| API response | `/chat` JSON | Per-response `abstained`, `confidence`, `metadata.grounded`, citations — but only observably, in real time; not persisted. |
| `config.yaml` | repo | All security flags (mostly unenforced — see `docs/setup/configuration.md`). |

## v2 path (the STYLE_GUIDE spec is the v2 target)

To satisfy the audit claim, v2 must implement:

1. A `setup_logging()` called by both the CLI and the API, configured with a JSON
   formatter (e.g., `python-json-logger`), writing newline-delimited JSON to `./logs/`.
2. A `request_id` middleware in the API injecting a per-request UUID, threaded through
   `RAGWorkflow.run()` into every log event.
3. Event-emitting calls at each pipeline stage using the §2.5 taxonomy
   (`query.received`, `security.pii_detected`, `retrieval.fused`, `generation.validated`,
   `generation.abstained`, `response.sent`, …).
4. The §2.3 required fields (`timestamp`, `level`, `event`, `module`, `session_id`,
   `request_id`, `duration_ms`, `pii_flag`, `abstained`, `risk_ref`).
5. The §2.6 NEVER-logged content rules (raw query, full chunk text, secrets).
6. A decided retention period enforced by rotation.

Until these land, the `STYLE_GUIDE.md` §2/§5 content is **aspirational**, and this file
records that honestly. The Scribe charter requires distinguishing current behavior
from intended behavior; here intended == the Style Guide, current == stdlib text logs.

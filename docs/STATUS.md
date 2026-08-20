# Documentation Status

**Version:** 1.0
**Date:** 2026-08-20
**Author:** Scribe
**Status:** Current

---

Rolled-up status of every documentation deliverable as of 2026-08-20 (task t_1547ebb4).
Each file's own front-matter `Status` is authoritative; this table is a convenience map.

Legend: **Current** = verified against the v1 implementation. **Planned** = outlined but
not implemented (`metrics.md`, `test-datasets.md` — eval harness is v2).

## Project front door

| File | Status | Notes |
|------|--------|-------|
| `README.md` | Current | Rewritten aligned to the actual deliverable. |

## Architecture

| File | Status | Notes |
|------|--------|-------|
| `docs/architecture/overview.md` | Current | Narrative; flags divergences from `ARCHITECTURE.md`. |
| `ARCHITECTURE.md` | Current (upstream, Archer) | Planned architecture; kept as reference. |

## API

| File | Status | Notes |
|------|--------|-------|
| `docs/api/overview.md` | Current | Lists all implemented endpoints. |
| `docs/api/chat-endpoint.md` | Current | Includes `/query` alias. |
| `docs/api/health-endpoint.md` | Current | Notes hardcoded probes. |
| `docs/api/ingest-endpoint.md` | Current | Honestly documents the v1 stub. |
| `docs/api/config-endpoint.md` | Current | GET-only; no POST. |
| `docs/api/sessions-endpoint.md` | Current | Was missing from the original outline. |

## Setup

| File | Status | Notes |
|------|--------|-------|
| `docs/setup/prerequisites.md` | Current | |
| `docs/setup/installation.md` | Current | Notes `verify.py` hardcode + optional deps. |
| `docs/setup/configuration.md` | Current | Every `config.yaml` field; flags unenforced ones. |
| `docs/setup/document-ingestion.md` | Current | Python pipeline path; `/ingest` stub noted. |
| `docs/setup/running-locally.md` | Current | CLI + API only (no Streamlit). |
| `docs/setup/troubleshooting.md` | Current | |

## User guide

| File | Status | Notes |
|------|--------|-------|
| `docs/user-guide/getting-started.md` | Current | Points to setup. |
| `docs/user-guide/asking-questions.md` | Current | |
| `docs/user-guide/understanding-citations.md` | Current | chunk_id lookup in metadata.json. |
| `docs/user-guide/session-management.md` | Current | API-only; not multi-turn in v1. |
| `docs/user-guide/limitations-and-scope.md` | Current | |

## Runbook

| File | Status | Notes |
|------|--------|-------|
| `docs/runbook/README.md` | Current | Index + v1 guiding facts. |
| `docs/runbook/reindexing.md` | Current | |
| `docs/runbook/index-corruption-recovery.md` | Current | Notes no checksum in v1. |
| `docs/runbook/llm-provider-swap.md` | Current | |
| `docs/runbook/embedding-model-change.md` | Current | Requires full re-index. |
| `docs/runbook/log-rotation-and-retention.md` | Current | Honestly: stdlib text logs only. |
| `docs/runbook/session-cleanup.md` | Current | Restart clears all. |
| `docs/runbook/incident-response.md` | Current | Manual detection baseline. |

## Compliance

| File | Status | Notes |
|------|--------|-------|
| `docs/compliance/scope-enforcement.md` | Current | Documented partial mitigation. |
| `docs/compliance/pii-handling.md` | Current | Regex (not Presidio); ingestion-only; redaction gap. |
| `docs/compliance/audit-trail.md` | Current | Honestly: no structured audit log in v1. |
| `docs/compliance/disclaimer.md` | Current | Not-for-production; v2 path. |

## Evaluation

| File | Status | Notes |
|------|--------|-------|
| `docs/evaluation/known-limitations.md` | Current | Exhaustive v1 gaps/divergences/bugs. |
| `docs/evaluation/metrics.md` | **Planned** | Eval harness not implemented in v1. |
| `docs/evaluation/test-datasets.md` | **Planned** | JSONL schema recorded for v2. |

## Decisions

| File | Status | Notes |
|------|--------|-------|
| `docs/decisions/adr-NNNN-template.md` | Current | Template + pre-identified decisions ADR-0001..0009. |

## Standards / index

| File | Status | Notes |
|------|--------|-------|
| `docs/STYLE_GUIDE.md` | Draft (upstream, Scribe) | Defines intended standards; v1 implementation does not yet meet §2 logging and §5 audit-trail sections. |
| `docs/DOCUMENTATION_OUTLINE.md` | Current | Updated to reflect written tree + resolved open questions. |
| `docs/STATUS.md` | Current | This file. |

---

## Open follow-ups (not blocking handoff)

1. Implement query-side PII detection, injection filter, rate limiting (B1–B3).
2. Implement structured JSON audit logging (Style Guide §2 — v1 has stdlib text only).
3. Wire `/ingest` to `DocumentIngestionPipeline` (replace the stub).
4. Reconcile fusion code: implement RRF as documented, or update ADR-0006 to match the
   implemented weighted-normalized fusion.
5. Fix `ingested_at` metadata bug (stores model name, not timestamp).
6. Make `tests/verify.py` path-relative (drop the hardcoded `/home/hari/...`).
7. Decide audit-log retention period (R016) — pending structured logging.
8. Locate or re-surface `research_notes.md` referenced in the triage handoff.

Each is recorded in `docs/evaluation/known-limitations.md`; none blocks v1 handoff as a
prototype.

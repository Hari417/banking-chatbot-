# Runbook: Incident Response

**Version:** 1.0
**Status:** Current
**Last Verified:** 2026-08-20 against `src/banking_rag/rag_workflow.py`, `src/banking_rag/ingestion.py`
**Sources:** `risk-analysis.md` R001/R002/R003/R004, `src/banking_rag/rag_workflow.py`, `src/banking_rag/ingestion.py`
**Owner:** Scribe

---

## Scope

How to handle a suspected security event in the Banking RAG Chatbot v1: prompt injection,
PII leak, or a scope-creep response that reached a user.

> **v1 detection baseline is weak.** There is no query-side injection filter, no
> query-side PII detection, no structured audit log, and no alerting. Incidents must be
> detected by operators/users observing bad output, not by the system. This runbook
> reflects that reality; the per-risk "implemented / not implemented" columns are
> authoritative.

---

## 1. Suspected prompt injection (R002)

**What it looks like:** a user query such as "ignore previous instructions and …"
causes the model to break scope, reveal the system prompt, or produce non-banking
content, and the abstention rewrite **didn't** fire (the response slipped through).

### Immediate response

1. **Capture the offending exchange:** the query, the full response, the `session_id`,
   and the config (`llm.provider`, `llm.model`, `temperature`). Without structured
   logging this is manual — reproduce via the CLI with `--debug` if needed.
2. **Stop the API** if the attack is ongoing or the output is dangerous (e.g., leaked
   PII). Otherwise you may leave it up but triage immediately.

### Triage

- Inspect `RAGWorkflow._should_abstain()` triggers: the response slipped because none of
  the hardcoded phrases (`"transactional"`, `"account-specific"`, `"i don't know"`, …)
  appeared in the output. R002 mitigation 1 (input sanitization / injection keyword
  filter) **is not implemented in v1** — there is no input-side check to defeat.
- Consider raising `llm.temperature` down (e.g., 0.4) and/or switching to a more
  compliant model. Scope control in v1 is entirely the system prompt + post-hoc
  abstention scan; injecting a stronger system prompt is a code change in
  `_load_system_prompt()`.

### Remediation options (v1, manual)

- Tighten the abstention trigger list in `_should_abstain()` for phrases observed in the
  attack. (Quick but brittle.)
- Add an input-side keyword filter in `RAGWorkflow.run()` before retrieval (R002
  mitigation 1) — a v2 feature you can back-port.
- Record the incident and the patch in an ADR under `docs/decisions/`.

### Disclosure

v1 has no user-auth or audit trail; there is no per-user forensics. Log the event in your
own incident ledger and update `docs/compliance/audit-trail.md` once structured logging
exists.

---

## 2. Suspected PII leak in a response (R003)

**What it looks like:** a generated answer contains an account number, SSN, card number,
or real customer data that should not be in the index (or was not caught at ingestion).

### Immediate response

1. **Stop the API.** A PII leak is the most severe event type.
2. **Preserve evidence:** copy the offending response and the source `chunk_id`s in the
   citations. Identify which source document contributed the PII.

### Triage

- Check `./data/quarantine/` — did this chunk's content get rejected at ingestion? If it
  is in the index despite containing reject-list PII, the `PIIDetector` patterns missed
  it (e.g., a format variant not covered by the regexes in `ingestion.py`).
- `PIIDetector` patterns are: `ssn` (`\b\d{3}-\d{2}-\d{4}\b`), `credit_card`
  (`\b(?:\d{4}[- ]?){3}\d{4}\b`), `email`, `phone`
  (`\b\d{3}[-.]?\d{3}[-.]?\d{4}\b`), `account_number` (`\b\d{8,20}\b`). Any PII outside
  these shapes (e.g., unformatted 7-digit account ids, international formats) is not
  detected.

### Remediation

1. Remove the offending source document from the corpus.
2. Add a pattern to `PIIDetector.PATTERNS` for the missed shape (and to `REJECT_TYPES`
   if it should reject rather than accept).
3. Re-index from a clean corpus — see `reindexing.md`. (`delete_chunk` doesn't remove the
   vector; a full rebuild is required.)
4. Review `./data/quarantine/` and delete quarantined files once triaged (do not retain
   PII).

### Prevention going forward

- Do not ingest real customer data in v1 (R003 mitigation 4). Use only the sample data
  in `sample_data.py` or sanitized public FAQs.
- Consider adding `PIIDetector.redact()` to the query path and the response path if
  this risk recurs. **Not implemented in v1** — see `docs/compliance/pii-handling.md`.

---

## 3. Scope-creep response reached a user (R004)

**What it looks like:** the bot answered an out-of-scope question ("What's my balance?")
with fabricated personal-account information instead of the standard refusal.

### Triage

- The abstention trigger scan (`_should_abstain`) rewrites responses containing
  `"account-specific"`, `"personal information"`, `"transactional"`, etc., to a fixed
  refusal. If a scope-creep answer slipped through, the model produced a plausible
  out-of-scope answer **without** using those exact phrases.
- This can happen when the LLM directly provides account-style info without hedging
  language, especially with high `temperature`.

### Remediation

- Lower `temperature`, swap to a more conservative model (`llm-provider-swap.md`), and/or
  add the observed phrases to the abstention trigger list.
- For a structural fix, add an intent classifier on the query path (R004 mitigation 1) —
  a v2 feature; not present in v1.

---

## 4. Incident logging (v1)

Because there is no structured audit log, record each incident manually with:

- Date/time, reporter, session_id, query, response, retrieved `chunk_id`s.
- Risk id (R001/R002/R003/R004) and the specific gap that allowed it.
- Remediation taken and the resulting code/config/ADR change.

Store these in your team's incident tracker. When v2 structured logging lands, import
the ledger into `docs/compliance/audit-trail.md`.

---

## 5. When to escalate

Escalate to a human decision-maker (use `kanban_block(kind="needs_input", reason=...)` on
the relevant task) if:

- A PII leak involved real customer data (R003 + real-data use case).
- An injection attack succeeded repeatedly despite the system prompt.
- You need to change the security architecture (add input guards, query-side PII
  detection, rate limiting) — these are v2 scope and should not be silently
  bolted on during incident response.

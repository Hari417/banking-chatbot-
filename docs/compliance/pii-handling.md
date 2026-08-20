# PII Handling

**Version:** 1.0
**Status:** Current
**Last Verified:** 2026-08-20 against `src/banking_rag/ingestion.py`, `src/banking_rag/rag_workflow.py`
**Sources:** `src/banking_rag/ingestion.py`, `risk-analysis.md` R003, `component-specification.md` §3.1, `INGESTION_SPEC.md`
**Owner:** Scribe

---

## v1 posture in one line

PII detection runs **at document ingestion only**, with regex patterns. It does **not**
run on user queries and does **not** run on generated responses. v1 uses **no real
customer data** (R003 mitigation 4); the sample data in `sample_data.py` is the default
corpus.

## What counts as PII here

Banking-domain PII, as hardcoded in `ingestion.py::PIIDetector`:

| Type | Pattern | Action |
|------|---------|--------|
| `ssn` | `\b\d{3}-\d{2}-\d{4}\b` | **Reject** |
| `credit_card` | `\b(?:\d{4}[- ]?){3}\d{4}\b` | **Reject** |
| `account_number` | `\b\d{8,20}\b` | **Reject** |
| `email` | `\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b` | Accept |
| `phone` | `\b\d{3}[-.]?\d{3}[-.]?\d{4}\b` | Accept |

> **Note:** The `account_number` pattern (`\b\d{8,20}\b`) is broad — any 8–20 digit
> number is treated as a potential account number and the chunk rejected. This is
> intentional over-inclusion on the reject side but will false-positive on numeric data
> like interest rates expanded to 8+ digits, large routing/aggregate figures, etc.

## Detection mechanism

- **Library:** regex (`re` in the standard library). The risk register's
  "Presidio or regex" open question (`docs/DOCUMENTATION_OUTLINE.md` §Open Questions #3)
  is **resolved by the implementation**: v1 chose **regex**, not Microsoft Presidio.
  This keeps the dependency surface minimal at the cost of pattern coverage.
- `PIIDetector.detect(text)` returns `PIIResult(has_pii, pii_types, action)` where
  `action` is `"reject"` if any reject-type is found, else `"accept"`.
- `PIIDetector.redact(text)` returns text with SSN/credit-card/email/phone replaced by
  `[SSN_REDACTED]` / `[CARD_REDACTED]` / `[EMAIL_REDACTED]` / `[PHONE_REDACTED]`.

## What happens at ingestion (stage 4)

`stage_4_pii_validation` runs `detect()` on each chunk after chunking:

- **Reject** → the chunk is written to `./data/quarantine/quarantined_<chunk_id>.json`
  with its content and metadata, and **excluded from the FAISS index**.
- **Accept** → the chunk passes to stage 5.

### Redaction gap (important)

The R003 mitigation calls for redaction before indexing. In the v1 code path:

```python
if pii_result.has_pii and pii_result.redacted_content:
    chunk.content = pii_result.redacted_content
valid_chunks.append(chunk)
```

But `PIIDetector.detect()` **never populates `redacted_content`** (the `PIIResult`
dataclass defaults it to `None`). So even accept-list PII (email, phone) reaches the
index **unredacted**. To actually redact, you must either:

1. Extend `detect()` to set `redacted_content = self.redact(text)` for accept cases, or
2. Call `PIIDetector.redact()` on chunk content explicitly before persistence.

**v1 ships without this wired.** Email addresses and phone numbers in source documents
will be embedded and retrievable as-is. See `docs/evaluation/known-limitations.md`.

## What does NOT happen with PII in v1

| Path | PII detection? | PII redaction? |
|------|-----------------|----------------|
| Document ingestion (reject types) | **Yes** (quarantine) | n/a (rejected) |
| Document ingestion (accept types: email/phone) | **Yes** (detected, accepted) | **No** (passes through) |
| User query on `/chat` | **No** | **No** |
| Generated response | **No** | **No** |
| Logs | **No** (queries are not logged in detail; DEBUG lines may include chunk text — see `docs/runbook/log-rotation-and-retention.md`) | n/a |

> A user typing an account number into `/chat` will not be blocked at input. The query
> is embedded and sent to the LLM verbatim. R003 mitigations 2–3 (query scrubbing) are
> **not implemented**.

## Storage

- The FAISS index stores **embeddings** of chunk text, not the raw text; the raw text is
  in `metadata.json` keyed by `chunk_id`. R003 acknowledges embedding PII is "less
  retrievable" — but the plaintext is still recoverable from `metadata.json`, so this
  is not a strong control. Honestly recorded as a residual risk.
- Quarantined chunks are written to disk **with their full content** (including the PII
  that triggered rejection). Operators must review and delete `./data/quarantine/`
  files rather than retain them.

## What you should do

- For v1, use only the sample data or sanitized public FAQs. **Do not ingest real
  customer documents** (R003 mitigation 4).
- If you must handle documents that may include emails/phones, pre-redact them (e.g., run
  `PIIDetector.redact()` in your ingestion script) before calling the pipeline, since
  the pipeline does not auto-redact.
- Periodically empty `./data/quarantine/` — it accumulates PII by design and should not
  be a long-term store.

## v2 path

- Query-side PII detection + redaction (R003 mitigations 2–3).
- Response-side PII scan before returning to the user.
- Optional upgrade to Presidio for richer entity coverage (the open question is
  resolved for v1 in favor of regex; revisit for v2 if coverage gaps bite).
- Structured `security.pii_detected` audit events (R003 mitigation 5) — see
  `docs/compliance/audit-trail.md`.
- An open decision still pending: **audit-log retention period** (R016 mitigation 3) —
  see `docs/DOCUMENTATION_OUTLINE.md` open questions. Not decided for v1.

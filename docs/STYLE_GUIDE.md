# Banking RAG Chatbot — Style Guide & Standards

**Version:** 1.0
**Date:** 2026-08-20
**Author:** Scribe (Documentation)
**Status:** Draft — for review by the orchestrator

---

## Purpose

This guide defines the standards every contributor to the Banking RAG Chatbot
follows for:

1. **Code comments** — what to document in source and what not to
2. **Logging** — structured-log format, levels, fields, and audit requirements
3. **Change tracking** — commit messages, changelog, and decision records
4. **Documentation conventions** — markdown structure, file headers, linking
5. **Compliance & auditability** — how the above three combine to produce an
   auditable system aligned with the banking-domain risk mitigations in
   `risk-analysis.md`

These standards are defined now, before implementation accelerates, so that Forge
writes code that is already audit-ready and Scribe documents code that already
follows a consistent style.

---

## Scope

Applies to all Python source, configuration, and documentation under
`/home/hari/Desktop/Banking/`. The existing upstream artifacts (ARCHITECTURE.md,
component-specification.md, etc.) were written before this guide existed; they are
not retroactively reformatted, but new or edited sections of them should conform.

---

## 1. Code Comment Standards

### 1.1 Principle

Comments explain **why**, not **what**. The code already says what it does. A comment
that restates the code is noise and rots faster than the code.

### 1.2 Module docstrings (required)

Every Python module begins with a docstring:

```python
"""FAISS index persistence: save, load, and verify the vector index.

Responsibility:
    Persist the FAISS index and its metadata mapping to disk and reload them,
    with a SHA-256 checksum so corruption (risk R008) is detected at load time.

Dependencies:
    configuration, embedding generation

Sources:
    component-specification.md §6.1, risk-analysis.md R008
"""
```

- **Responsibility** — one sentence on what this module owns.
- **Dependencies** — upstream modules this one imports (mirrors
  `DEPENDENCY_GRAPH.md`).
- **Sources** — the upstream artifact(s) this module implements. This is the
  audit link: a reviewer reading the module can find the design decision behind it.

### 1.3 Public API docstrings (required)

Every public function, class, and method that appears in an interface defined in
`component-specification.md` carries a docstring with:

```python
def retrieve(query: str, k: int = 5, filter: dict | None = None) -> list[RetrievedChunk]:
    """Embed the query and return the top-k chunks from the FAISS index.

    Args:
        query: The user's natural-language question.
        k: Number of results to return. Defaults to 5 (retrieval.top_k_final).
        filter: Optional metadata filter, e.g. {"source": "loan_policy.pdf"}.

    Returns:
        Retrieved chunks sorted by descending score. Returns an empty list if
        no chunks clear the score threshold (abstention trigger, see §10.2).

    Raises:
        IndexError: If the FAISS index is not loaded.
        ValueError: If the query is empty after sanitization.
    """
```

- Use the Numpy/Sphinx-compatible `Args / Returns / Raises` convention so docstrings
  can be extracted into API docs later.
- Document the **abstention** behavior explicitly wherever a low-confidence path
  exists — this is a banking compliance requirement, not a style choice.

### 1.4 Inline comments (sparingly)

Use inline comments only when:

| Use it for | Don't use it for |
|------------|-----------------|
| Non-obvious business rule ("FAISS inner-product requires L2-normalized vectors") | Restating the line ("# add two numbers") |
| A decision that defeated an obvious alternative ("# RRF with k=60 beats linear fusion, tested in eval set B") | TODO without a ticket reference |
| A risk reference ("# R003: redact PII before this point") | Commented-out code |
| Linking a magic number to its source ("# chunk_size=512 per component-specification.md §7.2") | Speculation about future behavior |

### 1.5 TODO / FIXME / NOTE

- `# TODO(forge): <action> — see t_<card-id>` — ties the comment to a Kanban card.
- `# FIXME(forge): <bug> — see t_<card-id>` — defect in flight, traced to card.
- `# NOTE(scribe): <doc gap> — see docs/.../<file>` — documentation follow-up.
- A bare `# TODO` with no owner and no card reference is **not** acceptable. It
  will rot and no one will know who owns it.

### 1.6 Security-sensitive comments

Any code that touches PII detection, prompt-injection filtering, abstention, or
scope enforcement carries a comment pointing at the risk it mitigates:

```python
# R002 (Critical): prompt-injection filter must run BEFORE the query reaches
# the retriever. Bypassing this is a security incident — see
# docs/compliance/scope-enforcement.md.
```

This makes security boundaries visible in `git blame` and in code review.

### 1.7 What NOT to comment

- Type information already in the signature.
- Standard library behavior ("# Counter counts occurrences").
- Code you deleted (the git history preserves it).
- Performance speculation you haven't measured.

---

## 2. Logging Standards

### 2.1 Rationale

The risk register (`risk-analysis.md`) requires auditability of every query and
every response (R016 mitigation 3) and log anonymization of PII (R003 mitigation
5). Logs are therefore a compliance artifact, not a debugging afterthought. The
format below is fixed so that an auditor can extract the trail for any session
without custom parsing.

### 2.2 Format: structured JSON, one event per line

Every log entry is a single JSON object on one line (newline-delimited JSON, the
format Splunk, Loki, and `jq` all consume natively):

```json
{"timestamp":"2026-08-20T15:30:00.123Z","level":"INFO","event":"query.received","session_id":"a1b2...","request_id":"r9f8...","module":"security.input_guard","msg":"query accepted"}
```

### 2.3 Required fields

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `timestamp` | ISO-8601 UTC with millis | yes | `Z` suffix, never local time |
| `level` | enum | yes | one of `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `event` | string | yes | dotted name (see 2.5) |
| `module` | string | yes | python module emitting the log, e.g. `retrieval.basic` |
| `msg` | string | yes | human-readable one-liner |
| `session_id` | string | yes if a session context exists | UUID, never the raw user query |
| `request_id` | string | yes for `/chat` and `/ingest` | per-request correlation id |
| `duration_ms` | int | yes for any timed operation | wall-clock duration |
| `pii_flag` | bool | yes for security-layer events | true if PII was detected (redacted content is never logged) |
| `abstained` | bool | yes for generation events | true if the system refused to answer |
| `risk_ref` | string | optional | the risk id this event relates to, e.g. `"R003"` |

### 2.4 Log levels

| Level | Use for | Example |
|-------|---------|---------|
| `DEBUG` | Detailed internal state, off in production | "BM25 scored 240 docs" |
| `INFO` | Normal operation — the audit trail events | "query.received", "response.sent" |
| `WARNING` | Degraded but functional; a risk mitigation fired | "injection_filter.matched", "rate_limited" |
| `ERROR` | Operation failed but the system stays up | "faiss.load_failed", "llm.timeout" |
| `CRITICAL` | System unusable or a security boundary breached | "pii_leak_detected" |

A `CRITICAL` `pii_leak_detected` event MUST also fire an alert (see runbook
`incident-response.md`).

### 2.5 Event names

Dotted, lowercase, phrase = `<domain>.<action>`:

| Domain | Events |
|--------|--------|
| `query` | `query.received`, `query.rejected`, `query.classified` |
| `security` | `security.pii_detected`, `security.injection_matched`, `security.rate_limited` |
| `retrieval` | `retrieval.dense_done`, `retrieval.sparse_done`, `retrieval.fused`, `retrieval.reranked`, `retrieval.empty` |
| `generation` | `generation.prompt_built`, `generation.llm_called`, `generation.validated`, `generation.abstained`, `generation.citation_built` |
| `ingestion` | `ingestion.started`, `ingestion.doc_loaded`, `ingestion.chunked`, `ingestion.embedded`, `ingestion.indexed`, `ingestion.completed` |
| `session` | `session.created`, `session.expired`, `session.reset` |
| `system` | `system.startup`, `system.faiss_loaded`, `system.health_ok`, `system.health_fail` |

Adding a new event name requires updating this table in the same PR. The event
namespace is a contract with the auditor.

### 2.6 What is NEVER logged

- The raw user query (it can contain PII — R003). Log the `session_id` and a
  short hash instead; the query is recoverable from the audit store with
  appropriate access control.
- The LLM system prompt (it is static; in code, not data).
- Full retrieved chunk text (log chunk_id + score only, R003).
- API keys, Ollama host tokens, any secret from `.env`.
- Full user PII (detections are flagged with `pii_flag:true`, content redacted).

### 2.7 Implementation

- Use the standard `logging` library with a JSON formatter (e.g. `python-json-logger`).
- Configure via the `logging` block in `config.yaml` (MODULE_BREAKDOWN.md §1):
  - `level`, `format`, `output` (file path in `./logs`), `rotation`, `retention`.
- A single `setup_logging()` call in the configuration module initializes loggers.
- No bare `print()` in production code paths — `print` bypasses the formatter
  and the audit trail.

### 2.8 Audit-trail linkage

Every `/chat` request produces, in order, these INFO events, all sharing the
same `request_id`:

```
query.received → security.* (0+ events) → query.classified →
retrieval.dense_done → retrieval.sparse_done → retrieval.fused →
retrieval.reranked → generation.prompt_built → generation.llm_called →
generation.validated → (generation.abstained OR generation.citation_built) →
response.sent
```

An auditor with the `request_id` can reconstruct the full decision trail. This
is the operationalization of R016 mitigation 3.

---

## 3. Change Tracking Standards

### 3.1 Commit messages

Format:

```
<type>(<scope>): <subject>

<body — why, what changed, what risk id it relates to>

<footer — refs t_<card-id>, BREAKING CHANGE, reviewer>
```

- **type** — one of `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `sec`,
  `perf`.
- **scope** — the module or doc area: `faiss`, `retrieval`, `generation`,
  `security`, `config`, `ui`, `docs`, `runbook`.
- **subject** — imperative, ≤ 50 chars, lowercase first word.
- **body** — wrapped at 72 cols; explain the why, not the what. If the change
  touches a mitigated risk (`risk-analysis.md`), name the risk id.
- **footer** — the Kanban card id this work belongs to.

Example:

```
feat(security): redact PII before retrieval dispatch

PII detected in a user query was previously logged in plaintext in the
query.received event. Per R003 mitigation 5, queries are now hashed before
logging and the raw value is held only in-memory for the request lifetime.

Refs t_<forge-implementation-card-id>
Reviewed-by: <sentinel>
```

### 3.2 Conventional-commit scope map

| Scope | Maps to |
|-------|---------|
| `faiss` | FAISS index create/persist/load |
| `retrieval` | dense, sparse, fusion, rerank |
| `generation` | prompt build, LLM call, validate, cite, abstain |
| `security` | input guard, PII, injection, rate limit |
| `config` | configuration loading/schema |
| `ui` | Streamlit chat interface |
| `session` | session store |
| `ingestion` | loaders, cleaners, chunker, embedder |
| `docs` | any file under `docs/` or top-level `.md` |
| `runbook` | any file under `docs/runbook/` |

### 3.3 Changelog

`CHANGELOG.md` lives at the project root and is maintained by Scribe at each
release/sprint boundary. Format follows Keep a Changelog:

```markdown
## [Unreleased]
### Added
- Initial documentation outline and style guide (t_5984901f)

## [0.1.0] - 2026-08-XX
### Added
- Configuration management system (t_<card>)
- LLM OpenAI-compatible interface (t_<card>)
```

- "Added", "Changed", "Deprecated", "Removed", "Fixed", "Security" sections.
- Each entry cites the Kanban card id so the board and the changelog cross-reference.
- `Security` entries cite the risk id from `risk-analysis.md` they address.

### 3.4 Decision records (ADRs)

Architecture decisions are recorded as ADRs in `docs/decisions/ADR-NNNN-*.md`
using the template in the documentation outline. Every ADR has:

- **Status** — Proposed → Accepted → (possibly Superseded)
- **Context** — why this decision is being made now
- **Alternatives** — what else was considered (from `technology-rationale.md`)
- **Decision** — what was decided
- **Rationale** — why, with evidence
- **Consequences** — what becomes easier / harder, which risks it touches
- **Sources** — the upstream artifacts that fed the decision

A decision that reverses a prior ADR marks the old one `Superseded by ADR-NNNN`
and the new one names the old in its context.

### 3.5 Branching

Tracked by the orchestrator, not by Scribe, but for the record:

- Work happens in branches named `<scope>/<short-id>-<card-id>`.
- Trivial doc edits (`docs:` commits) may go directly to the default branch with
  a review.
- Security-sensitive changes (`sec:` or anything touching R002/R003/R004) require
  a reviewer — Sentinel for technical review, Hiccup for process.

---

## 4. Documentation Conventions

### 4.1 File headers

Every documentation file begins with:

```markdown
# <Title>

**Version:** <semver>
**Status:** Planned | Draft | Current | Superseded
**Last Verified:** <date> against <rev / artifact>
**Sources:** <upstream artifacts this doc derives from>
**Owner:** <profile>
```

The `Status` field is the single source of truth for whether a document can be
trusted to match the implementation. See `DOCUMENTATION_OUTLINE.md` §Status
Conventions.

### 4.2 Markdown style

- ATX-style headers (`#`, not `=====` / `-----`).
- One sentence per line in source is acceptable for prose; tables and code blocks
  stay rigid.
- Code blocks carry a language fence ( ```python, ```yaml, ```bash ).
- Links: prefer relative links within the repo, not absolute paths, so docs
  survive a repo move: `[component spec](../component-specification.md)`.
- No raw HTML in markdown except for small tables where markdown tables are
  unreadable.
- Emphasis (`*italics*`) for new terms on first use; `**bold**` only for the
  "Required/Status" front-matter style in this guide.

### 4.3 Terminology

Use the terms already fixed in the upstream artifacts. A short glossary:

| Term | Meaning | Source |
|------|---------|--------|
| Chunk | A contiguous slice of a document, the unit of retrieval | MODULE_BREAKDOWN.md §3 |
| RetrievedChunk | A chunk returned by the retriever with score + metadata | MODULE_BREAKDOWN.md §6 |
| Citation | A `[N]` marker in a response mapped to a source excerpt | component-specification.md §4.8 |
| Abstention | The bot returning "I don't have enough information…" | component-specification.md §10.2 |
| Grounding | The response refers only to retrieved context | risk-analysis.md R001 |
| Hybrid retrieval | Dense (FAISS) + Sparse (BM25) fused via RRF | technology-rationale.md §2.5 |

Introducing a new term: define it on first use, then add it to this table in the
same PR.

### 4.4 Tone and audience

- **Architecture docs** — for engineers and architects. Precise, terse.
- **Setup / runbook docs** — for operators. Imperative, numbered, copy-paste-able.
- **User guide** — for end users of the chatbot. Plain, no internal jargon, no
  references to risk ids.
- **Compliance docs** — for auditors and reviewers. Passive where appropriate,
  every claim cited to a risk id or source.

### 4.5 Accuracy over polish

Per the Scribe charter: never invent requirements, features, configuration, or
decisions. If a documented claim is disputed, it goes to Skeptic for
verification, not silently "fixed." If a document and the code disagree, the
document is marked `Draft` and Forge is asked to confirm which is authoritative.

---

## 5. Compliance & Auditability

This section ties the three standards above together so that the system is
auditable end-to-end. It operationalizes the mitigations in `risk-analysis.md`
for R001 (hallucination), R002 (prompt injection), R003 (PII), R004 (scope),
and R016 (regulatory gap).

### 5.1 The audit claim

For any request the system has handled, a reviewer can reconstruct:

1. **What was asked** — session_id + query hash (not raw text) at
   `query.received`.
2. **Whether it was safe to answer** — `security.*` events (PII, injection,
   rate limit).
3. **What the system decided it was** — `query.classified` with intent.
4. **What evidence was retrieved** — `retrieval.*` events with chunk_ids and
   scores, not chunk text.
5. **What was sent to the LLM** — `generation.prompt_built` (template + context
   ids, not the full text for PII safety).
6. **What was returned** — `generation.validated` + `generation.citation_built`
   or `generation.abstained` + `response.sent`.
7. **Whether abstention fired** — `abstained:true` on the generation event.
8. **Why** — the `risk_ref` field on any event that fired a mitigation.

All of this is keyed by `request_id` so the trail is one `grep` away.

### 5.2 Scope enforcement is logged

R004 (information disclosure beyond scope) mitigations produce, by design, these
log events that an auditor can count:

- `query.rejected` with `reason:"out_of_scope"` — for "what's my balance" queries.
- `generation.abstained` with `reason:"insufficient_evidence"` — for low-confidence.
- `generation.validated` with `grounded:true` — for answers that went out.

A spike in `query.rejected` events is a leading indicator of scope confusion that
the compliance owner should investigate.

### 5.3 PII handling is logged by exception

R003 mitigations produce:

- `security.pii_detected` with `pii_flag:true` whenever the input guard fires.
- The **content** is never logged; only the flag and the redacted hash.
- A `CRITICAL pii_leak_detected` event is reserved for the case where PII is
  detected in the *response* (should not happen; if it does, it is an incident).

### 5.4 Hallucination mitigation is logged

R001 mitigations produce:

- `generation.validated` with `grounded:true|false`.
- `generation.abstained` when the response validator fails grounding.
- A `WARNING` event is logged and the response is held for human review if
  grounding fails twice with retry.

### 5.5 Retention

- Audit logs (all INFO and above security/generation events) are retained for the
  period defined in `docs/compliance/audit-trail.md` — **to be decided** (see
  Open Questions in `DOCUMENTATION_OUTLINE.md`). Until then, default to
  retaining for the life of the v1 prototype (local-dev, single user).
- DEBUG logs are rotated daily.
- No production PII retention for v1 (no real customer data is used).

### 5.6 Reviewer expectations

When Sentinel or a human reviews a change:

- A `sec:` commit touching R002/R003/R004 must show the corresponding log
  events fire in tests.
- A `feat:` commit must update the relevant doc in `docs/` to at least `Draft`.
- A doc marked `Current` must list the commit/rev it was verified against.

---

## 6. Configuration of these standards

These standards live in source:

- `pyproject.toml` (or `.flake8`, `ruff.toml`) enforces code style lint.
- A `.gitmessage` template in the repo root seeds commit format; `git config
  commit.template .gitmessage` activates it.
- The JSON-log formatter is configured in the configuration module per §2.7.
- `CHANGELOG.md` and `docs/decisions/` repository the human-readable change trail.

Forge adds the tooling; Scribe owns this guide and the documentation outline.

---

## Quick reference

- **Comments:** module docstring with Responsibility/Dependencies/Sources; public
  API docstrings with Args/Returns/Raises; inline comments only for the non-obvious.
- **Logs:** structured JSON, one event per line, required fields, never log raw
  query or PII, every `/chat` request is a `request_id`-linked event trail.
- **Commits:** `type(scope): subject` + body naming the risk id + `Refs t_<card>`.
- **Docs:** front-matter header with Status (Planned/Draft/Current/Superseded),
  relative links, cited sources, "Current" only after verification against code.
- **Auditability:** for any request, an auditor can reconstruct the decision
  trail from INFO logs keyed by `request_id`, with `risk_ref` on mitigations.

---

*End of Style Guide — Version 1.0*

# Disclaimer — Not for Production Use

**Version:** 1.0
**Status:** Current
**Last Verified:** 2026-08-20 against `src/`, `config.yaml`, `risk-analysis.md` R016
**Sources:** `risk-analysis.md` R016, `ROADMAP_SUMMARY.md`, `component-specification.md` §10
**Owner:** Scribe

---

## The disclaimer

> The Banking RAG Chatbot v1 is a **local-first prototype** for answering general
> banking FAQ questions from a controlled knowledge base. It is **not a production
> system**, is **not certified for any regulatory regime**, and **must not be exposed to
> real customer data or real banking operations**. Use it as a reference implementation
> and a testbed for RAG in the banking domain.

## Where this must be visible

The disclaimer should appear wherever a user or operator interacts with the system.
v1 placement status:

| Surface | Present in v1? | Note |
|---------|----------------|------|
| README.md | To be added (this doc links from the README) | Recommended text below |
| API `/chat` response footer | No | v2 item; responses currently carry only the answer+citations |
| CLI banner | No | The CLI banner describes scope but not the not-for-production notice |
| UI sidebar | n/a | No Streamlit UI exists in v1 |

### Recommended disclaimer text (drop into README and the API footer when added)

> **Prototype — Not for production use.** This system answers general banking FAQ
> questions from a loaded knowledge base. It cannot access account balances, perform
> transactions, or authenticate users. It has not undergone compliance review
> (R016), does not implement query-side PII protection, and does not produce a
> structured audit trail. Do not feed it real customer data. Engage compliance and
> security teams before any deployment beyond local single-user use.

## v1 scope limitations (summary)

- **Single-user, local** — no authentication, authorization, or multi-tenant isolation.
- **No real customer data** — sample data only (R003 mitigation 4).
- **No transactional features** — by design (the project constraint). `features.
  enable_transactions` is hardcoded false; even so, no code reads it, so it is a
  documentation guard, not an enforcement point (`docs/compliance/scope-enforcement.md`).
- **No structured audit trail** — stdlib text logs only; no `request_id`, no event
  taxonomy (`docs/compliance/audit-trail.md`).
- **No query-side security** — no input PII detection, no injection filter, no rate
  limiting (`docs/compliance/scope-enforcement.md`, `docs/setup/configuration.md`).
- **Grounding validation is a lexical heuristic** — can pass fabricated content
  (`docs/evaluation/known-limitations.md`).
- **Sessions are in-memory** — lost on restart; not multi-turn (R007).
- **`/ingest` is a stub** — does not ingest documents (`docs/api/ingest-endpoint.md`).

## v2 compliance path (per R016 mitigation 4)

Before any non-local deployment, the following must be in place — none are present in v1:

1. **Compliance review** — engage legal/compliance to define the regulatory regime
   (GDPR/CCPA/etc.) the deployment falls under.
2. **Query-side security layer** — input PII detection, injection filter, rate limiting
   (config flags exist, implementation does not).
3. **Structured audit logging** with a decided retention period (`audit-trail.md`).
4. **Real grounding validation** — a response validator that checks semantic grounding,
   not token overlap.
5. **Authn/Authz** — the v1 API has none.
6. **Persisted sessions** with TTL and a memory cap (config flags exist, ignored).
7. **Disclaimer surface** on every user-facing surface — see the table above.
8. **Documented decision records** for every security choice under `docs/decisions/`.

Until these exist, v1 is **not** a candidate for any production or regulated deployment.
The fact that the underlying RAG architecture is sound and modular does not override the
absence of the operational and compliance controls above.

## Source references

- `risk-analysis.md` R016 (regulatory gap) mitigation 4 — "engage compliance before
  production."
- `ROADMAP_SUMMARY.md` — v1 → v2 evolution path including the hardening items above.
- `docs/DOCUMENTATION_OUTLINE.md` open questions — audit-log retention period is
  undecided; PII-detection library resolved to regex for v1.
- `docs/STYLE_GUIDE.md` §5.5 — v1 default retention is "life of the v1 prototype."

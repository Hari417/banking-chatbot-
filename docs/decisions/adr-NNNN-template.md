# ADR-NNNN: <Decision Title>

**Status:** Proposed | Accepted | Superseded
**Date:** YYYY-MM-DD
**Deciders:** <profiles / roles>
**Supersedes:** <ADR id, if any>
**Superseded by:** <ADR id, if any>

---

## Context

What is the issue / force / constraint that requires a decision now? Cite the upstream
artifacts and risk ids that motivate it.

## Decision

The choice made, stated in one or two clear sentences.

## Alternatives Considered

- **A1:** … — rejected because …
- **A2:** … — rejected because …

## Rationale

Why this alternative won. Include evidence from tests, eval runs, or risk analysis. Name
the risk id(s) touched (R001, R002, …) where relevant.

## Consequences

- **Becomes easier:** …
- **Becomes harder:** …
- **Risks affected:** …
- **Follow-ups:** …

## Sources

- `risk-analysis.md` R0NN
- `technology-rationale.md` §N
- `component-specification.md` §N
- Implementation: `src/...`

---

## Decisions to record (pre-identified from upstream artifacts)

These were resolved during architecture and should be captured as ADRs as they are
ratified:

| Proposed id | Decision | Source |
|-------------|----------|--------|
| ADR-0001 | FAISS over PostgreSQL / Chroma (constraint: no Postgres) | `technology-rationale.md` |
| ADR-0002 | LangGraph single-workflow over multi-agent (constraint: no multi-agent) | `technology-rationale.md` |
| ADR-0003 | Standard RAG over CAG (constraint: no CAG) | `technology-rationale.md` |
| ADR-0004 | OpenAI-compatible LLM interface (provider-agnostic) | `component-specification.md` |
| ADR-0005 | `all-MiniLM-L6-v2` for v1 embeddings (speed; upgrade path documented) | `technology-rationale.md` |
| ADR-0006 | Hybrid retrieval (dense + BM25 + RRF) as v1 default | `technology-rationale.md` |
| ADR-0007 | In-memory session store for v1 (accepted risk R007) | `risk-analysis.md` |
| ADR-0008 | File-based persistence (no Postgres; upgrade to SQLite v2) | `technology-rationale.md` |
| ADR-0009 | Regex (not Presidio) for PII detection in v1 | `docs/compliance/pii-handling.md` (resolved by implementation) |

> **Note on ADR-0006:** The implementation actually uses normalized weighted fusion
> (`0.7 dense + 0.3 sparse`), not RRF — see `docs/evaluation/known-limitations.md` A3.
> Record ADR-0006 honestly: the *intended* v1 default was RRF; the *implemented* v1
> default is weighted normalized fusion. Either re-align the code to ADR-0006 or update
> ADR-0006 to match the code.

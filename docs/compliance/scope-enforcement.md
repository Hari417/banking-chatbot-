# Scope Enforcement

**Version:** 1.0
**Status:** Current
**Last Verified:** 2026-08-20 against `src/banking_rag/rag_workflow.py`, `config.yaml`
**Sources:** `src/banking_rag/rag_workflow.py`, `config.yaml`, `risk-analysis.md` R004, `component-specification.md` §3
**Owner:** Scribe

---

## The scope contract

The system is **FAQ-only**. It must answer general questions about banking policies,
products, fees, loans, eligibility, procedures, interest rates, and FAQs. It must
**not** answer questions about account balances, transactions, card operations, customer
authentication, real customer data, or any transactional banking functionality.

## How enforcement is (and is not) implemented in v1

| Planned mitigation (R004 + spec §3) | Implemented in v1? | Where |
|------------------------------------|--------------------|-------|
| System prompt explicitly states the limits | **Yes** | `RAGWorkflow._load_system_prompt()` |
| Intent classifier on the query path (detect `FAQ_QUERY` vs `IRRELEVANT`) | **No** | — |
| Input-side keyword / injection filter | **No** | — |
| Rate limiting | **No** | `config.yaml` flags ignored |
| Out-of-scope query rejection (`query.rejected` event) | **No** | no structured logging |
| Scope-violation response rewrite | **Yes (post-hoc)** | `RAGWorkflow._should_abstain()` |
| `query.rejected` audit-log entry | **No** | — |
| `features.enable_transactions: false` enforcement | **No (documentation-only)** | no code reads the flag |

### What actually enforces scope in v1

1. **System prompt** (`_load_system_prompt`) — instructs the model to answer only from
   the provided context, say "I don't know" when uncertain, cite sources, keep answers
   concise, and refuse transactional / personal-account requests.

2. **Post-hoc abstention trigger scan** (`_should_abstain`) — after generation, the
   response is scanned lowercase for any of these triggers:
   `["i don't know", "cannot answer", "not enough information", "i cannot provide",
   "outside my knowledge", "transactional", "account-specific", "personal information"]`.
   If any match, the response is **replaced** with the fixed message:

   > "I cannot provide answers about transactions, account balances, or personal account
   > information. I can only answer questions about general banking policies, products,
   > fees, loans, and procedures. Please ask about those topics."

   and `abstained=True`, `confidence=0.0`.

3. **No-documents abstention** — if retrieval returns zero chunks, the workflow returns
   a rephrase prompt with `abstained=True` instead of calling the LLM.

### What this means in practice

- Scope control is **defensive-by-generation**, not **preventive-by-input**. The query
  is never inspected; the model is trusted to follow the system prompt, and the output is
  scanned for hedging phrases after the fact.
- A model that produces a fluent, scope-violating answer **without using any of the
  trigger phrases** will reach the user. E.g., "Your balance is $1,234" contains none of
  the triggers and would pass unchanged. This is an accepted v1 limitation.
- There is no intent classification, so the system cannot proactively refuse "what's my
  balance?" before generation; it relies on the model's own compliance with the prompt.

## Standard abstention messages you will see

| Situation | Message | `abstained` |
|-----------|---------|-------------|
| No documents retrieved | "I couldn't find any relevant information in the knowledge base. Please try rephrasing your question or ask about banking policies, products, fees, loans, or procedures." | `true` |
| Response contained a scope/abstention trigger | "I cannot provide answers about transactions, account balances, or personal account information. I can only answer questions about general banking policies, products, fees, loans, and procedures. Please ask about those topics." | `true` |
| Pipeline exception | "I encountered an error processing your request. Please try again or contact support." | `true` |

## How to know abstention was triggered vs. an error

- `/chat` response: `abstained: true` with a non-empty `response` is a normal abstention
  (no-context or scope refusal). `abstained: true` with the error message + HTTP 500
  is a pipeline exception.
- `metadata.grounded` is `false` when the grounding validator failed; it does **not**
  by itself force abstention in v1 (only the trigger scan does).

## What would make enforcement robust (v2 path)

- **Input-side intent classifier** before retrieval (R004 mitigation 1) to reject
  out-of-scope queries explicitly and emit a `query.rejected` event.
- **Query-side input guard** (config flag exists, not wired) for injection patterns.
- **Structured `query.rejected` audit event** so a spike in scope violations is
  observable (R004 mitigation 4).
- A real response validator that checks **semantic** grounding, not just trigger
  phrases — see `docs/evaluation/known-limitations.md`.

These are deliberately v2 scope. v1's posture is documented honestly: it relies on the
model following the system prompt and a fragile post-hoc scan.

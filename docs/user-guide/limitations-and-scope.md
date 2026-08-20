# Limitations and Scope

**Version:** 1.0
**Status:** Current
**Last Verified:** 2026-08-20 against `src/banking_rag/rag_workflow.py`
**Sources:** `src/banking_rag/rag_workflow.py`, `risk-analysis.md` R004, `docs/compliance/scope-enforcement.md`
**Owner:** Scribe

---

## What this bot can answer

The Banking RAG Chatbot answers **general** questions about:

- banking policies and procedures
- banking products (savings, checking, CDs, loans, mortgages)
- fees, interest rates, and terms
- eligibility and application steps
- FAQs from the loaded knowledge base
- penalties, overdraft, and repayment policies

## What this bot will NOT answer

It explicitly refuses questions about:

- **your** account balance, history, or transactions
- card operations (lost/stolen card actions, blocking/unblocking)
- real customer authentication or login help
- other customers' data or internal staff information
- transactional banking functionality of any kind

When asked, it returns a fixed refusal: "I cannot provide answers about transactions,
account balances, or personal account information. I can only answer questions about
general banking policies, products, fees, loans, and procedures."

## Other v1 limits to know

- **No conversational memory.** Each question is answered independently. Asking "tell me
  more" right after a previous answer will not use the earlier context. Phrase each
  question self-contained.
- **Answers only from loaded documents.** If the knowledge base doesn't cover a topic,
  you get a rephrase prompt, not a guess. Ingest the documents you want answers from
  (see `docs/setup/document-ingestion.md`).
- **Confidence is a rough proxy.** The `Confidence` value shown is a lexical-overlap
  heuristic, not a calibrated probability. Treat it as a weak hint.
- **Citations refer to chunks, not URLs.** You'll see `[0]: <source> (chunk: chunk_5)`
  — see `understanding-citations.md`.
- **Sometimes it declines a question it could answer.** The scope scan rewrites any
  response containing phrases like "I don't know" or "personal information" to a fixed
  refusal. If a legitimate answer happens to hedge with those words, it is replaced.
  Rephrase the question or try a lower-temperature model.
- **Prototype, not production.** See `docs/compliance/disclaimer.md`. Do not feed it
  real customer data.

## How to tell abstention from an error

| You see | Meaning | What to do |
|---------|---------|------------|
| A clear refusal about transactions/personal info | Scope abstention (normal) | Rephrase as a general banking FAQ |
| "I couldn't find any relevant information..." | No documents retrieved (normal) | Rephrase, or ask in scope; or ingest the source docs |
| "I encountered an error processing your request..." + CLI traceback / HTTP 500 | Pipeline error | Check provider config / API key / index; see `docs/setup/troubleshooting.md` |

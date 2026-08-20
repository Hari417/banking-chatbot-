# Asking Questions

**Version:** 1.0
**Status:** Current
**Last Verified:** 2026-08-20 against `src/banking_rag/rag_workflow.py`, `src/cli.py`
**Sources:** `src/banking_rag/rag_workflow.py`, `src/cli.py`
**Owner:** Scribe

---

## How to ask

### Interactive (CLI)

```bash
python3 src/cli.py chat
```

Type your question at the `You:` prompt and press Enter. The assistant prints the answer,
any `Sources:` lines, and a `Confidence:` percentage. Type `quit`, `exit`, or `Ctrl+C`
to leave.

### Single question (CLI)

```bash
python3 src/cli.py query "What are your banking hours?" --json
```

Drop `--json` for plain-text output.

### Via the API

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What are your banking hours?"}'
```

See `docs/setup/running-locally.md` and `docs/api/chat-endpoint.md`.

## What makes a good question

The retriever embeds your question and finds chunks with similar meaning. To get good
results:

- **Be specific about the product/topic.** "What is the minimum balance for the standard
  checking account?" beats "tell me about accounts".
- **Ask one thing at a time.** Multi-part questions dilute retrieval.
- **Use banking vocabulary that matches the documents.** If the source says "overdraft
  protection", use that phrase, not a loose paraphrase.
- **Keep it in scope.** General product, policy, fee, loan, and procedure questions work
  best. Account-specific ("how do **I** reset **my** password?") may trigger the scope
  refusal even if a generic password-reset FAQ exists — rephrase as "how does one reset
  a password?".

## How the system processes your question

1. Your question is embedded into a vector (and tokenized for sparse search if BM25 is
   installed).
2. The system retrieves the top chunks from the loaded knowledge base (no internet).
3. It builds a prompt with the system rules + retrieved chunks + your question.
4. The LLM drafts an answer constrained to the provided context.
5. The response is checked for scope phrases; a hedging or out-of-scope answer is
   rewritten to a fixed refusal.
6. You get the answer, citations, and a confidence hint.

If no chunks are retrieved, you get "I couldn't find any relevant information…" —
rephrase or ensure the relevant documents are ingested
(`docs/setup/document-ingestion.md`).

## Tips when answers feel wrong

- **Always refuses:** the response may be hedging with trigger words
  ("I don't know", "personal information"). Rephrase; or the bot needs more documents
  loaded.
- **Confidence is low:** low lexical overlap between the answer and the retrieved
  chunk. Often means the chunk isn't a great match — rephrase to match document wording.
- **Wrong-looking fact:** the system only knows the loaded documents. If the document
  is stale or partial, the answer will be too. Confirm against `Sources:`.

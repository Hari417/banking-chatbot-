# POST /chat

**Version:** 1.0
**Status:** Current
**Last Verified:** 2026-08-20 against `src/api.py` lines 149–185
**Sources:** `src/api.py`, `src/banking_rag/rag_workflow.py`, `component-specification.md` §2.1
**Owner:** Scribe

---

## Method & path

`POST /chat` (also exposed as the alias `POST /query`).

## Purpose

Run the RAG workflow for a single banking-FAQ query and return the generated answer
with citations, confidence, and abstention flag. This is the primary user-facing
endpoint. `/query` is identical to `/chat` — it awaits `chat(request)` and returns the
same response.

## Request schema — `QueryRequest`

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `query` | string | yes | `min_length=1`, `max_length=1000` | The user's natural-language question. |
| `session_id` | string | no | — | If present, the exchange is appended to that session's history in the in-memory store. |
| `context` | `Dict[str,str]` | no | — | Declared on the model; **not consumed** by the handler (no-op in v1). |

Example:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{ "query": "What are your banking hours?", "session_id": "sess-1" }'
```

## Response schema — `QueryResponse` (HTTP 200)

| Field | Type | Description |
|-------|------|-------------|
| `query` | string | Echo of the input query. |
| `response` | string | The generated answer, or the fixed scope-refusal / abstention message. |
| `citations` | `List[string]` | `"[i]: <source> (chunk: <chunk_id>)"` per retrieved document; `[]` if none. |
| `confidence` | float | Heuristic 0.0–1.0 from the grounding validator (token-overlap proxy). |
| `abstained` | bool | `true` if the response was rewritten to a refusal/no-context message. |
| `session_id` | string \| null | Echo of the provided `session_id`. |
| `metadata` | `Dict` \| null | Workflow metadata: retrieval strategy, doc counts, response token count, confidence, `grounded` flag. |

Example (success):

```json
{
  "query": "What are your banking hours?",
  "response": "Our banking hours are Monday through Friday, 9:00 AM to 5:00 PM local time...",
  "citations": ["[0]: faq_hours.txt (chunk: chunk_0)"],
  "confidence": 0.62,
  "abstained": false,
  "session_id": "sess-1",
  "metadata": {
    "retrieval_strategy": "hybrid",
    "num_docs_retrieved": 1,
    "num_docs_used": 1,
    "response_tokens": 24,
    "confidence": 0.62,
    "grounded": true
  }
}
```

Example (abstention — out of scope):

```json
{
  "query": "What is my account balance?",
  "response": "I cannot provide answers about transactions, account balances, or personal account information. I can only answer questions about general banking policies, products, fees, loans, and procedures. Please ask about those topics.",
  "citations": [],
  "confidence": 0.0,
  "abstained": true,
  "session_id": null,
  "metadata": {}
}
```

Example (abstention — no documents retrieved):

```json
{
  "query": "What is the Mars rover battery life?",
  "response": "I couldn't find any relevant information in the knowledge base. Please try rephrasing your question or ask about banking policies, products, fees, loans, or procedures.",
  "citations": [],
  "confidence": 0.0,
  "abstained": true,
  "session_id": null,
  "metadata": {}
}
```

## Error responses

| Status | When | Body |
|--------|------|------|
| 422 | Pydantic validation fails (empty/overlong query, wrong types) | FastAPI validation error envelope. |
| 500 | `workflow.run()` raises | `{"detail": "<exception message>"}` |

The route `try/except` catches the exception and re-raises `HTTPException(500)` with the
raw exception string. (A separate global `@app.exception_handler(500)` would return a
generic `"An internal error occurred..."` message, but the route-level handler raises
first and dominates for this path.) Treat any 500 as a provider/credential or
configuration issue and tail the server logs.

## Security pre-checks applied

**None on the API path.** v1 does not run PII detection, an injection filter, a rate
limiter, or an input length guard beyond the `max_length=1000` on the request model.
Scope control is enforced **inside** `RAGWorkflow` by (a) the system prompt and (b) the
post-hoc `_should_abstain()` trigger scan. See `docs/compliance/scope-enforcement.md`.

## Streaming

**Not implemented.** The `RAGWorkflow` is synchronous and returns a single response.
`LLMClient` supports streaming at the LLM layer, but `/chat` does not expose an SSE /
chunked response. Streaming is a v2 item.

## Audit-log entry produced

**No structured audit trail in v1.** The handler emits stdlib `logger.error` lines on
failure only; there is no per-request `query.received` / `response.sent` event log.
See `docs/compliance/audit-trail.md`.

## Session handling

If `session_id` is provided, the user query and the assistant response (with citations)
are appended to `session_store[session_id]` as `{"role": ..., "content": ...}` entries.
Retrieve history via `GET /sessions/{session_id}`; delete via
`DELETE /sessions/{session_id}`. Sessions are in-memory only — see `sessions-endpoint.md`.

## How the response is produced

`workflow.run(request.query)` executes the 8-step pipeline: embed → retrieve → build
context → build prompt → call LLM → validate grounding → abstention check → generate
citations. See `docs/architecture/overview.md` §Query Flow for the full sequence and
the v1 caveats (grounding heuristic, dead RRF, no query-side security).

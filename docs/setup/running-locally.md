# Running Locally

**Version:** 1.0
**Status:** Current
**Last Verified:** 2026-08-20 against `src/cli.py`, `src/api.py`
**Sources:** `src/cli.py`, `src/api.py`, `config.yaml`
**Owner:** Scribe

---

## Choose a front-end

v1 ships two front-ends:

| Interface | How to start | Best for |
|-----------|--------------|----------|
| CLI | `python3 src/cli.py chat` | Quick local experimentation, scripted queries |
| REST API | `python3 src/api.py` | Programmatic access, integration |

There is **no Streamlit UI** in v1, despite references in the architecture. The CLI is
the interactive human interface.

---

## 1. Prerequisites complete

Confirm you have done the steps in `installation.md`: venv activated, dependencies
installed, `config.yaml` edited for your provider, and either `OPENAI_API_KEY` set or
Ollama running.

## 2. (Optional) Ingest documents

For real answers you need content in the FAISS index. To load the sample data or your
own documents, follow `document-ingestion.md`. If you skip ingestion, the chatbot will
return the "no documents retrieved" abstention message for every query.

## 3. Run the CLI

Interactive REPL:

```bash
python3 src/cli.py chat
```

You will see the banner, then a `You:` prompt. Ask a banking question; the assistant
prints the response, any `Sources:` citations, and a `Confidence:` percentage. Type
`quit` / `exit` / `Ctrl+C` to leave.

Single-shot query (prints JSON to stdout):

```bash
python3 src/cli.py query "What are your banking hours?" --json
```

Pipe a query via stdin (useful for scripts):

```bash
echo "What are your banking hours?" | python3 src/cli.py query --json
```

CLI flags:

| Flag | Effect |
|------|--------|
| `--config <path>` / `-c` | Use a specific config file. |
| `--mock` | Use mock components — no model load, no API key, no index. Useful for smoke tests. |
| `--json` (`query` only) | Output JSON instead of formatted text. |
| `--debug` | Enable DEBUG logging. |
| `--version` | Print `Banking RAG Chatbot v0.1.0` and exit. |

## 4. Run the API

Start the server (requires `fastapi` + `uvicorn` installed):

```bash
python3 src/api.py
# INFO:     Uvicorn running on http://0.0.0.0:8000
```

Override host/port/mock via env vars:

```bash
BANKING_RAG_API_PORT=9000 BANKING_RAG_MOCK=true python3 src/api.py
```

Health check:

```bash
curl http://localhost:8000/health
# {"status":"ready","version":"0.1.0","vector_store_ready":true,"model_available":true}
```

First query:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What are your banking hours?"}'
```

See `docs/api/` for every endpoint, request/response schema, and curl examples.

## 5. Mock mode (no key, no model)

For a zero-dependency smoke test of the wiring, run either front-end with `--mock` /
`BANKING_RAG_MOCK=true`. This uses `MockLLMClient`, `MockEmbeddingModel`, etc., and
returns canned responses. It exercises the full pipeline shape without any network or
model download. This is what `python3 tests/verify.py` does.

## 6. Stopping

- CLI: type `quit` or `Ctrl+C`.
- API: `Ctrl+C` in the terminal running `python3 src/api.py`. In-memory sessions are
  **lost on stop** (no persistence — see `docs/runbook/session-cleanup.md`).

---

## What to expect from a query

A successful chat response includes:

- `response` — the generated answer.
- `citations` — `[i]: <source> (chunk: <chunk_id>)` per retrieved document.
- `confidence` — a heuristic 0.0–1.0 score from the grounding validator (see the
  architecture overview — this is a token-overlap proxy, not a semantic score).
- `abstained` — `true` if the response was rewritten to a fixed scope-refusal or
  no-documents message.

Out-of-scope queries ("What's my account balance?") get a fixed refusal and
`abstained: true`. Unknown-but-in-scope queries with no retrieved context get a
rephrase prompt and `abstained: true`. See `docs/compliance/scope-enforcement.md` and
`docs/user-guide/limitations-and-scope.md`.

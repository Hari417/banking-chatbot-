# Understanding Citations

**Version:** 1.0
**Status:** Current
**Last Verified:** 2026-08-20 against `src/banking_rag/rag_workflow.py::(_generate_citations)`
**Sources:** `src/banking_rag/rag_workflow.py`, `src/banking_rag/vector_store.py`
**Owner:** Scribe

---

## What a citation looks like

Each assistant answer is followed by zero or more `Sources:` lines of the form:

```
[0]: path/to/document.pdf (chunk: chunk_5)
[1]: policies/overdraft.txt (chunk: chunk_8)
```

In JSON output (`--json` or the API), they appear as:

```json
"citations": ["[0]: policies/overdraft.txt (chunk: chunk_5)", "[1]: ..."]
```

## What the parts mean

| Part | Meaning |
|------|---------|
| `[0]` | An index matching the order the chunk was passed to the LLM. The answer may reference `[0]` or `[1]` inline; otherwise the list is just the set of sources used. |
| `path/to/document.pdf` | The `source` metadata field — the file path the document was ingested from. For in-memory ingests it may be `"unknown"` if no `source` metadata was set. |
| `chunk: chunk_5` | The `chunk_id` of the retrieved chunk. You can use it to look the chunk up in `data/index/metadata.json` to read the exact text that backed the answer. |

## How to read a chunk_id back

The chunk text is stored in `./data/index/metadata.json`, keyed by `chunk_id`:

```bash
python3 -c "import json; m=json.load(open('data/index/metadata.json')); \
c=m.get('chunk_5'); print(c['content'] if c else 'not found')"
```

This is the most reliable way to verify what the bot actually grounded on.

## When you get no citations

- `citations: []` with an abstention message means retrieval found no chunks
  (no-documents abstention), or the response was rewritten to the scope refusal.
- A non-empty answer with empty citations is unexpected in v1; if you see it, it's a
  sign retrieval silently failed — see `docs/setup/troubleshooting.md`.

## Limitations of v1 citations

- The citation shows the **source filename and chunk id only** — there is no page
  number, no highlighted excerpt in the UI, no collapsible source panel (those are v2
  UI features; the v1 UI is CLI/API text only).
- The `[i]` marker is **not validated** to appear in the answer itself. The LLM is
  *instructed* to cite, but v1 does not programmatically enforce inline citations or
  check that every claim is backed by a listed source. Treat the source list as "what
  was retrieved," not as a guaranteed proof of every sentence.
- `metadata.grounded` in the API response is a lexical-overlap score, not a citation
  validation. See `docs/evaluation/known-limitations.md` C4.

## Verifying an answer

For any claim that matters:

1. Note the `chunk_id` from the citation.
2. Read the chunk from `metadata.json` (above).
3. Confirm the claim is supported by the chunk text.

If the chunk doesn't support the answer, it's a hallucination — report via an incident
record (`docs/runbook/incident-response.md` §1) and consider lowering `temperature`
or switching models (`docs/runbook/llm-provider-swap.md`).

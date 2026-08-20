# Evaluation Test Datasets

**Version:** 1.0
**Status:** Planned — **not implemented in v1**
**Last Verified:** 2026-08-20 against `src/` (no eval dataset present)
**Sources:** `component-specification.md` §9, `docs/evaluation/metrics.md`
**Owner:** Scribe

---

## Status: not implemented

No JSONL evaluation dataset exists in v1. The format below is the intended v2 schema,
recorded here so it is not lost. See `docs/evaluation/metrics.md` and
`docs/evaluation/known-limitations.md` §E.

## Intended format

Newline-delimited JSON, one record per question:

```json
{"question": "What is the minimum balance for the standard checking account?",
 "expected_chunks": ["chunk_42", "chunk_43"],
 "acceptable_answers": ["$500", "five hundred dollars"]}
```

| Field | Type | Meaning |
|-------|------|---------|
| `question` | string | Natural-language query. |
| `expected_chunks` | `List[chunk_id]` | Chunks that *should* be retrieved. |
| `acceptable_answers` | `List[string]` | Substrings/markers that indicate a correct answer (for Answer F1 / hallucination checks). |

## Intended categories (from `component-specification.md` §9)

1. **Retrieval accuracy** — are the expected chunks surfaced?
2. **Answer relevance** — does the answer address the question?
3. **Hallucination detection** — does the answer stray beyond the chunks?
4. **Abstention correctness** — does the system correctly say "I don't know" / refuse
   scope when it should?

## How to extend (intended, v2)

Append records to `docs/evaluation/eval_dataset.jsonl` (file does not exist in v1).
Document the source/citation for each record so the dataset is auditable. The runner
(v2) would group results by category.

# Evaluation Metrics

**Version:** 1.0
**Status:** Planned — **not implemented in v1**
**Last Verified:** 2026-08-20 against `src/` (no evaluation harness present)
**Sources:** `component-specification.md` §9, `risk-analysis.md` R014/R015
**Owner:** Scribe

---

## Status: not implemented

The outline (`docs/DOCUMENTATION_OUTLINE.md` §8) plans an evaluation suite with the
metrics below. **No evaluation harness, eval dataset, or metrics script exists in the v1
codebase.** This file records the intended metrics for v2; do not assume any of it runs
today. See `docs/evaluation/known-limitations.md` §E (Accepted v1 scope).

## Intended metrics (from `component-specification.md` §9.2)

| Metric | v2 target | How (intended) |
|--------|-----------|-----------------|
| Recall@K | > 0.8 @ K=5 | Fraction of relevant chunks retrieved in the top-K. |
| MRR | > 0.7 | Mean reciprocal rank of the first relevant chunk. |
| Answer F1 | > 0.6 | Token-level F1 between generated answer and reference. |
| Hallucination Rate | < 0.05 | Fraction of answers not supported by retrieved context. |
| Abstention Accuracy | > 0.9 | Correctness of "I don't know" vs. "answer" decisions. |

## How to run (intended, in v2)

A JSONL evaluation dataset (see `test-datasets.md`) is loaded, each run queried through
the RAG workflow, and the metrics computed against expected chunks/answers. The runner
would output a JSON summary and append to a results log. The dataset format and runner
do not exist in v1.

## Why it is not in v1

v1 prioritized a working RAG pipeline, CLI/API, and ingestion. Evaluation harnesses
require gold-labeled datasets that did not exist for this prototype. The accepted-risk
register (R014, R015) covers the v1 absence of these metrics. v2 will ship the suite.

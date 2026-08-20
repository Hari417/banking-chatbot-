# Getting Started

**Version:** 1.0
**Status:** Current
**Last Verified:** 2026-08-20 against `src/cli.py`, `src/api.py`
**Sources:** `docs/setup/installation.md`, `docs/setup/running-locally.md`
**Owner:** Scribe

---

## The fast path (mock mode, no key, no model)

1. Follow `docs/setup/installation.md` steps 1–3 (venv + core deps).
2. Run the smoke test: `python3 tests/verify.py` — expect "ALL TESTS PASSED!".
3. Chat in mock mode (returns canned answers, exercises the full pipeline shape):
   `python3 src/cli.py chat --mock`

## The real path (with a provider)

1. Complete `docs/setup/installation.md` through step 6.
2. Configure a provider in `config.yaml` (`docs/setup/configuration.md`).
3. (Recommended) Ingest documents — see `docs/setup/document-ingestion.md`. Without
   ingestion, every query abstains with "no documents found".
4. Run it — see `docs/setup/running-locally.md` for the CLI and API commands.

## What you actually have in v1

- **Two interfaces:** the CLI (`src/cli.py chat` / `query`) and the REST API
  (`src/api.py`). There is **no Streamlit UI** in v1 (see `docs/evaluation/known-limitations.md` A1).
- The first answer depends entirely on what is in the FAISS index. Use the sample data
  in `sample_data.py` or your own documents via the Python ingestion pipeline.

Next: `docs/user-guide/asking-questions.md`, `docs/user-guide/understanding-citations.md`,
`docs/user-guide/limitations-and-scope.md`.

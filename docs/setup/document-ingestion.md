# Document Ingestion

**Version:** 1.0
**Status:** Current
**Last Verified:** 2026-08-20 against `src/banking_rag/ingestion.py`, `sample_data.py`
**Sources:** `src/banking_rag/ingestion.py`, `INGESTION_SPEC.md`, `config.yaml`
**Owner:** Scribe

---

## Two ingestion paths — and the difference matters

v1 has **two** ways to ingest, and they are not equivalent:

| Path | How | Status |
|------|-----|--------|
| **Python pipeline** (`DocumentIngestionPipeline`) | instantiate the class and call `ingest_file()` / `ingest_directory()` | **Real** — runs the full 8-stage pipeline. |
| **REST `/ingest` endpoint** | `POST /ingest` on the API | **Stub** — returns a fixed placeholder; does not ingest. |

> **Important:** The `/ingest` endpoint does **not** call the pipeline. It always
> returns `document_id: "doc_001", chunks_ingested: 1, embeddings_generated: 1`
> (or `mock_doc_001` in mock mode), regardless of the payload. This is a v1 limitation
> — see `docs/api/ingest-endpoint.md`. To actually load content, use the Python
> pipeline below.

---

## Supported formats

`DocumentLoader` supports:

| Extension | Loader | Optional dependency |
|-----------|--------|--------------------|
| `.txt` | plain read | none |
| `.md` | plain read (treated as text) | none |
| `.pdf` | `PyPDF2.PdfReader` page extraction | `PyPDF2` |
| `.html` | `BeautifulSoup` text extraction | `beautifulsoup4` |
| `.docx` | falls back to the text loader | none (limited — extracts raw bytes-as-text) |

PDF and HTML loaders raise `ImportError` if their optional library is not installed.

## Where data goes

The pipeline persists, by default under `./data/`:

| Path | Contents |
|------|----------|
| `data/index/faiss.index` | The FAISS vector index. |
| `data/index/metadata.json` | `chunk_id → {content, chunk_id, ...metadata}` map. |
| `data/index/document_registry.json` | `document_id → {chunk_ids, source, format, ...}` map. |
| `data/quarantine/` | Chunks rejected for PII (one JSON per rejected chunk). |

Paths are configurable via `vector_store.persist_path`, `metadata_path`, `registry_path`,
and `data_dir` (for quarantine).

---

## The 8-stage pipeline

`DocumentIngestionPipeline.ingest_file(path)` runs:

1. **Format detection** — extension → format string.
2. **Content extraction** — `DocumentLoader` → a `Document`.
3. **Chunking** — `DocumentChunker.chunk()` using `chunking.strategy`.
4. **PII validation** — `PIIDetector.detect()` per chunk. Reject-list PII
   (`ssn`, `account_number`, `credit_card`) → quarantined, excluded from index.
5. **Metadata enrichment** — adds `token_count`, `embedding_model`, `ingested_at`,
   `format`.
6. **Embedding generation** — batch embed via `EmbeddingModel.generate_batch()`.
7. **Persistence** — `VectorStore.add_chunks()` writes index + metadata + registry.
8. **Validation** — confirms chunk count and presence in the store.

See `docs/architecture/overview.md` §Ingestion Flow for the divergence notes (e.g.,
non-reject PII redaction is declared but not auto-applied in stage 4).

---

## How to ingest

### A. Single file

Create a small script `ingest.py` in the project root:

```python
import sys
sys.path.insert(0, "src")
from banking_rag.config import load_config
from banking_rag.vector_store import VectorStore
from banking_rag.ingestion import create_ingestion_pipeline

config = load_config("config.yaml")
vs = VectorStore(config)
pipeline = create_ingestion_pipeline(vs, config)

result = pipeline.ingest_file("path/to/document.pdf")
print(f"chunks={result.chunks} embeddings={result.embeddings} failed={result.failed}")
if result.errors:
    print("errors:", result.errors)
```

Run it with the venv active:

```bash
python3 ingest.py
```

Requirements: the format's optional loader installed (`PyPDF2` / `beautifulsoup4`), and
the embedding model available (local model download or a working API key).

### B. Whole directory

```python
result = pipeline.ingest_directory("path/to/docs")
print(f"chunks={result.chunks} embeddings={result.embeddings} failed={result.failed}")
```

`ingest_directory` recursively walks files with extensions
`{.txt, .md, .pdf, .html}`.

### C. Loading the sample FAQ data

`sample_data.py` ships FAQ, policy, product, and loan entries as Python lists. To load
them into the index, render them to text and ingest, e.g.:

```python
import sys
sys.path.insert(0, "src")
import sample_data
from banking_rag.config import load_config
from banking_rag.vector_store import VectorStore
from banking_rag.chunking import DocumentChunker
from banking_rag.embeddings import get_embedding_model
from banking_rag.ingestion import DocumentIngestionPipeline, Document

config = load_config()
vs = VectorStore(config)
pipeline = DocumentIngestionPipeline(vs, config)

# Convert each FAQ to a Q/A text chunk and ingest via the faq_preserved strategy.
texts = [f"Q: {f['question']}\n\nA: {f['answer']}" for f in sample_data.FAQS]
# ...build Document objects and call pipeline.stage_3..7, or write to .txt files
# and use ingest_file(). The simplest path is to write each FAQ to a .txt file
# under a directory and call ingest_directory().
```

For a quick start, write the samples to `.txt` files and point `ingest_directory` at
them — the recursive chunker handles paragraph-style text well.

---

## Metadata captured per chunk

After ingestion, each chunk's metadata contains (at least):

| Key | Source | Example |
|-----|--------|---------|
| `chunk_id` | `VectorStore.add_chunks` | `chunk_12` |
| `chunk_index` | `DocumentChunker` | `0`, `1`, … |
| `total_chunks` | `ChunkingResult` | `18` |
| `chunk_strategy` | pipeline | `recursive` |
| `source` | `DocumentLoader` | `path/to/file.pdf` |
| `filename` | `DocumentLoader` | `fees.pdf` |
| `format` | stage 1 | `pdf` |
| `token_count` | stage 5 | `98` |
| `embedding_model` | stage 5 | `all-MiniLM-L6-v2` |
| `ingested_at` | stage 5 | *(currently set to the embedding model name — see limitation below)* |

> **Limitation:** stage 5 sets `ingested_at = str(self.config.embedding.model)` — a
> copy-paste bug; it stores the model name, not a timestamp. Flagged in
> `docs/evaluation/known-limitations.md`.

## PII handling during ingestion

`PIIDetector` patterns detect: `ssn`, `credit_card`, `email`, `phone`,
`account_number` (see `docs/compliance/pii-handling.md` for the exact regexes).

- **Reject** (`ssn`, `account_number`, `credit_card`): the chunk is written to
  `data/quarantine/quarantined_<chunk_id>.json` and excluded from the index.
- **Accept** (`email`, `phone`): the chunk passes through. A `redact()` method exists
  but is **not automatically invoked** by stage 4 in v1 — emails/phones in documents
  will reach the index as-is. If you need redaction, call `PIIDetector.redact()` on the
  content before adding chunks, or pre-process your source documents.

## Re-ingesting / updating

FAISS `IndexFlatIP` is append-only in this implementation; `delete_chunk()` only removes
the chunk from the metadata map — it does **not** remove the vector from the FAISS index
(the comment in `vector_store.py` acknowledges this). To fully remove a document or
change chunking/embedding, rebuild the index from scratch:

```python
vs.clear()   # creates a fresh index and clears metadata + registry
# then re-ingest
```

See `docs/runbook/reindexing.md` and `docs/runbook/embedding-model-change.md`.

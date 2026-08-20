# POST /ingest

**Version:** 1.0
**Status:** Current
**Last Verified:** 2026-08-20 against `src/api.py` lines 224–249
**Sources:** `src/api.py`, `src/banking_rag/ingestion.py`, `INGESTION_SPEC.md`
**Owner:** Scribe

---

## Method & path

`POST /ingest`

## Purpose

Declared purpose: ingest a new document into the knowledge base.
**Actual v1 behavior: this endpoint is a stub.** It does not call the
`DocumentIngestionPipeline`. It returns a fixed placeholder response regardless of the
request payload.

## Request schema — `IngestRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `content` | string | yes | Would-be document content. **Ignored** in v1. |
| `source` | string | yes | Would-be source label. **Ignored** in v1. |
| `metadata` | `Dict` | no | Would-be metadata. **Ignored** in v1. |
| `chunk_strategy` | string | no | Would-be chunking strategy. **Ignored** in v1. |

```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{ "content": "Our routing number is 021000021.", "source": "routing.txt" }'
```

## Response schema — `IngestResponse` (HTTP 200)

| Field | Type | Value returned in v1 |
|-------|------|------------------------|
| `document_id` | string | `"doc_001"` (mock mode: `"mock_doc_001"`) |
| `chunks_ingested` | int | `1` |
| `embeddings_generated` | int | `1` |

Example:

```json
{ "document_id": "doc_001", "chunks_ingested": 1, "embeddings_generated": 1 }
```

These values are constants and do **not** reflect any real ingestion.

## Error responses

| Status | When |
|--------|------|
| 422 | Pydantic validation fails (missing `content`/`source`). |
| 500 | Unhandled exception in the handler. |

## How to actually ingest documents

The REST endpoint does not ingest. To load content into the FAISS index, use the
Python `DocumentIngestionPipeline` directly. See `docs/setup/document-ingestion.md`
for the full procedure (`ingest_file()` / `ingest_directory()`).

## Why the stub exists

The ingestion pipeline is fully implemented as a Python class
(`src/banking_rag/ingestion.py`); only the API wiring to it is missing in v1. A
follow-up task should replace the placeholder `return IngestResponse(...)` with:

```python
pipeline = DocumentIngestionPipeline(config)
document = Document(content=request.content, metadata=request.metadata or {}, source=request.source)
chunks = pipeline.stage_3_chunking(document)
chunks = pipeline.stage_4_pii_validation(chunks)
chunks = pipeline.stage_5_metadata_enrichment(chunks)
embeddings = pipeline.stage_6_embedding_generation(chunks)
chunk_ids = pipeline.stage_7_persistence(chunks, embeddings, doc_id)
pipeline.stage_8_validation(chunks, chunk_ids)
```

Until that wiring lands, treat `/ingest` as non-functional and use the Python path.
This divergence is logged in `docs/evaluation/known-limitations.md` and against the
Scribe task as a follow-up.

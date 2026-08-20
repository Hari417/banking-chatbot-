# Configuration

**Version:** 1.0
**Status:** Current
**Last Verified:** 2026-08-20 against `config.yaml` and `src/banking_rag/config.py`
**Sources:** `config.yaml`, `src/banking_rag/config.py`, `component-specification.md`
**Owner:** Scribe

---

## Configuration model

Configuration lives in `config.yaml` (project root) and is loaded by
`banking_rag.config.load_config()`. Each top-level section maps to a Pydantic
`BaseModel` sub-config, aggregated into the `AppConfig` dataclass:

```
AppConfig
├── system             (debug, log_level, data_dir, cache_dir)
├── llm      → LLMConfig
├── embedding→ EmbeddingConfig
├── vector_store → VectorStoreConfig
├── retrieval→ RetrievalConfig
├── security → SecurityConfig
├── chunking → ChunkingConfig
├── session  → SessionConfig
└── features → FeatureConfig
```

A process-global singleton is exposed via `get_config()`; `reload_config()` re-reads the
file (used by the API's `/config` reload semantics, though note `/config` is read-only —
see `docs/api/config-endpoint.md`). If `config.yaml` is missing, `load_config()`
returns an `AppConfig()` built entirely from the Pydantic defaults.

## Fallback / override chain

`llm.api_key_env` and `embedding.api_key_env` name an **environment variable** that holds
the secret; the secret itself is read via `os.environ.get()` at call time. The chain is:

1. `config.yaml` provides base values.
2. Environment variables provide secrets (named by config) and deployment overrides
   (see [Deployment env vars](#deployment-env-vars)).
3. Pydantic field defaults apply for anything unset.

There is no `.env` file loader in the codebase; set env vars in your shell, systemd unit,
or container.

---

## Reference: every field

### `system`

| Field | Default | Description |
|-------|---------|-------------|
| `debug` | `false` | Enables verbose logging in the CLI. |
| `log_level` | `"INFO"` | Stdlib logging level. **Note:** despite the Style Guide, v1 uses stdlib text logging, not structured JSON. |
| `data_dir` | `"./data"` | Root for the FAISS index, metadata, registry, and quarantine. |
| `cache_dir` | `"./cache"` | Reserved; not currently read by the code. |

### `llm`

| Field | Default | Description |
|-------|---------|-------------|
| `provider` | `"openai"` | One of `openai`, `openai_compatible`, `ollama`. |
| `model` | `"gpt-4o-mini"` | Model id sent to the API. For Ollama, e.g. `llama3`. |
| `api_base` | `"https://api.openai.com/v1"` | Base URL for `openai` / `openai_compatible`. |
| `api_key_env` | `"OPENAI_API_KEY"` | Name of the env var holding the API key. |
| `ollama_base_url` | `"http://localhost:11434"` | Ollama daemon URL (used only when `provider: ollama`). |
| `ollama_model` | `"llama3"` | Ollama model id (used only when `provider: ollama`; note `llm.model` is also sent — see [Ollama notes](#ollama-notes)). |
| `temperature` | `0.7` | Sampling temperature. |
| `max_tokens` | `1000` | Max generated tokens. |
| `timeout` | `30` | HTTP request timeout, seconds. |

#### Ollama notes
When `provider: ollama`, `LLMClient` POSTs to `<ollama_base_url>/chat/completions`
and sends `model: <llm.model>` in the payload. The separate `ollama_model` field exists
on the config but is **not used by `LLMClient`** — set `llm.model` to the Ollama model
id you pulled.

### `embedding`

| Field | Default | Description |
|-------|---------|-------------|
| `model` | `"all-MiniLM-L6-v2"` | Local sentence-transformers model name, or an API embedding model id. |
| `dimensions` | `384` | Vector dimension. Must match the model (384 for `all-MiniLM-L6-v2`). |
| `provider` | `"local"` | One of `local`, `openai`, `openai_compatible`. |
| `api_base` | `"https://api.openai.com/v1/embeddings"` | Embeddings API base (API providers). |
| `api_key_env` | `"OPENAI_API_KEY"` | Env var name for the API key. |
| `batch_size` | `32` | Local batch size for `generate_batch()`. |
| `timeout` | `60` | API timeout, seconds. |

> The embedding **dimensions must agree** with the FAISS index dimension. The index is
> created with `config.embedding.dimensions`. Changing the embedding model without
> re-indexing causes dimension-mismatch errors — see `docs/runbook/embedding-model-change.md`.

### `vector_store`

| Field | Default | Description |
|-------|---------|-------------|
| `index_type` | `"IndexFlatIP"` | `IndexFlatIP` (brute-force inner product) or `IndexIVFFlat`. |
| `nlist` | `100` | IVF cell count (only for `IndexIVFFlat`). |
| `persist_path` | `"./data/index/faiss.index"` | FAISS index file. |
| `metadata_path` | `"./data/index/metadata.json"` | chunk_id → metadata map. |
| `registry_path` | `"./data/index/document_registry.json"` | document_id → chunk_ids map. |

### `retrieval`

| Field | Default | Description |
|-------|---------|-------------|
| `dense_k` | `10` | Number of dense (FAISS) candidates. |
| `sparse_k` | `10` | Number of sparse (BM25) candidates. |
| `final_k` | `5` | Results returned after fusion/truncation. |
| `score_threshold` | `0.5` | Declared but **not enforced** on the query path in v1. |
| `rerank_enabled` | `true` | Declared; no reranker is wired in v1. |
| `rerank_model` | `"cross-encoder/ms-marco-MiniLM-L-6-v2"` | Declared reranker; not installed or invoked in v1. |

> **Note:** `score_threshold`, `rerank_enabled`, and `rerank_model` are present in
> config but the `HybridRetriever` does not apply a score threshold or invoke a
> reranker. They are placeholders for v2. Retrieval simply fuses dense+sparse and
> truncates to `final_k`.

### `security`

| Field | Default | Description |
|-------|---------|-------------|
| `rate_limit_enabled` | `true` | **Declared, not implemented.** No rate limiter runs on the query path. |
| `rate_limit_requests` | `10` | Requests per window. Not enforced in v1. |
| `rate_limit_window` | `60` | Window seconds. Not enforced in v1. |
| `pii_detection_enabled` | `true` | Applied at **ingestion** only (document chunks). Not applied to user queries. |
| `input_guard_enabled` | `true` | **Declared, not implemented.** No query-side input guard runs. |
| `prompt_injection_check_enabled` | `true` | **Declared, not implemented.** No injection filter runs. |

> These flags reflect the planned security layer. Their partial/absent enforcement is
> documented in `docs/compliance/scope-enforcement.md` and `docs/evaluation/known-limitations.md`.

### `chunking`

| Field | Default | Description |
|-------|---------|-------------|
| `chunk_size` | `512` | Target chunk size (characters for the recursive strategy). |
| `chunk_overlap` | `50` | Approximate overlap between long-paragraph splits. |
| `strategy` | `"recursive"` | One of `recursive`, `faq_preserved`, `table_aware`. |

### `session`

| Field | Default | Description |
|-------|---------|-------------|
| `memory_limit` | `100` | Declared max sessions; **not enforced** — the API uses an unbounded dict. |
| `ttl_minutes` | `30` | Declared TTL; **no TTL sweeper runs** in v1 (sessions persist until the process dies or are deleted via the API). |
| `persistence` | `false` | If `true`, SQLite persistence was planned; **not implemented** in v1. |

### `features`

| Field | Default | Description |
|-------|---------|-------------|
| `enable_transactions` | `false` | **Hardcoded false must remain false.** No code reads it — it is a documentation-only guard; the real scope enforcement is the system prompt + abstention trigger scan. |
| `enable_premium_reranker` | `false` | v2 placeholder. |

### `presentation`

| Field | Default | Description |
|-------|---------|-------------|
| `streamlit_port` | `8501` | Declared; **no Streamlit UI exists in v1.** |
| `api_host` | `"0.0.0.0"` | Used by the API's deployment config (overridable via `BANKING_RAG_API_HOST`). |
| `api_port` | `8000` | API port (overridable via `BANKING_RAG_API_PORT`). |
| `enable_api` | `true` | Declared; the API is the only web front-end in v1. |
| `enable_streamlit` | `true` | Declared; **ignored** — no Streamlit UI exists. |

---

## Deployment env vars

These environment variables are read by the API/CLI at runtime:

| Variable | Read by | Purpose |
|----------|---------|---------|
| `OPENAI_API_KEY` (or whatever `*.api_key_env` names) | `LLMClient`, `EmbeddingModel` | Secret for OpenAI / OpenAI-compatible calls. |
| `BANKING_RAG_CONFIG` | `src/api.py` | Path to the config file (default `config.yaml`). |
| `BANKING_RAG_MOCK` | `src/api.py` | `true` makes the API use `Mock*` components (no model, no key). |
| `BANKING_RAG_API_HOST` | `src/api.py` | API bind host (default `0.0.0.0`). |
| `BANKING_RAG_API_PORT` | `src/api.py` | API port (default `8000`). |
| `BANKING_RAG_DEBUG` | `src/api.py` | `true` enables uvicorn reload. |
| `OLLAMA_HOST` | Ollama tooling (not the app) | Conventional env var for the Ollama daemon. Set `llm.ollama_base_url` in config to match. |

## Example: switch from OpenAI to local Ollama

```yaml
llm:
  provider: "ollama"
  model: "llama3"        # LLMClient sends this as 'model' to Ollama
  temperature: 0.4
  max_tokens: 1000
  timeout: 60            # local LLMs are slower; raise the timeout
  ollama_base_url: "http://localhost:11434"
```

No code change is required; `LLMClient` routes to Ollama's OpenAI-compatible
`/chat/completions` endpoint. See `docs/runbook/llm-provider-swap.md` for the full
procedure and rollback.

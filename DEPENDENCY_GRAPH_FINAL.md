# Banking RAG Chatbot - Dependency Graph (Final v1.0)

**Version:** 1.0  
**Status:** Final  
**Last Updated:** 2026-08-20  
**Incorporates Research:** Embedding models (t_698a9758), Chunking strategy (t_42f3d6b3)

---

## High-Level Module Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PRESENTATION LAYER                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐          │
│  │   Streamlit UI   │  │    FastAPI       │  │      CLI         │          │
│  │   (Port 8501)    │  │    (Port 8000)   │  │   (Future)       │          │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘          │
│           │                     │                     │                    │
│           └─────────────────────┼─────────────────────┘                    │
│                                 │                                          │
│                                 ▼                                          │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │                    SECURITY MIDDLEWARE                            │    │
│  │  ┌─────────────┐ ┌─────────────┐ ┌───────────────────────┐      │    │
│  │  │Rate Limiter │ │  PII Guard  │ │Injection Detection    │      │    │
│  │  └─────────────┘ └─────────────┘ └───────────────────────┘      │    │
│  └──────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ORCHESTRATION LAYER                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │                    LANGGRAPH WORKFLOW                             │    │
│  │                                                                  │    │
│  │   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌─────────┐  │    │
│  │   │  Route   │───►│ Retrieve │───►│ Rerank   │───►│ Generate│  │    │
│  │   │  Query   │    │  Chunks  │    │ (Optional)    │ Response│  │    │
│  │   └──────────┘    └──────────┘    └──────────┘    └─────────┘  │    │
│  │        │               │                │                              │    │
│  │        ▼               ▼                ▼                              │    │
│  │   ┌────────────────────────────────────────────────────────┐     │    │
│  │   │                   RETRIEVAL MODULE                      │     │    │
│  │   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │     │    │
│  │   │  │   FAISS     │  │   BM25      │  │  RRF Fusion     │ │     │    │
│  │   │  │  (Dense)    │  │  (Sparse)   │  │  (Hybrid)       │ │     │    │
│  │   │  └─────────────┘  └─────────────┘  └─────────────────┘ │     │    │
│  │   └────────────────────────────────────────────────────────┘     │    │
│  │                                                                  │    │
│  └──────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        DATA & STORAGE LAYERS                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐       │
│  │  DOCUMENT STORE  │  │   FAISS INDEX    │  │ SESSION STORAGE  │       │
│  │  (Filesystem)    │  │   (Local)        │  │  (In-Memory)     │       │
│  │                  │  │                  │  │                  │       │
│  │  ┌────────────┐  │  │  ┌────────────┐  │  │  ┌────────────┐  │       │
│  │  │   PDF      │  │  │  │  IndexFlat │  │  │  │  Dict      │  │       │
│  │  │   DOCX     │  │  │  │    IP      │  │  │  │  (v1)      │  │       │
│  │  │   HTML     │  │  │  │  (384-dim) │  │  │  │            │  │       │
│  │  └────────────┘  │  │  └────────────┘  │  │  └────────────┘  │       │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘       │
│                                                                              │
│  ┌──────────────────┐  ┌──────────────────┐                              │
│  │ INGESTION PIPELINE │  │    LLM ACCESS    │                              │
│  │                  │  │                  │                              │
│  │  ┌────────────┐  │  │  ┌────────────┐  │                              │
│  │  │  Loaders   │  │  │  │   OpenAI   │  │                              │
│  │  │  Chunkers  │  │  │  │Compatible  │  │                              │
│  │  │  PII       │  │  │  └────────────┘  │                              │
│  │  └────────────┘  │  │  ┌────────────┐  │                              │
│  │                  │  │  │   Ollama   │  │                              │
│  │  ┌────────────┐  │  │  │  (Local)   │  │                              │
│  │  │ Embedding  │  │  │  └────────────┘  │                              │
│  │  │Generator   │  │  │                  │                              │
│  │  │(bge-small) │  │  └──────────────────┘                              │
│  │  └────────────┘  │                                                    │
│  └──────────────────┘                                                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Module Dependencies Matrix

### Sprint Dependencies

| Module | Depends On | Priority | Sprint |
|--------|-----------|----------|--------|
| **Configuration** | - | P0 | Sprint 0 |
| **LLM Interface** | Configuration | P0 | Sprint 0 |
| **FAISS Index** | Configuration | P0 | Sprint 0 |
| **Document Loaders** | Configuration | P1 | Sprint 0 |
| **Chunking** | Configuration, Document Loaders | P0 | Sprint 1 |
| **Embedding Generator** | Configuration | P0 | Sprint 1 |
| **BM25 Index** | Configuration, Chunking | P2 | Sprint 1 |
| **Ingestion Pipeline** | All above | P0 | Sprint 1 |
| **Retrieval** | FAISS Index, BM25 Index | P0 | Sprint 2 |
| **Reranker** | Retrieval | P2 | Sprint 2 |
| **LangGraph Workflow** | Retrieval, LLM Interface | P0 | Sprint 2 |
| **Grounded Generation** | LangGraph Workflow | P0 | Sprint 2 |
| **Session Management** | Configuration | P1 | Sprint 3 |
| **UI Layer** | LangGraph Workflow, Session | P0 | Sprint 3 |
| **Security Layer** | - | P1 | Sprint 3 |
| **Monitoring** | - | P3 | Sprint 4 |

---

## Detailed Module Interactions

### 1. Configuration Module

```
Configuration (config.yaml, .env)
    │
    ├──► All other modules (isomorphic dependency)
    │
    ├──► Schema: Pydantic models
    │
    └──► Environment: local | dev | prod
```

**Exported Configuration:**
- `app`: name, version, environment
- `llm`: provider, model, temperature, max_tokens
- `embeddings`: model (BAAI/bge-small-en), device, batch_size
- `faiss`: index_type, persistence_path, dimensions (384)
- `chunking`: strategy (section-level), size (512), overlap (50)
- `retrieval`: k_dense (10), k_sparse (10), k_final (5), rrf_k (60)
- `session`: ttl_minutes, max_history
- `ui`: port, show_sources

---

### 2. Ingestion Pipeline

```
Document File
    │
    ├──► [Document Loader] (PDF, DOCX, HTML, TXT)
    │       └──► Raw text with metadata
    │
    ├──► [Format Detection]
    │       └──► doc_type, extracted text, sections
    │
    ├──► [PII Validation] (Presidio + patterns)
    │       ├──► Pass: Continue
    │       └──► Fail: Reject/Quarantine
    │
    ├──► [Chunking] (Section-level semantic)
    │       └──► List[Chunk] with metadata
    │
    ├──► [Metadata Enrichment]
    │       └──► banking_category, document_type, section_path
    │
    ├──► [Embedding Generator] (bge-small-en)
    │       └──► 384-dim normalized vectors
    │
    ├──► [BM25 Index Update]
    │       └──► Inverted index terms
    │
    ├──► [FAISS Index Update]
    │       └──► Add vectors with IDs
    │
    └──► [Persistence]
            ├──► Save index
            ├──► Save metadata
            └──► Log ingestion
```

**Key Files:**
- `ingestion/pipeline.py` - Orchestrator
- `ingestion/loaders/` - Document loaders
- `ingestion/chunkers.py` - Semantic chunking implementation
- `ingestion/pii_detector.py` - PII validation
- `ingestion/metadata.py` - Banking-specific metadata

---

### 3. Retrieval Module

```
Query String
    │
    ├──► [Query Pre-processor]
    │       └──► Normalize, expand synonyms
    │
    ├──────────────────────────────────────────────────────┐
    │                                                      │
    ▼                                                      ▼
┌───────────────┐                                    ┌───────────────┐
│    FAISS      │                                    │     BM25      │
│    Search     │                                    │    Search     │
│               │                                    │               │
│ 1. Embed query                                    │ 1. Tokenize    │
│    (bge-small)                                    │    query       │
│               │                                    │               │
│ 2. Index.search                                   │ 2. Score docs │
│    top_k=10                                       │    top_k=10   │
│               │                                    │               │
│ 3. Get metadata                                   │ 3. Return     │
│               │                                    │    results    │
└───────┬───────┘                                    └───────┬───────┘
        │                                                    │
        └────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  RRF Fusion     │
                    │  (k=60)         │
                    │                 │
                    │ Score = Σ(1/(k+r))│
                    │  r = ranking    │
                    │  in each list   │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Top-k Results   │
                    │ (default: 5)    │
                    └─────────────────┘
```

**Key Files:**
- `retrieval/dense.py` - FAISS retriever
- `retrieval/sparse.py` - BM25 retriever
- `retrieval/fusion.py` - RRF fusion
- `retrieval/reranker.py` - Cross-encoder reranking (optional)

---

### 4. LangGraph Workflow

```
State: RAGState
    │
    └──► [Query Router]
            │
            ├──► Greeting ────────► [Greeting Handler]
            │
            ├──► Irrelevant ──────► [Abstention Handler]
            │
            └──► FAQ Query ───────► [Retrieval Node]
                                        │
                                        ▼
                                    [Hybrid Retrieve]
                                        │
                                        ▼
                                    [Rerank Node] (optional)
                                        │
                                        ▼
                                    [Context Assembly]
                                        │
                                        ├──► Chunks
                                        └──► Chat History
                                                │
                                                ▼
                                    [Grounded Generation]
                                        │
                                        ├──► LLM Client
                                        └──► Prompt Assembly
                                                │
                                                ▼
                                    [Response Validation]
                                        │
                                        ├──► Confidence Check
                                        │   ├──► Low: Abstain
                                        │   └──► OK: Continue
                                        │
                                        ├──► Hallucination Check
                                        │   └──► Warn if needed
                                        │
                                        │
                                        ▼
                                    [Citation Generation]
                                        │
                                        └──► Format [1], [2]
                                                │
                                                ▼
                                    [Session Update]
                                        │
                                        └──► Save to SessionStore
```

**Key Files:**
- `workflow/graph.py` - LangGraph definition
- `workflow/state.py` - RAGState TypedDict
- `workflow/nodes.py` - Node implementations
- `workflow/prompts.py` - Prompt templates

---

### 5. LLM Interface

```
[Unified Interface]
    │
    ├──► OpenAI Provider
    │       └──► GPT-4o-mini (default), GPT-4o
    │
    ├──► Ollama Provider
    │       └──► Local models (llama3, mistral)
    │
    └──► Generic OpenAI-Compatible
            └──► Other endpoints

Methods:
    - generate(prompt, temperature, max_tokens)
    - chat(messages, temperature)
    - stream(prompt, callback)
```

**Configuration:**
```yaml
llm:
  provider: "openai"      # openai | ollama | compatible
  model: "gpt-4o-mini"
  temperature: 0.1
  max_tokens: 500
  max_retries: 3
```

---

### 6. Session Management

```
Session ID (UUID)
    │
    ├──► [Session Store] (In-Memory Dict v1)
    │       │
    │       ├──► Messages: List[ChatMessage]
    │       ├──► Metadata: created_at, last_active
    │       └──► Context: retrieved_docs, user_prefs
    │
    ├──► TTL: 30 minutes idle
    │       └──► Auto-cleanup
    │
    └──► Operations:
            - create_session() -> UUID
            - add_message(session_id, message)
            - get_history(session_id) -> List[Message]
            - reset_session(session_id)
```

**Key Files:**
- `sessions/store.py` - InMemorySessionStore
- `sessions/manager.py` - SessionManager

---

### 7. UI Layer

```
User Input
    │
    ├──► [Streamlit Interface]
    │       │
    │       ├──► Chat Display
    │       │       └──► Messages with history
    │       │
    │       ├──► Input Box
    │       │       └──► Submit to API
    │       │
    │       ├──► Citation Panel
    │       │       └──► Expandable sources
    │       │
    │       ├──► New Session Button
    │       │       └──► Clear / New UUID
    │       │
    │       └──► Settings Sidebar
    │               └──► Config overrides (optional)
    │
    └──► [FastAPI Backend]
            └──► REST endpoints
```

**Key Files:**
- `ui/streamlit_app.py` - Main Streamlit application
- `ui/components.py` - Reusable UI components
- `api/routes.py` - FastAPI endpoints
- `api/models.py` - Pydantic request/response models

---

## Dependency Chains

### Critical Path (Sprint 0-1)

```
Configuration
    │
    ├──► LLM Interface ──────────────────┐
    │                                      │
    ├──► FAISS Index ──► Embedding Gen ────┤
    │                                      │
    ├──► Document Loaders ─► Chunking ─────┤
    │                                      │
    └──► Ingestion Pipeline (combines all)─┘
```

### Retrieval Path (Sprint 2)

```
Configuration
    │
    ├──► FAISS Index ───────────────────┐
    │                                     │
    ├──► BM25 Index (depends on chunking)─┤
    │                                     │
    ├──► RRF Fusion ◄─────────────────────┤
    │                                     │
    └──► Retrieval Module ───► LangGraph ──┴──► LLM
```

### User Facing (Sprint 3)

```
Session ─┐
         ├──► LangGraph ───► UI / API
LLM ─────┘
```

---

## Module Import Hierarchy

### Package Structure

```
banking_rag/
├── __init__.py
├── config/
│   ├── __init__.py
│   ├── loader.py          # Load and validate config
│   ├── schema.py          # Pydantic models
│   └── settings.py        # Runtime settings
│
├── embeddings/
│   ├── __init__.py
│   └── generator.py       # BAAI/bge-small-en
│
├── ingestion/
│   ├── __init__.py
│   ├── pipeline.py        # Orchestrator
│   ├── loaders/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── pdf.py
│   │   ├── docx.py
│   │   ├── html.py
│   │   └── txt.py
│   ├── chunkers.py        # Section-level semantic
│   ├── pii_detector.py
│   └── metadata.py
│
├── retrieval/
│   ├── __init__.py
│   ├── dense.py           # FAISS retriever
│   ├── sparse.py          # BM25 retriever
│   ├── fusion.py          # RRF fusion
│   └── reranker.py        # Cross-encoder
│
├── index/
│   ├── __init__.py
│   └── faiss_index.py     # Index manager
│
├── workflow/
│   ├── __init__.py
│   ├── state.py           # RAGState
│   ├── graph.py           # LangGraph
│   ├── nodes.py           # Node functions
│   └── prompts.py         # Prompt templates
│
├── generation/
│   ├── __init__.py
│   └── grounded_gen.py    # Response generation
│
├── llm/
│   ├── __init__.py
│   ├── client.py          # Unified interface
│   ├── base.py            # Abstract base
│   ├── openai_provider.py
│   └── ollama_provider.py
│
├── sessions/
│   ├── __init__.py
│   ├── store.py           # In-memory store
│   └── manager.py
│
├── security/
│   ├── __init__.py
│   ├── rate_limiter.py
│   ├── input_guard.py     # PII detection
│   └── injection_detect.py
│
├── ui/
│   ├── __init__.py
│   └── streamlit_app.py
│
├── api/
│   ├── __init__.py
│   ├── routes.py
│   └── models.py
│
└── utils/
    ├── __init__.py
    └── logging.py
```

---

## Data Flow Diagrams

### 1. Document Ingestion Flow

```
Raw Document (PDF/DOCX/HTML)
    │
    ├─► Detect format ──► Reject if unsupported
    │
    ├─► Extract text ──► Structured content + sections
    │
    ├─► PII scan ──► Reject if sensitive PII detected
    │
    ├─► Chunk (section-level, 512 tokens) ──► Chunks with metadata
    │
    ├─► Tag metadata ──► banking_category, document_type
    │
    ├─► Embed (BAAI/bge-small-en) ──► 384-dim vectors
    │
    ├─► Add to FAISS index ──► Index + metadata mapping
    │
    ├─► Update BM25 index ──► Inverted index
    │
    └─► Persist ──► Disk (index + metadata)
```

### 2. Query-Response Flow

```
User Query
    │
    ├─► Security check ──► Block if injection/PII
    │
    ├─► Route intent ──► FAQ / Greeting / Irrelevant
    │
    ├─► Embed query ──► 384-dim vector
    │
    ├─► FAISS search ──► Top-10 chunks
    │
    ├─► BM25 search ──► Top-10 chunks
    │
    ├─► RRF fusion ──► Combined rank (k=60)
    │
    ├─► Rerank (optional) ──► Cross-encoder scores
    │
    ├─► Assemble context ──► Formatted context string
    │
    ├─► Build prompt ──► System + context + query
    │
    ├─► LLM generate ──► Response + citations
    │
    ├─► Validate ──► Abstain if low confidence
    │
    ├─► Format citations ──► [1], [2], etc.
    │
    ├─► Update session ──► Add to history
    │
    └─► Return to user ──► Response + sources
```

---

## Performance Considerations

### Memory Requirements

| Component | v1 Target | Memory | Storage |
|-----------|-----------|--------|---------|
| FAISS Index | 10K docs @ 384d | ~30MB | ~15MB |
| BM25 Index | 10K docs | ~20MB | ~10MB |
| Embeddings | Cached | ~15MB | - |
| Session Store | 100 sessions | ~5MB | - |
| Total | | ~70MB | ~25MB |

### Latency Targets

| Operation | Target | Max |
|-----------|--------|-----|
| Document load | < 500ms/page | 2s |
| Chunking | < 100ms/doc | 500ms |
| Embedding generation | < 10ms/chunk | 50ms |
| FAISS search (10K) | < 50ms | 100ms |
| BM25 search | < 100ms | 200ms |
| Fusion + Rerank | < 50ms | 100ms |
| LLM generation | < 800ms | 2s |
| **Total p50** | **< 1.0s** | **< 2.5s** |

---

## Risk Points

| Risk | Mitigation | Owner Module |
|------|------------|--------------|
| FAISS memory growth | Monitor size, switch to IVF if >50K | index/ |
| BM25 performance | Pre-tokenize documents | retrieval/ |
| LLM timeout | Retry with exponential backoff | llm/ |
| Session leak | TTL cleanup + limits | sessions/ |
| PII leak | Presidio + regex validation | security/ |

---

## Version Migration

### v1 (Current)
- FAISS IndexFlatIP (exact search)
- In-memory session store
- Local-only embedding model

### v2+ (Future)
- FAISS IndexIVFFlat (if scale > 50K)
- Optional: Weaviate/Chroma cloud
- SQLite session persistence
- Cross-encoder reranking default

---

*End of Dependency Graph*

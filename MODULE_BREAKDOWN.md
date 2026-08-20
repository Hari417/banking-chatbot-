# Banking RAG Chatbot - Module Breakdown

## Overview

This document breaks down the Banking RAG Chatbot into implementable modules with clear interfaces, dependencies, and incremental delivery milestones.

---

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              presentation                                      │
│                    (Streamlit UI / CLI / API layer)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                              orchestration                                    │
│                         (LangGraph workflow)                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                              retrieval                                         │
│              (vector search + reranking + hybrid retrieval)                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                              indexing                                          │
│           (document ingestion + chunking + embedding + FAISS)               │
├─────────────────────────────────────────────────────────────────────────────┤
│                              storage                                           │
│                    (FAISS index + metadata persistence)                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                              LLM                                               │
│                   (OpenAI-compatible provider)                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Core Modules

### 1. Configuration Management

**Responsibility**: Load, validate, and provide access to configuration settings

**Key Components**:
- `config.yaml` loader with schema validation
- Environment variable overlay
- LLM provider configuration (OpenAI-compatible endpoints)
- Embedding model configuration
- FAISS persistence configuration
- Logging configuration

**Dependencies**: None

**Delivery Milestone**: Sprint 0 (foundational)

---

### 2. Document Ingestion Pipeline

**Responsibility**: Load, clean, and prepare documents from various sources

**Submodules**:
- `loaders/` - Document loaders for common formats
  - PDF loader (PyPDFium2 / pdfplumber)
  - DOCX loader (python-docx)
  - TXT loader
  - HTML loader (BeautifulSoup)
- `cleaners/` - Document cleaning utilities
  - Header/footer removal
  - Page number removal
  - Extra whitespace normalization
  - Table extraction and formatting

**Input**: Local file paths / URLs / directories

**Output**: List of Document objects with metadata (source, page, timestamp)

**Dependencies**: Configuration

**Delivery Milestone**: Sprint 1

---

### 3. Document Chunking

**Responsibility**: Split documents into semantically meaningful chunks

**Strategies**:
- Fixed-size chunking (configurable, e.g., 512 tokens)
- Recursive character chunking (with overlap)
- Semantic chunking (sentence boundary aware)
- Hybrid chunking (combine strategies)

**Output**: List of chunked Document objects with:
- `content`: Text content
- `metadata`: Source info, chunk index, token count
- `chunk_id`: Unique identifier

**Dependencies**: Configuration, Document Ingestion

**Delivery Milestone**: Sprint 1

---

### 4. Embedding Generation

**Responsibility**: Convert text chunks into vector embeddings

**Submodules**:
- `embeddings/` - OpenAI-compatible embedding endpoints
  - Local embedding models (ONNX / sentence-transformers)
  - Remote API endpoints
  - Fallback strategy

**Configuration**:
- Model name
- Embedding dimensions
- Batch size
- Timeout

**Output**: Embeddings array + metadata mapping

**Dependencies**: Configuration

**Delivery Milestone**: Sprint 1

---

### 5. Vector Database Interface (FAISS)

**Responsibility**: Index creation, persistence, and retrieval

**Submodules**:
- `faiss_index/` - FAISS index management
  - Index creation from chunk embeddings
  - Index persistence to disk
  - Index loading from disk
  - Metadata mapping (chunk_id → metadata)
  - Vector searching with configurable k

**Key Features**:
- FAISS index types (IndexFlatIP, IndexIVFFlat)
- Binary/float precision tradeoffs
- Memory-mapped I/O options
- Persistence format (`.faiss` + `.json`)

**Dependencies**: Embedding Generation, Configuration

**Delivery Milestone**: Sprint 1

---

### 6. Retrieval Engine

**Responsibility**: Query processing and result ranking

**Submodules**:
- `retrieval/` - Retrieval operations
  - Query embedding
  - Vector similarity search
  - Result filtering by metadata
  - Score thresholding

**Interfaces**:
```
Retriever {
  retrieve(query: str, k: int, filter: dict) -> List[RetrievedChunk]
}

RetrievedChunk {
  content: str
  score: float
  metadata: dict
  chunk_id: str
}
```

**Dependencies**: FAISS Index, Embedding Generation

**Delivery Milestone**: Sprint 2

---

### 7. Reranking / Hybrid Retrieval

**Responsibility**: Improve retrieval quality through reranking

**Strategies**:
- Cross-encoder reranking (local or API)
- Hybrid keyword + vector search (BM25)
- RRF (Reciprocal Rank Fusion)
- Query expansion / rewriting

**Dependencies**: Configuration (optional - for v2)

**Delivery Milestone**: Sprint 3 (optional enhancement)

---

### 8. LangGraph Workflow

**Responsibility**: Orchestrate the RAG pipeline as a state machine

**Graph Structure**:
```
graph TD
    A[Start] --> B[Parse Query]
    B --> C[Query Analysis]
    C --> D[Retrieval]
    D --> E[Reranking]
    E --> F[Grounded Generation]
    F --> G[Response Formatting]
    G --> H[End]
```

**State Schema**:
```python
class RAGState(TypedDict):
    query: str
    context: List[RetrievedChunk]
    messages: List[ChatMessage]
    response: str
    citations: List[Citation]
    metadata: dict
```

**Dependencies**: Retrieval Engine, Language Model Interface

**Delivery Milestone**: Sprint 2

---

### 9. Language Model Interface

**Responsibility**: Interact with LLM providers

**Interfaces**:
```
LLMClient {
  generate(prompt: str, temperature: float, stream: bool) -> str
  chat(messages: List[ChatMessage], temperature: float) -> ChatMessage
}
```

**Providers**:
- OpenAI (GPT-4, GPT-3.5-turbo)
- OpenAI-compatible endpoints
- Local LLMs (GGUF via llama.cpp)

**Dependencies**: Configuration

**Delivery Milestone**: Sprint 0 (foundational)

---

### 10. Grounded Generation

**Responsibility**: Generate responses grounded in retrieved context

**Strategies**:
- Prompt templates with context injection
- CoT (Chain of Thought) prompting
- Self-check / self-citation prompting
- Abstention when insufficient evidence

**Output**:
- `response`: Generated answer
- `citations`: List of source chunks cited
- `confidence`: Self-assessed confidence score
- `abstained`: Boolean flag for low-confidence cases

**Dependencies**: LangGraph Workflow, Language Model Interface, Retrieval

**Delivery Milestone**: Sprint 2

---

### 11. Session Management

**Responsibility**: Maintain conversation state across turns

**Features**:
- In-memory session store
- Session ID generation
- Message history
- Context window management
- Session reset/creation

**Interfaces**:
```
SessionManager {
  create_session() -> SessionID
  add_message(session_id, message) -> None
  get_history(session_id) -> List[ChatMessage]
  reset_session(session_id) -> None
}
```

**Dependencies**: None (or minimal)

**Delivery Milestone**: Sprint 3

---

### 12. Presentation Layer

**Responsibility**: User-facing interface

**Components**:
- `ui/` - Streamlit-based UI
  - Chat interface
  - Source citation display
  - Query history
  - Session management
- `api/` - REST API layer (optional)
  - `/chat` endpoint
  - `/health` endpoint
  - `/sessions` endpoint
- `cli/` - CLI interface (optional)

**Dependencies**: LangGraph Workflow, Session Management

**Delivery Milestone**: Sprint 3

---

### 13. Monitoring & Logging

**Responsibility**: System observability

**Features**:
- Structured logging (JSON format)
- Metrics collection (latency, token count, retrieval quality)
- Error tracking
- Request tracing
- Performance dashboards (optional)

**Dependencies**: Configuration

**Delivery Milestone**: Sprint 4

---

## Third-Party Services / Libraries

### Required Dependencies

| Library | Purpose | Notes |
|---------|---------|-------|
| `langchain-core` | Core RAG abstractions | LangGraph foundation |
| `faiss-cpu` | Vector similarity search | CPU version for local deployment |
| `chromadb` | Optional: embedding cache | Not required for v1 |
| `numpy` | Vector operations | Required by FAISS |
| `pydantic` | Data validation | Configuration objects |
| `python-dotenv` | Environment loading | Optional |
| `PyPDFium2` or `pdfplumber` | PDF processing | Choose one |
| `python-docx` | DOCX processing | Optional |
| `sentence-transformers` | Local embeddings | Optional, fallback option |

### Optional Dependencies

| Library | Purpose | Notes |
|---------|---------|-------|
| `llama.cpp` | Local LLM inference | GGUF model support |
| `streamlit` | Web UI | User-friendly interface |
| `uvicorn` | API server | For REST endpoint |
| `pytest` | Testing | Development dependency |
| `black`, `ruff` | Code quality | Development dependency |

### External API Services (Optional)

| Service | Purpose | Cost | Notes |
|---------|---------|------|-------|
| OpenAI API | Embeddings, LLM | Pay-per-use | Recommended for v1 |
| Cohere API | Embeddings | Pay-per-use | Alternative |
| Local models | All-inference | Free (after download) | Hardware intensive |

---

## Implementation Order (Incremental Delivery)

### Sprint 0: Foundation (1 week)
- Configuration management
- LLM interface (OpenAI-compatible)
- FAISS index creation basics
- Basic document loader (PDF/TXT)

### Sprint 1: Core RAG (1-2 weeks)
- Document ingestion pipeline
- Document chunking
- Embedding generation
- FAISS persistence
- Basic retrieval

### Sprint 2: Workflow & Generation (1-2 weeks)
- LangGraph workflow orchestration
- Grounded generation with citations
- Session management basics

### Sprint 3: Enhancement (1-2 weeks)
- Reranking / hybrid retrieval
- Session management enhancements
- Presentation layer (Streamlit UI)
- Error handling improvements

### Sprint 4: Hardening (1 week)
- Monitoring & logging
- Performance optimization
- Evaluation dataset setup
- Documentation

---

## Key Design Decisions

### 1. Vector Database Choice: FAISS

**Why FAISS?**
- Fast local vector similarity search
- CPU and GPU support
- Good Python bindings
- No external service dependencies
- Simple persistence model

**Tradeoffs**:
- In-memory by default (we'll use persistence for reload)
- Single-node only (acceptable for prototype)
- No distributed features (not needed for v1)

### 2. Document Processing: LangChain-inspired but Custom

**Why not full LangChain?**
- Simpler, more controllable codebase
- Less abstraction overhead
- Better control over chunking strategies
- Easier debugging

**LangChain inspirations**:
- Document abstraction
- BaseLoader pattern
- BaseRetriever pattern

### 3. Embedding Strategy: OpenAI-Compatible

**Why OpenAI-compatible?**
- Proven embedding quality (text-embedding-3)
- Easy fallback to local models
- Standard interface
- Multiple provider options

**Local option**: sentence-transformers as fallback

### 4. Workflow Orchestration: LangGraph

**Why LangGraph?**
- State machine approach for RAG
- Built-in persistence hooks
- Clear separation of concerns
- Active community support

### 5. Persistence Layer: File-based

**Why file-based?**
- No PostgreSQL required (per requirements)
- Simple for local testing
-FAISS handles vector persistence natively
- JSON metadata files

**Future upgrade**: PostgreSQL for production

### 6. UI: Streamlit

**Why Streamlit?**
- Fast prototyping
- No frontend infrastructure
- Python-only development
- Good for internal tools

**Future upgrade**: React + FastAPI for production

---

## Testing Strategy

### Unit Tests
- Document loaders (various formats)
- Chunking logic (boundary conditions)
- Embedding generation (error handling)
- FAISS operations (index CRUD)
- Retrieval (scoring, filtering)
- Generation (prompt construction)

### Integration Tests
- End-to-end RAG pipeline
- Multi-turn sessions
- Error recovery paths
- Persistence/reload cycles

### Evaluation Tests
- Retrieval quality (precision@k, recall)
- Generation quality (factuality, grounding)
- Abstention behavior (when to say "I don't know")

---

## Dependencies Graph (Simplified)

```
Configuration
    ↓
  LLM Client ────────────────────────┐
    ↓                                ↓
FAISS Index ◄────────────────── Embeddings
    ↓                                ↓
  Retrieval ◄───────────────────────────
    ↓
LangGraph Workflow
    ↓
Session Manager ───────────┐
    ↓                      ↓
Grounded Generation ──► Presentation
    ↓
Monitoring & Logging
```

---

## Risk Mitigation

### Technical Risks

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Embedding quality issues | High | Start with proven model (text-embedding-3) |
| Retrieval not finding relevant docs | High | Implement reranking, test with sample queries |
| Hallucination / factuality | High | Grounded generation, citations, confidence scores |
| Slow performance | Medium | Chunking optimization, batching, caching |
| Memory usage high | Medium | Stream processing, FAISS memory options |

### Schedule Risks

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Research takes longer | Medium | Fixed-time research spikes |
| Integration complexities | Medium | Incremental delivery, test early |
| Model unavailable | Low | Fallback to local models |

---

## Success Criteria

### Functional
- Can load banking documents (PDF, DOCX, TXT)
- Processes documents into chunks with metadata
- Generates embeddings for chunks
- Stores index and loads it on restart
- Answers queries using retrieved context
- Produces citations for answers
- Maintains session history
- Abstains when insufficient evidence

### Non-Functional
- User query to answer: < 5 seconds (80th percentile)
- Document ingestion: < 10 minutes for 100-page PDF
- Index load time: < 5 seconds
- Zero external service dependencies (except LLM/embeddings API)

---

## Future Enhancements (Post-v1)

1. Multi-doc Q&A with cross-document references
2. Conversation summarization for long sessions
3. User feedback collection (thumbs up/down)
4. Knowledge base versioning
5. Administrative UI for document management
6. Advanced analytics on query patterns
7. A/B testing for retrieval strategies
8. Security audit mode for prompts

---

*Document version: 1.0*
*Last updated: 2026-08-20*

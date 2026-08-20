# Banking RAG Chatbot - Dependency Graph

## Overview

This document illustrates the module dependencies and execution flow for the Banking RAG Chatbot system.

---

## High-Level Architecture Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USERS / CLIENTS                                  │
│                              (Streamlit / API / CLI)                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PRESENTATION LAYER                                  │
│                    (Streamlit UI / REST API / CLI)                            │
│  • Session management                                                         │
│  • User input handling                                                        │
│  • Response display                                                           │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          ORCHESTRATION LAYER                                  │
│                         (LangGraph Workflow)                                  │
│  • State management                                                           │
│  • Workflow control                                                           │
│  • Context assembly                                                           │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
          ┌───────────────────────────┼───────────────────────────┐
          ▼                           ▼                           ▼
┌─────────────────────┐     ┌─────────────────────┐    ┌─────────────────────┐
│    RETRIEVAL        │     │     GENERATION      │    │    RERANKING        │
│     LAYER           │     │     LAYER           │    │     (Optional)      │
│                     │     │                     │    │                     │
│ • Query processing  │     │ • Prompt assembly   │    │ • Reranking         │
│ • Vector search     │     │ • LLM inference     │    │ • Hybrid retrieval  │
│ • Metadata mapping  │     │ • Citation extraction│   │ • RRF fusion        │
│ • Score filtering   │     │ • Abstention logic  │    │                     │
└─────────────────────┘     └─────────────────────┘    └─────────────────────┘
          ▲                           │                           ▲
          │                           ▼                           │
          └───────────────────────┌───────────────────┐           │
                                  │  INDEXING LAYER   │           │
                                  │                   │           │
                                  │ • Document        │           │
                                  │   ingestion       │           │
                                  │ • Chunking        │           │
                                  │ • Embedding       │           │
                                  │ • FAISS index     │           │
                                  │ • Metadata storage│           │
                                  └───────────────────┘           │
                                            │                     │
                                            ▼                     │
                                  ┌───────────────────┐           │
                                  │   STORAGE LAYER   │           │
                                  │                   │           │
                                  │ • FAISS index     │           │
                                  │   persistence     │           │
                                  │ • Metadata JSON   │           │
                                  │ • Document cache  │           │
                                  └───────────────────┘           │
                                            │                     │
                                            └─────────────────────┘
                                                      │
                                                      ▼
                                          ┌─────────────────────┐
                                          │      LLM API        │
                                          │ (OpenAI-compatible) │
                                          └─────────────────────┘
```

---

## Module Dependencies Matrix

| Module | Depends On | Priority |
|--------|-----------|----------|
| **Configuration** | - | Core (Sprint 0) |
| **Document Ingestion** | Configuration | Sprint 1 |
| **Chunking** | Configuration, Document Ingestion | Sprint 1 |
| **Embedding Generation** | Configuration | Sprint 1 |
| **FAISS Index** | Configuration, Embedding Generation | Sprint 1 |
| **Retrieval** | Configuration, FAISS Index | Sprint 2 |
| **Reranking** | Configuration, Retrieval | Sprint 3 (optional) |
| **Language Model Interface** | Configuration | Sprint 0 |
| **LangGraph Workflow** | Configuration, Retrieval, LLM Interface | Sprint 2 |
| **Grounded Generation** | Configuration, LangGraph Workflow, LLM Interface | Sprint 2 |
| **Session Management** | Configuration | Sprint 3 |
| **Presentation Layer** | Configuration, LangGraph Workflow, Session Management | Sprint 3 |
| **Monitoring & Logging** | Configuration | Sprint 4 |

---

## Detailed Module Dependencies

### Configuration Module
```
Configuration
├── config.yaml (primary configuration)
├── .env (API keys and secrets)
└── Environment variables (runtime overrides)
```

**No dependencies** - This is the root of the dependency tree.

---

### Document Ingestion Module
```
Document Ingestion
├── Configuration (for file paths, processing options)
├── PDF Loader (PyPDFium2 / pdfplumber)
├── DOCX Loader (python-docx)
├── TXT Loader (built-in)
├── cleaners/ (header/footer removal, whitespace normalization)
└── Output: List[Document] with metadata
```

**Dependencies**: Configuration

---

### Chunking Module
```
Chunking
├── Configuration (chunk size, overlap, strategy)
├── Document Ingestion (input documents)
├── Tokenizer (for token-based chunking)
├── Strategy implementations:
│   ├── FixedSizeChunker
│   ├── RecursiveCharacterChunker
│   ├── SemanticChunker
│   └── HybridChunker
└── Output: List[Chunk] with chunk_id and metadata
```

**Dependencies**: Configuration, Document Ingestion

---

### Embedding Generation Module
```
Embedding Generation
├── Configuration (model name, batch size, timeout)
├── Embedding Provider:
│   ├── OpenAICompatible (remote API)
│   ├── SentenceTransformers (local model)
│   └── Fallback chain
└── Output: List[Embedding] + Chunk-embedding mapping
```

**Dependencies**: Configuration

---

### FAISS Index Module
```
FAISS Index
├── Configuration (index type, dimensions, persistence path)
├── Embedding Generation (vector embeddings)
├── Chunking (metadata mapping)
├── FAISS Index types:
│   ├── IndexFlatIP (exact search, small datasets)
│   ├── IndexIVFFlat (approximate search, large datasets)
│   └── IndexHNSW (fast search, memory tradeoffs)
├── Persistence:
│   ├── save_index(path)
│   ├── load_index(path)
│   ├── save_metadata(path)
│   └── load_metadata(path)
└── Search operations:
    ├── knn(query_vector, k)
    ├── filter_by_metadata(query, filter)
    └── score_thresholding(results, threshold)
```

**Dependencies**: Configuration, Embedding Generation, Chunking

---

### Retrieval Module
```
Retrieval
├── Configuration (k, score threshold, filter options)
├── FAISS Index (vector search)
├── Query processing:
│   ├── Query embedding
│   ├── Metadata filtering
│   └── Result reordering
├── Output: List[RetrievedChunk] with content, score, metadata
└── Optional: Reranking integration
```

**Dependencies**: Configuration, FAISS Index

---

### Reranking Module (Optional)
```
Reranking
├── Configuration (reranker model, score threshold)
├── Retrieval (candidate chunks)
├── Reranker types:
│   ├── CrossEncoder (pairwise scoring)
│   ├── HybridRetriever (BM25 + vector)
│   └── RRF (Reciprocal Rank Fusion)
└── Output: Reranked List[RetrievedChunk]
```

**Dependencies**: Configuration, Retrieval

---

### Language Model Interface Module
```
LLM Interface
├── Configuration (provider, model, temperature, timeout)
├── Provider implementations:
│   ├── OpenAI (GPT-4, GPT-3.5-turbo)
│   ├── OpenAI-compatible (local models, other APIs)
│   └── Local (llama.cpp, Ollama)
├── Methods:
│   ├── generate(prompt, temperature, stream)
│   ├── chat(messages, temperature)
│   └── tokenize(text) -> int
└── Output: Generated text or ChatMessage
```

**Dependencies**: Configuration

---

### LangGraph Workflow Module
```
LangGraph Workflow
├── Configuration (graph options, state schema)
├── State definition (RAGState TypedDict)
├── Nodes:
│   ├── parse_query (extract intent)
│   ├── retrieval (call Retrieval module)
│   ├── reranking (optional)
│   ├── grounded_generation (call Generation module)
│   └── format_response (add citations, confidence)
├── Edges:
│   ├── parse_query → retrieval
│   ├── retrieval → reranking (if enabled)
│   ├── retrieval → grounded_generation (fallback)
│   ├── reranking → grounded_generation
│   └── grounded_generation → format_response
├── Input: User query
└── Output: Response with citations and metadata
```

**Dependencies**: Configuration, Retrieval, LLM Interface

---

### Grounded Generation Module
```
Grounded Generation
├── Configuration (prompt template, max tokens, abstention threshold)
├── LangGraph Workflow (context assembly)
├── Prompt templates:
│   ├── base_prompt (system + context)
│   ├── few_shot_examples (optional)
│   └── abstention_prompt (when confidence low)
├── Generation strategies:
│   ├── Direct generation
│   ├── Chain of Thought
│   └── Self-check prompting
├── Output:
│   ├── response (generated answer)
│   ├── citations (list of cited chunks)
│   ├── confidence (self-assessment)
│   └── abstained (boolean flag)
└── Fallback: "I don't know" when confidence below threshold
```

**Dependencies**: Configuration, LangGraph Workflow, LLM Interface

---

### Session Management Module
```
Session Management
├── Configuration (session TTL, max messages)
├── Session store (in-memory dict or SQLite)
├── Operations:
│   ├── create_session() → SessionID
│   ├── add_message(session_id, message)
│   ├── get_history(session_id)
│   ├── update_context(session_id, context)
│   └── reset_session(session_id)
├── State management:
│   ├── Message history (ChatMessage list)
│   ├── Context window management
│   └── Session metadata
└── Output: Session state for workflow
```

**Dependencies**: Configuration

---

### Presentation Layer Module
```
Presentation Layer
├── Configuration (UI options, API ports)
├── Streamlit UI:
│   ├── Chat interface (input, display)
│   ├── Session sidebar
│   ├── Source citation panel
│   ├── Query history
│   └── Settings panel
├── REST API (optional):
│   ├── POST /chat
│   ├── GET /health
│   ├── GET /sessions
│   └── POST /sessions
├── CLI interface (optional):
│   ├── Interactive mode
│   └── One-shot query mode
└── Output: User-facing interface
```

**Dependencies**: Configuration, LangGraph Workflow, Session Management

---

### Monitoring & Logging Module
```
Monitoring & Logging
├── Configuration (log level, metrics enabled)
├── Logging:
│   ├── Structured JSON logs
│   ├── Request/response logging
│   └── Error tracking
├── Metrics:
│   ├── Query latency (p50, p80, p95)
│   ├── Token usage
│   ├── Retrieval quality
│   └── System health
├── Integration:
│   ├── stdout/stderr
│   ├── File rotation
│   └── Optional: Prometheus export
└── Output: Observable system state
```

**Dependencies**: Configuration

---

## Execution Flow Diagrams

### 1. User Query Flow

```
User Query
    │
    ├─► [Presentation Layer]
    │   └─► Parse and validate input
    │
    ├─► [Session Management]
    │   └─► Append to conversation history
    │
    ├─► [LangGraph Workflow - Start]
    │
    ├─► [Parse Query]
    │   └─► Extract intent, entities
    │
    ├─► [Retrieval]
    │   ├─► Embed query
    │   ├─► Search FAISS index
    │   └─► Get top-k chunks
    │
    ├─► [Reranking] (Optional)
    │   └─► Reorder candidates
    │
    ├─► [Grounded Generation]
    │   ├─► Build prompt with context
    │   ├─► Call LLM
    │   └─► Extract response + citations
    │
    ├─► [Format Response]
    │   ├─► Add confidence score
    │   └─► Format output
    │
    ├─► [Session Management]
    │   └─► Append to history
    │
    └─► [Presentation Layer]
        └─► Display response to user
```

### 2. Document Ingestion Flow

```
Document (PDF/DOCX/TXT)
    │
    ├─► [Document Ingestion]
    │   ├─► Load document
    │   └─► Extract text + metadata
    │
    ├─► [Chunking]
    │   ├─► Split into chunks
    │   └─► Generate chunk IDs
    │
    ├─► [Embedding Generation]
    │   ├─► Embed each chunk
    │   └─► Generate embeddings
    │
    ├─► [FAISS Index]
    │   ├─► Add to index
    │   └─► Update metadata mapping
    │
    ├─► [Persistence]
    │   ├─► Save index to disk
    │   └─► Save metadata to disk
    │
    └─► [Monitoring]
        └─► Log ingestion stats
```

### 3. System Startup Flow

```
Start Application
    │
    ├─► [Configuration]
    │   ├─► Load config.yaml
    │   ├─► Load .env
    │   └─► Apply environment overrides
    │
    ├─► [FAISS Index]
    │   ├─► Load index from disk
    │   └─► Load metadata from disk
    │
    ├─► [Session Management]
    │   └─► Initialize in-memory store
    │
    ├─► [Monitoring]
    │   └─► Initialize logging
    │
    └─► [Presentation Layer]
        └─► Start UI / API server
```

---

## Configuration Dependencies

```
Configuration Hierarchy
    │
    ├── global
    │   ├── app_name
    │   ├── version
    │   └── environment
    │
    ├── llm
    │   ├── provider (openai, local, compatible)
    │   ├── model (gpt-4, gpt-3.5-turbo, llama-3, etc.)
    │   ├── temperature
    │   ├── max_tokens
    │   └── endpoint (for compatible providers)
    │
    ├── embeddings
    │   ├── provider (openai, local)
    │   ├── model (text-embedding-3, all-MiniLM-L6-v2)
    │   └── dimensions
    │
    ├── faiss
    │   ├── index_type (flat, ivfflat, hnsw)
    │   ├── persistence_path
    │   └── nlist (for IVF)
    │
    ├── chunking
    │   ├── strategy (fixed, recursive, semantic, hybrid)
    │   ├── chunk_size (tokens)
    │   ├── chunk_overlap
    │   └── separators
    │
    ├── retrieval
    │   ├── k (number of results)
    │   ├── score_threshold
    │   └── rerank_enabled
    │
    ├── logging
    │   ├── level (debug, info, warning, error)
    │   ├── format (json, text)
    │   └── output (stdout, file)
    │
    └── ui
        ├── theme
        ├── max_history
        └── api_enabled
```

---

## Data Flow Between Modules

```
Document
    │
    ▼
[Document Ingestion]
    │ Output: Document
    ▼
[Chunking]
    │ Output: Chunk
    ▼
[Embedding Generation]
    │ Output: Embedding (vector)
    ▼
[FAISS Index]
    │ Output: Index + MetadataMapping
    │
    │ Input: Query
    ▼
[Retrieval]
    │ Output: RetrievedChunk
    ▼
[Reranking] (Optional)
    │ Output: RerankedRetrievedChunk
    │
    │ Input: Chunk + Query
    ▼
[Grounded Generation]
    │ Output: Response + Citations
    ▼
[Presentation]
    │ Output: User-displayable result
```

---

## Testing Dependencies

```
Module Tests
    │
    ├── Configuration Tests
    │   └── Load valid/invalid configs
    │
    ├── Document Ingestion Tests
    │   ├── Test PDF loading
    │   ├── Test DOCX loading
    │   └── Test TXT loading
    │
    ├── Chunking Tests
    │   ├── Test boundary conditions
    │   ├── Test overlap behavior
    │   └── Test token counting
    │
    ├── Embedding Tests
    │   ├── Test API call
    │   ├── Test fallback
    │   └── Test batch processing
    │
    ├── FAISS Tests
    │   ├── Index CRUD operations
    │   ├── Persistence cycle
    │   └── Search accuracy
    │
    ├── Retrieval Tests
    │   ├── Score calculation
    │   ├── Filtering logic
    │   └── Threshold behavior
    │
    ├── Generation Tests
    │   ├── Prompt construction
    │   ├── Citation extraction
    │   └── Abstention logic
    │
    ├── Session Tests
    │   ├── Create/get/reset
    │   ├── History management
    │   └── Context window
    │
    └── Integration Tests
        ├── End-to-end query
        ├── Multi-turn conversation
        └── Persistence reload
```

---

## Performance Dependencies

```
Performance Considerations
    │
    ├── Latency Path
    │   ├── Document load time
    │   ├── Chunking time
    │   ├── Embedding time (batched)
    │   ├── FAISS search time (k-NN)
    │   ├── LLM inference time
    │   └── UI rendering time
    │
    ├── Throughput
    │   ├── Concurrent queries
    │   ├── Document ingestion rate
    │   ├── Memory per session
    │   └── Request queue handling
    │
    └── Resource Usage
        ├── RAM (embeddings, FAISS index)
        ├── Disk (index, documents)
        └── CPU (chunking, embeddings, reranking)
```

---

## Error Handling Dependencies

```
Error Propagation
    │
    ├── Configuration Errors
    │   └── Fail fast at startup
    │
    ├── Document Errors
    │   ├── Skip problematic files
    │   ├── Log error details
    │   └── Continue processing others
    │
    ├── Embedding Errors
    │   ├── Retry with backoff
    │   ├── Fallback to local model
    │   └── Return empty if all fail
    │
    ├── FAISS Errors
    │   ├── Recovery from backup
    │   ├── Graceful degradation
    │   └── User notification
    │
    ├── LLM Errors
    │   ├── Retry with different model
    │   ├── Return error to user
    │   └── Log for investigation
    │
    └── Session Errors
        ├── Reset corrupted sessions
        ├── Preserve valid history
        └── Notify user
```

---

## Deployment拓扑

```
Deployment Topology (Local / V1)
    │
    ├── Application Layer
    │   ├── Streamlit UI (port 8501)
    │   ├── REST API (port 8000, optional)
    │   └── Background worker (optional)
    │
    ├── Data Layer
    │   ├── Documents/ (raw files)
    │   ├── embeddings/ (cached embeddings)
    │   └── faiss/ (index + metadata)
    │
    └── External Services
        ├── OpenAI API (embeddings, LLM)
        └── Optional: Local model server (Ollama, llama.cpp)
```

---

## Future Enhancement Dependencies

```
Enhancement Dependencies (Post-v1)
    │
    ├── Multi-doc Q&A
    │   └── Requires: Cross-document chunk indexing
    │
    ├── Conversation Summarization
    │   └── Requires: Session history + LLM
    │
    ├── User Feedback System
    │   └── Requires: Session persistence + DB
    │
    ├── Knowledge Versioning
    │   └── Requires: Index versioning system
    │
    ├── Admin UI
    │   └── Requires: Document management APIs
    │
    ├── Analytics Dashboard
    │   └── Requires: Query/event logging
    │
    └── A/B Testing
        └── Requires: Experiment tracking framework
```

---

*Graph version: 1.0*
*Last updated: 2026-08-20*

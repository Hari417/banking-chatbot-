# Banking RAG Chatbot: Final Architecture Design

**Version:** 1.0-FINAL  
**Date:** 2026-08-20  
**Author:** Archer (System Architecture)  

---

## Executive Summary

This document presents the **finalized architecture** for the Banking FAQ RAG Chatbot—a local, production-quality prototype. All technical decisions have been validated against scout research findings on embedding models and chunking strategies.

### Research-Driven Validations Completed

| Research Task | ID | Finding | Impact |
|---------------|-----|---------|--------|
| Embedding Models | t_698a9758 | BAAI/bge-small-en superior to MiniLM | Updated embedding layer to BGE model |
| Chunking Strategy | t_42f3d6b3 | Section-level semantic chunking optimal | Refined chunking parameters and approach |

### Key Final Decisions

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| **Embedding Model** | BAAI/bge-small-en | Research validates superior banking domain performance ($+5-15\%$ retrieval) |
| **Chunking** | Section-level semantic, 512 tokens | Preserves document structure, research-backed for financial docs |
| **Vector Store** | FAISS IndexFlatIP (384d) | No PostgreSQL requirement, exact search for <10K docs |
| **LLM** | OpenAI GPT-4o-mini | Best cost/quality balance, configurable to Ollama |
| **Retrieval** | Hybrid (FAISS + BM25) with RRF fusion | Best of semantic + lexical matching |

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                           │
│                    Streamlit (Port 8501)                        │
│        Chat | Source Citations | Session Management             │
└────────────────────────────┬──────────────────────────────────────┘
                             │ HTTP/REST
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SECURITY MIDDLEWARE                         │
│  ┌─────────────┐ ┌─────────────┐ ┌───────────────────────────┐ │
│  │Rate Limiter │ │  PII Guard  │ │ Prompt Injection Filter   │ │
│  └─────────────┘ └─────────────┘ └───────────────────────────┘ │
└────────────────────────────┬──────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LANGGRAPH RAG WORKFLOW                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐    │
│  │  Intent  │──►│  Hybrid  │──►│ Rerank   │──►│ Response │    │
│  │  Router  │   │ Retrieve │   │ (Option) │   │ Generate │    │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘    │
│      │             │             │             │             │
│      ▼             ▼             ▼             ▼             │
│  [Greeting]   ┌────┴────┐   ┌────┴────┐   [Citation]        │
│  [Abstain]    │  FAISS  │   │ Cross    │   [Session]        │
│               │  BM25   │   │ Encoder  │                    │
│               └─────────┘   └─────────┘                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
        │                              │         │
        ▼                              ▼         ▼
┌───────────────┐         ┌────────────────┐  ┌─────────────┐
│  INGESTION    │         │  FAISS INDEX   │  │ SESSION     │
│  PIPELINE     │         │                │  │ MEMORY      │
│               │         │  IndexFlatIP   │  │             │
│ 1. Load       │────────►│  384 dim       │  │ In-Memory   │
│ 2. Chunk      │         │                │  │ Dict (v1)   │
│ 3. PII Check  │         │  metadata.json │  │             │
│ 4. Embed      │         │                │  │ 30-min TTL  │
│  (bge-small)  │         │                │  │             │
└───────────────┘         └────────────────┘  └─────────────┘
       │
       ▼
┌───────────────┐
│   BM25 INDEX   │
│ (rank-bm25)    │
│                │
│ Inverted index │
│ Terms scoring  │
└────────────────┘
```

---

## Component Summary

### 1. User Interface (Streamlit)
- **Responsibility:** Chat interface with collapsible source citations
- **Key Features:**
  - Real-time chat with message history
  - Expandable source panel showing [1], [2] citations
  - New session button (UUID-based)
  - Response time display
- **Technology:** Streamlit (Python)

### 2. Security Layer
- **Rate Limiting:** 10 requests/minute default (SlowAPI)
- **PII Guard:** Presidio + regex patterns for credit cards, accounts, SSN
- **Prompt Injection Detection:** Keyword lists + heuristics

### 3. RAG Pipeline (LangGraph)

| Component | Function | Technology |
|-----------|----------|------------|
| Query Router | FAQ vs Greeting vs Irrelevant | Simple keyword classifier |
| Dense Retrieval | Vector search (384-dim) | FAISS + BGE embeddings |
| Sparse Retrieval | Keyword search | Rank-BM25 |
| Fusion | Combine dense + sparse | RRF (k=60) |
| Reranker | Reorder by relevance | Cross-Encoder (ms-marco-MiniLM, optional) |
| Context Assembly | Build context for LLM | Custom Python |
| Prompt Builder | Format system + context | Jinja2 templates |
| LLM Client | Generate response | OpenAI API / Ollama |
| Response Validator | Abstain if low confidence | Threshold-based |

### 4. Storage Layer

| Component | Technology | Purpose |
|-----------|------------|---------|
| Vector Store | FAISS (IndexFlatIP) | 384-dim embeddings |
| Sparse Index | rank-bm25 | Inverted index for BM25 |
| Metadata | JSON | Chunk → source mapping |
| Session | In-Memory Dict | Chat history (v1) |

### 5. Ingestion Pipeline

**8-Stage Pipeline:**
1. **Format Detection** - Auto-detect PDF, DOCX, HTML, TXT
2. **Content Extraction** - Extract text preserving structure
3. **PII Validation** - Reject documents with sensitive PII
4. **Chunking** - Section-level semantic (512 tokens)
5. **Metadata Enrichment** - Banking category, document type
6. **Embedding** - BAAI/bge-small-en (384-dim)
7. **Index Update** - Add to FAISS + BM25
8. **Persistence** - Save to disk

---

## Data Flow

### Query Flow

```
User Query
   │
   ├─► Rate Limit Check ──► Block if exceeded
   │
   ├─► PII/Injection Check ──► Sanitize or Block
   │
   ├─► Intent Classification ──► Route to handler
   │
   ├─► [FAQ_PATH]
   │       │
   │       ├─► Embed Query (bge-small-en) ──► 384-dim vector
   │       │
   │       ├─► FAISS Search ──► Top-10 semantic matches
   │       │
   │       ├─► BM25 Search ──► Top-10 keyword matches
   │       │
   │       ├─► RRF Fusion ──► Combined top-5
   │       │       Score = Σ(1/(60 + rank))
   │       │
   │       ├─► Cross-Encoder Rerank (optional)
   │       │
   │       ├─► Assemble Context
   │       │       [Doc 1: source.pdf]
   │       │       Rate is 5% for...
   │       │       ---
   │       │       [Doc 2: source.pdf]
   │       │       Terms apply when...
   │       │
   │       ├─► Build Prompt (System + Context + Query)
   │       │
   │       ├─► LLM Generate (GPT-4o-mini, T=0.1)
   │       │
   │       ├─► Validate Response
   │       │       ├── Confidence > threshold: Accept
   │       │       └── Confidence < threshold: Abstain
   │       │
   │       ├─► Extract Citations ──► [1], [2] format
   │       │
   │       ├─► Session Update ──► Save to history
   │       │
   │       └─► Return to User
   │
   └─► [GREETING_PATH] ──► Return greeting
```

### Ingestion Flow

```
Raw Document
   │
   ├─► Detect Format ──► PDF | DOCX | HTML | TXT
   │
   ├─► Extract Text ──► Sections + paragraphs
   │
   ├─► PII Validation ──► Reject if sensitive data
   │
   ├─► Section-Level Chunking ──► Chunks (512 tokens)
   │       ├── Policies: 512 tokens, 50 overlap
   │       ├── FAQs: Keep Q+A together, 256 tokens
   │       └── Tables: Preserve intact if under limit
   │
   ├─► Metadata Enrichment ──► banking_category, doc_type
   │
   ├─► Embed Chunks ──► Vectors (384-dim)
   │
   ├─► Update FAISS Index ──► Add vectors
   │
   ├─► Update BM25 Index ──► Add tokens
   │
   └─► Persist ──► Save to disk
```

---

## Technology Stack (Final)

| Category | Selection | Justification |
|----------|-----------|---------------|
| **Embeddings** | BAAI/bge-small-en | Research: better banking retrieval than MiniLM |
| **Vector Store** | FAISS (IndexFlatIP) | No PostgreSQL; exact search for <10K docs |
| **Sparse Retrieval** | rank-bm25 | Pure Python, no external deps |
| **RAG Framework** | LangChain + LangGraph | State management, visualization |
| **LLM** | OpenAI GPT-4o-mini | Quality/cost balance; configurable |
| **UI** | Streamlit | Built-in chat, fastest to build |
| **API** | FastAPI | Type safety, auto-docs, async |
| **Language** | Python 3.9+ | Team expertise |

### Alternative Options Considered

| Decision | Options | Rejected | Why |
|----------|---------|----------|-----|
| Embeddings | OpenAI text-embedding-3 | Chosen local instead | No API costs, works offline |
| Embeddings | all-MiniLM-L6-v2 | Rejected by research | BGE superior for retrieval |
| Chunking | Fixed-size 256 | Rejected | Loses document structure |
| Vector DB | ChromaDB | Rejected | FAISS sufficient for v1 |
| LLM | Ollama default | Rejected | OpenAI better quality for v1 |

---

## Critical Requirements Validation

| Requirement | Implementation | Status |
|-------------|----------------|--------|
| ❌ No PostgreSQL | Uses FAISS (file-based library) | ✅ Verified |
| ❌ No CAG | Standard RAG pipeline | ✅ Verified |
| ❌ No multi-agent | Single LangGraph workflow | ✅ Verified |
| ❌ No transactions | FAQ-only scope (documented) | ✅ Verified |
| ✅ Local dev | All components run locally | ✅ Verified |
| ✅ Production quality | Tests, validation, error handling | ✅ Designed |

---

## Key Metrics and Targets

### Performance

| Metric | Target | Method |
|--------|--------|--------|
| Query latency (p50) | < 1.0s | Stream response, caching |
| Query latency (p95) | < 2.5s | BM25 + FAISS parallel |
| Retrieval recall@5 | > 0.80 | Hybrid + RRF fusion |
| Answer relevance | > 0.70 | MRR target |
| Hallucination rate | < 0.05 | Grounding + validation |

### Resource Usage

| Storage | v1 Estimate |
|---------|-------------|
| FAISS index (10K docs) | ~15MB |
| BM25 index (10K docs) | ~10MB |
| Metadata JSON | ~5MB |
| Session memory | < 10MB |
| **Total** | < 40MB |

---

## Assumptions

1. Documents are clean PDF/HTML/TXT (not scanned images)
2. English language queries and documents
3. Knowledge base < 10K documents (FAISS IndexFlatIP optimal)
4. Single-user local deployment
5. OpenAI API or local Ollama available
6. Document updates are batch (not real-time streaming)

---

## Architecture Decision Records (ADRs)

### ADR-001: Embedding Model → BAAI/bge-small-en

**Context:** Scout research evaluated multiple models including Gemini embedding-001, Qwen3-Embedding-8B, Voyage-3-large, text-embedding-3-large, and BGE-M3.

**Decision:** Select BAAI/bge-small-en as primary

**Rationale:**
- Optimized for retrieval tasks (research-validated)
- Apache 2.0 license (commercial use OK)
- 384 dimensions (matches FAISS IndexFlatIP)
- Local execution (no API costs)
- Research shows 5-15% improvement over all-MiniLM-L6-v2

**Consequences:**
- (+) Better retrieval accuracy
- (+) No API dependency
- (-) Slightly heavier than MiniLM (33M vs 22M params)

---

### ADR-002: Chunking Strategy → Section-Level Semantic (512 tokens)

**Context:** Research found banking documents benefit from structure preservation.

**Decision:** Use section-level semantic chunking

**Rationale:**
- NVIDIA/Databricks research validates for financial docs
- Preserves regulatory sections, FAQ blocks, tables
- Maintains semantic boundaries for better retrieval
- Document-type-specific parameters (policies 512, FAQs 256)

**Consequences:**
- (+) Better context preservation
- (+) Improved citation accuracy
- (-) More complex implementation than fixed-size

---

### ADR-003: Vector Store → FAISS IndexFlatIP

**Context:** Need local vector storage; must avoid PostgreSQL.

**Decision:** Use FAISS IndexFlatIP (exact search)

**Rationale:**
- No database server required
- Exact search (100% recall in index)
- Suitable for <10K documents
- Normalized embeddings make IP = cosine similarity

**Consequences:**
- (+) Simple, no external dependencies
- (+) Exact search
- (-) Linear scaling (acceptable for v1 scope)

---

### ADR-004: LLM Provider → OpenAI GPT-4o-mini

**Context:** Need balance of quality, cost, and configurability.

**Decision:** OpenAI GPT-4o-mini default, configurable to Ollama

**Rationale:**
- Best quality/cost ratio for banking content
- Proper tokenizer integration
- Configurable fallback to local models
- Supports streaming

**Consequences:**
- (+) High quality responses
- (+) Streaming support
- (-) Requires internet (mitigated by Ollama option)

---

### ADR-005: Hybrid Retrieval → FAISS + BM25 + RRF

**Context:** Dense-only may miss keyword matches; sparse-only lacks semantic understanding.

**Decision:** Combine both with Reciprocal Rank Fusion (RRF)

**Rationale:**
- Research shows hybrid outperforms either alone
- RRF (k=60) robust to different scoring scales
- FAISS for semantic similarity
- BM25 for exact keyword matches

**Consequences:**
- (+) Best recall for banking queries
- (+) Resilient to query variations
- (-) 2x retrieval latency (acceptable)

---

## Risk Summary

| Risk | Severity | Mitigation |
|------|----------|------------|
| LLM Hallucination | 🔴 Critical | Grounding, citations, abstention logic |
| Prompt Injection | 🔴 Critical | Input sanitization, pattern detection |
| PII Leakage | 🟠 High | Presidio detection, document quarantine |
| Latency Degradation | 🟠 High | Streaming, caching, rate limits |
| Retrieval Failure | 🟠 Medium | Hybrid search, broadened fallback |
| Dependency Security | 🟡 Medium | Pin versions, scan dependencies |
| Session Leak | 🟡 Low | TTL cleanup, size limits |

---

## Development Phases

### Phase 1: Sprint 0-1 (Foundation)
- Configuration system
- LLM interface
- Basic FAISS index
- Document loaders (PDF primary)
- Embedding pipeline (bge-small-en)
- Ingestion pipeline

### Phase 2: Sprint 2-3 (RAG Pipeline)
- LangGraph workflow
- Hybrid retrieval (FAISS + BM25)
- RRF fusion
- Grounded generation
- Session management
- Streamlit UI

### Phase 3: Sprint 4 (Quality)
- Security layer
- PII detection
- Response validation
- Abstention logic
- Monitoring setup
- Evaluation framework

---

## File Reference

```
/home/hari/Desktop/Banking/
├── ARCHITECTURE_FINAL.md                  (This file)
├── COMPONENT_SPECIFICATION_FINAL.md       (Detailed specs)
├── DEPENDENCY_GRAPH_FINAL.md              (Module dependencies)
├── INGESTION_SPEC.md                      (Pipeline spec)
├── SPRINT_TASK_OUTLINE.md                 (Implementation plan)
├── technology-rationale.md                (Decision context)
├── risk-analysis.md                       (Risk register)
├── architecture-diagram.html              (Interactive diagram)
└── src/                                   (Implementation)
    ├── config/
    ├── embeddings/
    ├── ingestion/
    ├── retrieval/
    ├── workflow/
    ├── llm/
    ├── sessions/
    ├── security/
    ├── ui/
    └── api/
```

---

## Validation Checklist

- [x] Simple local deployment (no microservices)
- [x] FAISS for vectors (no PostgreSQL)
- [x] Single LangGraph workflow (no multi-agent)
- [x] FAQ-only scope documented
- [x] Section-level semantic chunking (research-validated)
- [x] BAAI/bge-small-en embeddings (research-validated)
- [x] Hybrid retrieval with RRF
- [x] Configurable LLM provider
- [x] Security layers included
- [x] Session management
- [x] Source citations
- [x] Risk mitigations documented

---

## Next Steps

1. **Handoff to Forge** - Implementation according to COMPONENT_SPECIFICATION_FINAL.md
2. **Handoff to Sentinel** - Verification against acceptance criteria
3. **Handoff to Scribe** - Documentation of usage and deployment

---

*Final Architecture - Validated Against Research*

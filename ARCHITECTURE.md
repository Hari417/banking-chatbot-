# Banking RAG Chatbot: Architecture Design

**Version:** 1.0  
**Date:** 2026-08-20  
**Author:** Archer (System Architecture)

---

## Overview

This document presents the complete architecture for a Banking FAQ RAG Chatbot—a local, production-quality prototype designed to answer questions about banking policies, products, fees, loans, and procedures from a knowledge base.

**Scope Statement:**
- ✅ **In scope:** FAQ, knowledge retrieval, policy questions
- ❌ **Out of scope:** Transactions, balances, real customer data, authentication

---

## Deliverables Summary

| File | Description | Size |
|------|-------------|------|
| `architecture-diagram.html` | Interactive SVG architecture diagram | 24 KB |
| `component-specification.md` | Detailed component definitions and APIs | 12 KB |
| `technology-rationale.md` | Technology selection with alternatives | 14 KB |
| `risk-analysis.md` | Risk register and mitigations | 14 KB |

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                       USER INTERFACE                        │
│                  Streamlit (Port 8501)                     │
│         Chat Interface | Source Citations | New Session    │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/REST
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    SECURITY LAYER                           │
│  ┌─────────────┐ ┌─────────────┐ ┌───────────────────────┐ │
│  │Rate Limiter │ │Input Guard  │ │Prompt Injection Filter│ │
│  └─────────────┘ └─────────────┘ └───────────────────────┘ │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    BACKEND API                              │
│                   FastAPI (Python)                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                     │
│  │ /chat   │ │ /ingest │ │ /health │                     │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘                  │
└───────┼────────────┼────────────┼──────────────────────────┘
        │            │            │
        │            ▼            │
        │  ┌──────────────────┐   │
        └──│  LANGGRAPH      │◄┐ │
           │  WORKFLOW       │ │ │
           │ ┌────────────┐ │ │ │
           │ │Query Router│─┘ │ │
           │ └─────┬──────┘    │ │
           │       ▼           │ │
           │ ┌──────────────┐   │ │
           │ │Hybrid        │   │ │
           │ │Retriever     │───┘ │
           │ └──────┬───────┘     │
           │        ▼             │
           │ ┌──────────────┐    │
           │ │Reranker      │    │
           │ └──────┬───────┘    │
           │        ▼             │
           │ ┌──────────────┐    │
           │ │Context       │    │
           │ │Assembler     │    │
           │ └──────┬───────┘    │
           │        ▼             │
           │ ┌──────────────┐    │
           │ │Prompt Builder│    │
           │ └──────┬───────┘    │
           │        ▼             │
           │ ┌──────────────┐    │
           │ │LLM Client    │────┴───► OpenAI/Ollama
           │ └──────┬───────┘
           │        ▼
           │ ┌──────────────┐
           │ │Response      │
           │ │Validator     │
           │ └──────┬───────┘
           │        ▼
           │ ┌──────────────┐
           │ │Citation Gen  │───► Session Memory
           │ └──────────────┘
           └───────────────────────

┌─────────────────────────────────────────────────────────────┐
│                    DATA LAYERS                              │
│                                                             │
│  ┌─────────────┐  ┌─────────────────┐  ┌────────────────┐ │
│  │Document     │  │ FAISS Vector   │  │Session Memory  │ │
│  │Store        │  │ Store (Local)  │  │(In-Memory/SQLite)│ │
│  └─────────────┘  └─────────────────┘  └────────────────┘ │
│       │                  │                                        │
│       ▼                  ▼                                        │
│  ┌─────────────┐  ┌─────────────────┐                          │
│  │PDF/HTML/TXT │  │Embeddings:      │                          │
│  │Chunker      │  │all-MiniLM-L6-v2 │                          │
│  │Metadata     │  │Index: Flat/IVF  │                          │
│  └─────────────┘  └─────────────────┘                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Component Summary

### 1. User Interface Layer
- **Technology:** Streamlit
- **Purpose:** Chat interface with source citations
- **Key Features:** Session management, message history, collapsible sources

### 2. Security Layer
- **Rate Limiting:** SlowAPI or Redis (10/min default)
- **Input Guard:** PII detection, length validation
- **Prompt Shield:** Injection pattern detection

### 3. Backend API
- **Technology:** FastAPI + Uvicorn
- **Endpoints:** /chat, /ingest, /health, /config
- **Models:** Pydantic validation, streaming responses

### 4. RAG Pipeline (LangGraph)
| Component | Function | Technology |
|-----------|----------|------------|
| Query Router | Classify intent, route flow | Logistic/classifier |
| Hybrid Retriever | Dense + Sparse retrieval | FAISS + Rank-BM25 |
| Reranker | Reorder by relevance | Cross-Encoder |
| Context Assembler | Build LLM input | Custom Python |
| Prompt Builder | Format system prompt | Jinja2 templates |
| LLM Client | Generate response | OpenAI API |
| Response Validator | Check grounding | Heuristics |
| Citation Generator | Map to sources | Metadata tracking |

### 5. Storage Layer
- **Documents:** Local filesystem + metadata
- **Vector Store:** FAISS (IndexFlatIP or IVF)
- **Embeddings:** Sentence-BERT
- **Session:** In-memory dict (v1) / SQLite (v2)

---

## Data Flow

```
User Query
   │
   ├─► Security Check (PII, Injection, Rate Limit)
   │       └─► Block or Sanitize
   │
   ├─► Intent Classification (FAQ vs Greeting vs Irrelevant)
   │       └─► Route to handler
   │
   ├─► Retrieve from FAISS (Dense: Embeddings)
   ├─► Retrieve from BM25 (Sparse: Keywords)
   │
   ├─► Fuse Results (Reciprocal Rank Fusion)
   │
   ├─► Rerank (Cross-Encoder)
   │
   ├─► Assemble Context (Deduplicate, Format)
   │
   ├─► Build Prompt (System + Context + Query)
   │
   ├─► LLM Generate (OpenAI/Ollama)
   │
   ├─► Validate (Grounding check)
   │       └─► Retry or Abstain if fail
   │
   ├─► Generate Citations
   │
   └─► Return to User (with sources)
```

---

## Technology Stack

| Category | Choice | Alternatives Rejected |
|----------|--------|----------------------|
| UI | Streamlit | Gradio, React+FastAPI |
| API | FastAPI | Flask, Django |
| RAG Framework | LangChain + LangGraph | LlamaIndex, Haystack |
| Vector Store | FAISS | Chroma, Pinecone |
| Embeddings | all-MiniLM-L6-v2 | OpenAI API, mpnet-base |
| Sparse Retrieval | Rank-BM25 | Elasticsearch, Whoosh |
| Reranker | Cross-Encoder (optional) | LLM-as-reranker, skip |
| LLM | OpenAI API | Ollama, Anthropic |
| Language | Python 3.9+ | None (team strength) |

---

## Trade-off Matrix

### Latency vs Accuracy
| Path | Latency | Accuracy | When Used |
|------|---------|----------|-----------|
| Dense-only | Fast (~500ms) | Good | Speed priority |
| Dense + BM25 | Medium (~700ms) | Better | Default |
| Full (w/ rerank) | Slower (~1.2s) | Best | Quality priority |

**v1 Default:** Dense + BM25 + Reranker (balanced)

### Local vs Cloud
| Component | v1 Choice | Configurable |
|-----------|-----------|--------------|
| Embeddings | Local CPU | N/A |
| Vector Store | FAISS (local) | Chroma, Weaviate |
| LLM | OpenAI (cloud) | → Ollama (local) |
| Session | Memory (local) | SQLite (local) |

**Design:** Cloud-first but configurable to full-local.

---

## Critical Requirements

| Requirement | Implementation |
|-------------|----------------|
| No PostgreSQL | Uses FAISS (library, not DB) |
| No CAG | Standard RAG pipeline used |
| No multi-agent | Single LangGraph workflow |
| No transactions | FAQ-only, documented boundaries |
| Local dev | All components run locally |
| Production quality | Tests, validation, error handling |

---

## Risk Summary

| Risk | Severity | Mitigation |
|------|----------|------------|
| LLM Hallucination | 🔴 Critical | Grounding, citations, abstention |
| Prompt Injection | 🔴 Critical | Input sanitization, validation |
| PII Leakage | 🟠 High | Presidio detection, redaction |
| Latency Degradation | 🟠 High | Streaming, caching, rate limits |
| Retrieval Failure | 🟠 Medium | Hybrid search, fallback broadening |

See `risk-analysis.md` for full register.

---

## Integration Points

### With LLM Provider
```
Banking RAG ──OpenAI API──► OpenAI (GPT-4o-mini)
           │
           └──Ollama API──► Ollama (local models)
```

### With Document Sources
```
Document Store ──Loaders──► PDF/HTML/TXT
             │
             ├─Chunker───► Text chunks
             │
             └─Metadata──► Source, section, date
```

### With Session Storage
```
Conversation ←─Session Memory──► In-Memory (v1)
     │           
     └───────────────► SQLite (v2 option)
```

---

## Scalability Boundaries

| Dimension | v1 Limit | v2 Path |
|-----------|----------|---------|
| Concurrent Users | 1 (local) | Multi-user with auth |
| Document Count | ~10K | Weaviate/Chroma |
| Session Duration | 30 min TTL | Persistent SQLite |
| Embedding Model | CPU | GPU if available |
| Deployment | Local | Docker + Cloud |

---

## Assumptions

1. Banking documents are clean PDF/HTML/TXT (not scanned)
2. User queries are in English
3. Knowledge base fits in <10K documents
4. Single-user local deployment for v1
5. OpenAI API or Ollama available
6. Document updates are batch (not real-time)

---

## Validation 

The architecture satisfies:

- [x] Simple local deployment (no microservices)
- [x] FAISS for vectors (no PostgreSQL)
- [x] Single LangGraph workflow (no multi-agent)
- [x] FAQ-only scope (no transactions)
- [x] Hybrid retrieval (FAISS + BM25)
- [x] Configurable LLM provider
- [x] Security layers included
- [x] Session management
- [x] Source citations
- [x] Risk mitigations documented

---

## Next Steps

1. **Scout Research:** Validate embedding model choices, chunking strategies
2. **Forge Implementation:** Build components per specification
3. **Sentinel Verification:** Test retrieval, generation, grounding

---

## Files Reference

```
/home/hari/Desktop/Banking/
├── architecture-diagram.html      (Interactive diagram)
├── component-specification.md     (Detailed specs)
├── technology-rationale.md        (Tech decisions)
└── risk-analysis.md               (Risk register)
```

To view the architecture diagram:
```bash
xdg-open /home/hari/Desktop/Banking/architecture-diagram.html
```

---

*End of Architecture Design*

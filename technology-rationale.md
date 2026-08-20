# Technology Stack Rationale

**Document:** Banking RAG Chatbot Technology Decisions  
**Version:** 1.0  
**Date:** 2026-08-20  
**Author:** Archer (System Architecture)

---

## Executive Summary

This document provides evidence-based rationale for all technology choices in the Banking RAG Chatbot. Each decision was evaluated against:

1. **Local-first operation** (no PostgreSQL, minimal external dependencies)
2. **Development velocity** (fast iteration, Python-native)
3. **Operational simplicity** (single machine, minimal configuration)
4. **Banking domain fit** (structured documents, FAQ-focused)
5. **Cost efficiency** (open source + pay-as-you-go API options)

---

## 1. Tech Stack Overview

```
┌─────────────────────────────────────────────┐
│              TECHNOLOGY STACK               │
├─────────────────┬───────────────────────────┤
│ UI Layer        │ Streamlit                 │
│ API Layer       │ FastAPI                   │
│ RAG Framework   │ LangChain + LangGraph     │
│ Vector Store    │ FAISS                     │
│ Embedder        │ Sentence-Transformers     │
│ Sparse Retriever│ Rank-BM25                 │
│ Reranker        │ Cross-Encoder (MSMarco)   │
│ LLM Interface   │ OpenAI-Compatible API   │
│ Session Memory    │ In-Memory / SQLite        │
│ Document Store  │ Local filesystem          │
│ Language        │ Python 3.9+               │
└─────────────────┴───────────────────────────┘
```

---

## 2. Decisions with Alternatives

### 2.1 UI Framework: Streamlit

**Decision:** Use Streamlit for the chat interface.

**Alternatives Considered:**

| Option | Pros | Cons |
|--------|------|------|
| **Gradio** | Built-in chat component, easy ML demo | Less control over layout, fewer widgets |
| **Flask/Jinja2** | Full control, production proven | Manual chat UI construction, slower dev |
| **React+FastAPI** | Best UX, scalable | Requires JS build pipeline, complexity |
| **Streamlit** | Python-only, chat built-in, fast | Less customizable, not for production |

**Rationale:**

Streamlit is the optimal choice for a **v1 prototype** because:

1. **Zero JS required:** Pure Python development
2. **Built-in chat:** `st.chat_message()` and `st.chat_input()` perfect for our use case
3. **Session state:** Native session management for conversation history
4. **Fast iteration:** Change code → see result in seconds
5. **Local focus:** Designed for single-user local development

**Trade-offs:**
- Limited customization compared to React
- Higher memory usage than Flask
- Not suitable for multi-user production (v2 consideration)

---

### 2.2 RAG Framework: LangChain + LangGraph

**Decision:** Use LangChain for retrievers/embeddings, LangGraph for workflow.

**Alternatives Considered:**

| Option | Pros | Cons |
|--------|------|------|
| **LlamaIndex** | Native RAG, query engine, better indexing | Single-purpose, learn new API |
| **Haystack** | End-to-end RAG pipeline | Heavyweight, YAML config heavy |
| **Raw Python** | Full control, no deps | Rebuild the wheel, more bugs |
| **LangChain+Graph** | Ecosystem, LangGraph for flow control | Abstraction overhead |

**Rationale:**

1. **Ecosystem:** LangChain has the most integrations for vector stores, loaders, retrievers
2. **LangGraph specifically:**
   - Explicit state machine for the RAG pipeline
   - Conditional edges (router → retriever → validator)
   - Retry loops built-in
   - Clear debugging via graph visualization
3. **Future extensibility:** Easy to add agents later if needed
4. **Banking fit:** Our flow (query → retrieve → assemble → generate) maps well to a graph

**Trade-offs:**
- LangChain can be magical in places (high-level abstractions)
- Import times are slower due to heavy dependency chain

**Mitigation:** Use only specific LangChain modules; write custom retrievers。

---

### 2.3 Vector Store: FAISS

**Decision:** Use FAISS for vector storage.

**Alternatives Considered:**

| Option | Pros | Cons |
|--------|------|------|
| **Chroma** | Easy setup, Python-native | Newer, less mature, future stability |
| **Weaviate** | Hybrid search, GraphQL | Requires separate server, complex |
| **Pinecone** | Managed, fast, hybrid | Cloud-only, paid, external dependency |
| **PostgreSQL + pgvector** | SQL familiarity, ACID | Requires Postgres (v1 constraint: not allowed) |
| **FAISS** | Facebook proven, fast, local files only | No metadata filtering (manage separately) |

**Rationale:**

1. **Constraint satisfaction:** FAISS is a library, not a database. No PostgreSQL required.
2. **Maturity:** Meta/Facebook production proven
3. **Performance:** C++ backend with Python bindings
4. **Flexibility:** Multiple index types (Flat, IVF, HNSW)
5. **Simplicity:** Save index to file, reload from file

**Trade-offs:**
- No built-in metadata filtering (store metadata separately → join at retrieval)
- No transactions (manage index updates carefully)

**Mitigation:** Build metadata-to-FAISS-ID mapping in Python.

---

### 2.4 Embedding Model: all-MiniLM-L6-v2

**Decision:** Use sentence-transformers with MiniLM model.

**Alternatives Considered:**

| Model | Embedding Size | Speed | Quality | Use Case |
|-------|---------------|-------|---------|----------|
| all-MiniLM-L6-v2 | 384 | Fastest | Good | Prototyping |
| all-mpnet-base-v2 | 768 | Medium | Better | Production |
| BAAI/bge-small-en | 512 | Fast | Good | Performance |
| BAAI/bge-base-en | 768 | Medium | Best | Quality |
| E5-base | 768 | Medium | Excellent | Semantic search |
| OpenAI text-embedding-3-small | 1536 | API | Excellent | Cloud-first |

**Rationale:**

For v1:
1. **Local execution:** Runs on CPU, no API costs
2. **Speed:** Fastest model suitable for local use
3. **Size:** 22MB download, reasonable memory
4. **Good enough:** For banking FAQs, sentence-level semantics are sufficient

**Future paths:**
- Upgrade to `bge-base-en` for 10-15% quality bump
- Switch to OpenAI embeddings for larger/dynamic KB

---

### 2.5 Sparse Retriever: Rank-BM25

**Decision:** Use Rank-BM25 for lexical retrieval.

**Alternatives Considered:**

| Option | Pros | Cons |
|--------|------|------|
| **Whoosh** | Pure Python, fast, inverted index | Less active, smaller community |
| **Elasticsearch** | Industry standard, powerful | Requires Java, heavy setup |
| **Skip sparse** | Simpler, faster | Miss keyword matches, acronym searches |
| **Rank-BM25** | Simple, pip install, works well | Single-threaded |

**Rationale:**

Hybrid retrieval (dense + sparse) is important for banking:

1. **Domain terminology:** Account codes, policy names
2. **Acronyms:** "APR", "HELOC", "FDIC" match poorly in embeddings
3. **Exact match:** User asks for exact product names

**Implementation:**
```python
# Combine scores with Reciprocal Rank Fusion
rrf_score = 1.0 / (k + dense_rank) + 1.0 / (k + sparse_rank)
```

**Trade-off:** Memory usage for the inverted index (acceptable for <10K docs).

---

### 2.6 Reranker: Cross-Encoder (MSMarco)

**Decision:** Use a cross-encoder for reranking (v1 optional).

**Alternatives Considered:**

| Option | Pros | Cons |
|--------|------|------|
| **ColBERT** | Better accuracy, token-level | Higher latency, more compute |
| **LLM-as-reranker** | Flexible, powerful | Expensive, slow, API costs |
| **Skip reranking** | Faster, simpler | Lower precision at top-5 |
| **Cross-Encoder** | Best precision/speed tradeoff | Local compute needed |

**Rationale:**

1. **Precision matters:** In banking, wrong info is worse than "I don't know"
2. **Latency acceptable:** ~100ms for cross-encoder on 10 docs
3. **Local execution:** `cross-encoder/ms-marco-MiniLM-L-6-v2` runs on CPU

**Decision:** Include in architecture as optional component. Can be disabled for speed.

---

### 2.7 LLM Interface: OpenAI-Compatible

**Decision:** Support any OpenAI-compatible API endpoint.

**Alternatives Considered:**

| Option | Pros | Cons |
|--------|------|------|
| **OpenAI only** | Best models, reliable | API costs, rate limits, internet required |
| **Ollama only** | Free, local, offline | Lower quality, requires GPU for speed |
| **Anthropic only** | Excellent quality | API-only, higher cost |
| **OpenAI-compatible** | Flexible, interchangeable | Lowest common denominator features |

**Rationale:**

The best design is **provider-agnostic** but **OpenAI-compatible**:

1. **Standard interface:** `openai` library is the de-facto standard
2. **Ollama compatibility:** Ollama provides OpenAI-compatible API
3. **Future swap:** Easy to switch providers by changing base_url
4. **Fallback:** Can use Ollama locally if OpenAI is down

**Configuration:**
```python
# Primary: OpenAI
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

# Fallback: Ollama
client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)
```

---

### 2.8 Session Memory: In-Memory

**Decision:** Use in-memory dict for session state (v1).

**Alternatives Considered:**

| Option | Pros | Cons |
|--------|------|------|
| **SQLite** | Persistent, SQL access | File locking, cleanup needed |
| **Redis** | Fast, TTL built-in | Requires server, external dep |
| **In-memory** | Simplest, fastest, easiest | Lost on restart, single-process |

**Rationale:**

v1 is a **single-user local prototype**:

1. Simplicity wins → in-memory dict
2. Loss on restart is acceptable
3. Can upgrade to SQLite for v2

**Future path:** SQLite with TTL for session expiration.

---

### 2.9 Document Loader: PyPDF2 + BeautifulSoup

**Decision:** Use format-specific loaders.

**Alternatives Considered:**

| Option | Best For | Implementation |
|--------|----------|----------------|
| **PyPDF2** | PDFs | Standard, PDFMiner fallback |
| **pdfplumber** | Tables in PDFs | Better layout preservation |
| **BeautifulSoup** | HTML | `lxml` parser |
| **python-docx** | Word docs | Simple, keeps structure |
| **Unstructured.io** | All formats | Heavy deps, cloud features |
| **LangChain loaders** | Consistency | Abstractions, proven |

**Rationale:**

Use **LangChain loaders** (which wrap the above):

1. Unified interface: `load()` method
2. Metadata extraction built-in
3. Error handling included
4. Future format additions are trivial

**Supported v1 formats:** PDF, HTML, TXT

---

## 3. Rejected Technologies (and Why)

| Technology | Why Rejected | Alternative |
|------------|--------------|-------------|
| PostgreSQL + pgvector | v1 constraint: no Postgres | FAISS |
| Pinecone/Weaviate (cloud) | External dependency, cost | FAISS local |
| CAG (Cache-Augmented Generation) | v1 constraint: not allowed | Standard RAG |
| Autonomous agents | v1 constraint: too complex | Static LangGraph |
| Multi-agent system | Overkill for FAQ chatbot | Single pipeline |
| llamafile/llama.cpp | Good, but Ollama preferred | Ollama |
| Commercial LLM APIs only | Vendor lock-in | Configurable provider |
| Microservices | Over-engineered for v1 | Monolithic Python |
| Docker (v1) | Adds complexity | Direct Python execution |

---

## 4. Technology Maturity Assessment

| Component | Maturity | Risk | Mitigation |
|-----------|----------|------|------------|
| Streamlit | ⭐⭐⭐⭐ | Low | Swap to React later |
| FastAPI | ⭐⭐⭐⭐⭐ | None | Industry standard |
| FAISS | ⭐⭐⭐⭐⭐ | None | Meta production |
| LangChain | ⭐⭐⭐⭐ | Low | Use subset of features |
| Rank-BM25 | ⭐⭐⭐⭐ | Low | Simple algorithm |
| Sentence-Transformers | ⭐⭐⭐⭐⭐ | None | Well maintained |
| Ollama | ⭐⭐⭐ | Medium | Fallback to OpenAI |
| OpenAI API | ⭐⭐⭐⭐⭐ | None | Industry standard |

---

## 5. Dependencies Summary

### Core Dependencies
```
fastapi>=0.110
uvicorn>=0.27
langchain>=0.1.0
langchain-community>=0.0.20
langchain-openai>=0.0.5
langgraph>=0.0.20
faiss-cpu>=1.7.4
sentence-transformers>=2.3.0
rank-bm25>=0.2.2
pypdf2>=3.0.0
beautifulsoup4>=4.12.0
streamlit>=1.31.0
pydantic>=2.5
pydantic-settings>=2.1
python-dotenv>=1.0
```

### Optional Dependencies
```
presidio-analyzer>=2.2    # PII detection
ollama>=0.1.0             # Local LLM
```

**Total venv size:** ~1.5GB (including model downloads)

---

## 6. Key Architectural Principles

1. **Local-first:** Everything should work offline with Ollama
2. **Swap without rewrite:** LLM provider, embedding model, vector store
3. **Minimal moving parts:** Fewer external services = fewer failures
4. **Python-native:** No language polyglots for v1
5. **Readable code:** Avoid over-abstraction

---

## 7. Future Technology Evolution

| v1 (Current) | v2+ (Potential) |
|--------------|-----------------|
| FAISS local | Weaviate or Chroma |
| In-memory sessions | SQLite with TTL |
| CPU-only embeddings | GPU (CUDA) if available |
| OpenAI API | Multi-provider fallback |
| Monolithic | Containerized (Docker) |
| File-based index | Re-indexing pipeline |
| Static configuration | Dynamic UI-based config |
| Single user | Multi-user with auth |

---

## Appendix: Decision Justification

### Why not LlamaIndex?

LlamaIndex is excellent for document-centric applications. We chose LangChain because:

1. LangGraph provides explicit control over the flow (important for banking compliance)
2. More retriever options in LangChain ecosystem
3. Banking FAQ is query-centric, not document-centric

Both are good choices; this is a marginal decision.

### Why not Haystack?

Haystack's pipeline abstraction is great, but:

1. YAML/JSON config is harder to debug than Python
2. Less community content than LangChain
3. Smaller ecosystem

### Why not Langserve?

Langserve is deprecated in favor of LangGraph's deployment options. We use FastAPI directly for explicit control.

---

*[End of Technology Stack Rationale]*

# Banking RAG Chatbot: Technology Stack Finalization

**Version:** 1.0  
**Status:** Final  
**Date:** 2026-08-20  
**Validated Against:** Scout research findings

---

## Executive Summary

This document finalizes the technology stack for the Banking RAG Chatbot, incorporating research-validated decisions from the completed scout tasks.

### Final Stack Overview

| Layer | Technology | Version | License |
|-------|-----------|---------|---------|
| **Embeddings** | BAAI/bge-small-en | v1.5 | Apache 2.0 |
| **Vector Store** | FAISS (CPU) | 1.7.4+ | MIT |
| **Sparse Retrieval** | rank-bm25 | 0.1.3 | MIT |
| **LLM Framework** | LangChain + LangGraph | 0.1.x | MIT |
| **LLM Provider** | OpenAI API / Ollama | Latest | Commercial/Apache 2.0 |
| **UI** | Streamlit | 1.28+ | Apache 2.0 |
| **API** | FastAPI | 0.104+ | MIT |
| **Server** | Uvicorn | 0.24+ | BSD |
| **Validation** | Pydantic | 2.0+ | MIT |

---

## Component-by-Component Decisions

### 1. Embeddings: BAAI/bge-small-en

**Selected:** `BAAI/bge-small-en` via sentence-transformers

**Specs:**
- Dimensions: 384
- Parameters: 33M
- Seq length: 512 tokens
- Normalized: Yes (cosine similarity)

**Why This Model:**

| Criterion | Score | Evidence |
|-----------|-------|----------|
| Banking domain accuracy | ★★★★☆ | Fine-tuned for retrieval tasks |
| Local execution | ★★★★★ | CPU inference, no API dependency |
| License | ★★★★★ | Apache 2.0 (commercial OK) |
| Model size | ★★★☆☆ | 33M params (bigger than MiniLM) |
| Research validation | ★★★★★ | Scout task t_698a9758 |

**Alternatives Considered:**

| Model | Dimensions | Params | Status | Reason |
|-------|------------|--------|--------|--------|
| all-MiniLM-L6-v2 | 384 | 22M | Rejected | Inferior retrieval per research |
| BAAI/bge-base-en | 768 | 110M | Alternative | Higher quality, slower |
| Qwen3-Embedding-8B | 4096 | 8B | Future | Best quality, needs GPU |
| text-embedding-3-large | 3072 | - | Rejected | Requires API, no local option |
| Voyage-3-large | 1024 | - | Rejected | API-only, expensive |

**Installation:**
```bash
pip install sentence-transformers
```

**Usage:**
```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('BAAI/bge-small-en')
embeddings = model.encode(texts, normalize_embeddings=True)
```

**Dimensions:** 384 (matches FAISS configuration)

---

### 2. Vector Store: FAISS

**Selected:** `faiss-cpu` (IndexFlatIP)

**Why FAISS:**
- File-based (no database server)
- Exact search with IndexFlatIP
- Suitable for <10K documents
- Optimized for 384-dim vectors
- MIT licensed

**Index Configuration:**

| Index Type | Purpose | Trade-offs |
|------------|---------|------------|
| IndexFlatIP | v1 default | Exact search, O(N) |
| IndexIVFFlat | >50K docs | Faster, approximate |
| IndexHNSW | >100K docs | Fast, high memory |

**Installation:**
```bash
pip install faiss-cpu
```

**Python Usage:**
```python
import faiss

dimension = 384
index = faiss.IndexFlatIP(dimension)
index = faiss.IndexIDMap(index)  # For ID mapping

# Add vectors
index.add_with_ids(embeddings, ids)

# Search
scores, ids = index.search(query_vector, k=5)
```

---

### 3. Sparse Retrieval: rank-bm25

**Selected:** `rank-bm25`

**Why rank-bm25:**
- Pure Python implementation
- No external dependencies
- Fast for small-medium corpora
- MIT licensed

**Installation:**
```bash
pip install rank-bm25
```

**Python Usage:**
```python
from rank_bm25 import BM25Okapi

# Tokenize corpus
tokenized_corpus = [doc.split() for doc in corpus]
bm25 = BM25Okapi(tokenized_corpus)

# Query
tokenized_query = query.split()
doc_scores = bm25.get_scores(tokenized_query)
top_n = bm25.get_top_n(tokenized_query, corpus, n=5)
```

---

### 4. RAG Framework: LangChain + LangGraph

**Selected:** `langchain` + `langgraph`

**Why LangChain/LangGraph:**
- State management for complex workflows
- Visualization of graph execution
- Good integration with FAISS
- Active community

**Installation:**
```bash
pip install langchain langgraph
pip install langchain-openai
pip install langchain-community
```

**Key Components:**
```python
from langgraph.graph import StateGraph, END
from typing import TypedDict

# Define state
class RAGState(TypedDict):
    query: str
    chunks: list
    response: str

# Build graph
builder = StateGraph(RAGState)
builder.add_node("retrieve", retrieve_fn)
builder.add_node("generate", generate_fn)
builder.add_edge("retrieve", "generate")
builder.add_edge("generate", END)

graph = builder.compile()
```

---

### 5. LLM Provider: OpenAI API

**Selected:** `openai` Python SDK with GPT-4o-mini default

**Configuration:**
```yaml
llm:
  provider: "openai"      # openai | ollama
  model: "gpt-4o-mini"
  temperature: 0.1
  max_tokens: 500
  timeout: 30
```

**Why OpenAI:**
- Best cost/quality for banking content
- Fast response times
- Streaming support
- Configurable fallback to local

**Alternatives:**

| Provider | Model | When to Use | Config |
|----------|-------|-------------|--------|
| OpenAI | GPT-4o-mini | Default | provider=openai |
| Ollama | llama-3.1 | Offline | provider=ollama |
| Ollama | mistral | Offline | provider=ollama |

**Installation:**
```bash
pip install openai
```

**Usage:**
```python
from openai import OpenAI

client = OpenAI()

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": question}
    ],
    temperature=0.1
)
```

---

### 6. UI: Streamlit

**Selected:** `streamlit` + `streamlit-chat`

**Why Streamlit:**
- Fastest to implement for v1
- Built-in chat components
- No frontend framework needed
- Handles async by default

**Installation:**
```bash
pip install streamlit
```

**Configuration:**
```yaml
ui:
  port: 8501
  theme: "light"
  page_title: "Banking FAQ Assistant"
  show_source_citations: true
```

**Usage:**
```python
import streamlit as st

st.title("Banking FAQ Assistant")

# Chat interface
if prompt := st.chat_input("Ask about banking policies..."):
    with st.chat_message("user"):
        st.write(prompt)
    
    response = rag_chain.invoke(prompt)
    
    with st.chat_message("assistant"):
        st.write(response["answer"])
        with st.expander("Sources"):
            for cite in response["citations"]:
                st.caption(cite)
```

---

### 7. API: FastAPI

**Selected:** `fastapi` + `uvicorn`

**Why FastAPI:**
- Type-safe with Pydantic
- Auto-generated OpenAPI docs
- Async/await support
- Fast performance

**Installation:**
```bash
pip install fastapi uvicorn
```

**Usage:**
```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None

class ChatResponse(BaseModel):
    response: str
    citations: list[Citation]

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    # RAG pipeline execution
    return {"response": "...", "citations": []}
```

---

### 8. Document Processing

**Chunking:** RecursiveCharacterTextSplitter (from LangChain)
```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=512,  # tokens
    chunk_overlap=50,
    separators=["\n\n", "\n", ". ", "? ", "! ", " ", ""]
)
```

**Document Loaders:**

| Format | Library | PyPI |
|--------|---------|------|
| PDF | pypdfium2 / pdfplumber | `pypdfium2` |
| DOCX | python-docx | `python-docx` |
| HTML | BeautifulSoup4 | `beautifulsoup4` |
| TXT | Built-in | - |

**PII Detection:** Microsoft Presidio
```bash
pip install presidio-analyzer presidio-anonymizer
```

---

## Requirements.txt

```
# Core
python>=3.9
pydantic>=2.0.0
python-dotenv>=1.0.0
pyyaml>=6.0

# Embeddings
sentence-transformers>=2.2.0

# Vector Store
faiss-cpu>=1.7.4

# Sparse Retrieval
rank-bm25>=0.1.3

# RAG Framework
langchain>=0.1.0
langgraph>=0.0.20
langchain-openai>=0.0.5

# LLM
openai>=1.0.0

# Document Processing
pypdfium2>=4.0.0
python-docx>=1.1.0
beautifulsoup4>=4.12.0

# Security
presidio-analyzer>=2.2.0
presidio-anonymizer>=2.2.0

# API
fastapi>=0.104.0
uvicorn>=0.24.0

# UI
streamlit>=1.28.0

# Utilities
tiktoken>=0.5.0
numpy>=1.24.0
tqdm>=4.66.0
```

---

## Development Dependencies

```
# Testing
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
pytest-mock>=3.12.0

# Code Quality
black>=23.0.0
ruff>=0.1.0
mypy>=1.7.0

# Linting
pre-commit>=3.5.0

# Documentation
mkdocs>=1.5.0
mkdocs-material>=9.4.0
```

---

## Architecture Decision Records

### ADR-TS-001: Embedding Model → BAAI/bge-small-en

**Context:** Multiple embedding models evaluated (Gemini, Qwen3, Voyage, OpenAI, BGE).

**Decision:** Use BAAI/bge-small-en

**Rationale:**
1. Research validates superior retrieval performance
2. 384-dim compatible with FAISS
3. Apache 2.0 licensed
4. Local execution (no API dependency)
5. Optimal banking domain performance

**Consequences:**
- (+) Better retrieval accuracy per research
- (+) No API costs
- (+) Works offline
- (-) 33M params vs 22M (acceptable)

---

### ADR-TS-002: Vector Store → FAISS

**Context:** Requirement to avoid PostgreSQL.

**Decision:** Use FAISS IndexFlatIP

**Rationale:**
1. File-based library (not database)
2. Exact search with no approximation loss
3. Suitable for <10K documents
4. MIT licensed

**Consequences:**
- (+) No database server
- (+) Exact search
- (-) Linear search time (acceptable for scale)

---

### ADR-TS-003: RAG Framework → LangChain + LangGraph

**Context:** Need state management for multi-step workflow.

**Decision:** LangChain with LangGraph

**Rationale:**
1. LangGraph handles state transitions
2. Good documentation and community
3. Native FAISS integration
4. Manifested state machines

**Consequences:**
- (+) Visualize execution graph
- (+) State persistence
- (-) Dependency on LangChain ecosystem

---

### ADR-TS-004: UI → Streamlit

**Context:** Need rapid v1 implementation.

**Decision:** Streamlit over Gradio/React

**Rationale:**
1. Fastest to implement
2. Built-in chat components
3. No JavaScript knowledge required
4. Handles async automatically

**Consequences:**
- (+) Days vs weeks implementation
- (+) Python-only
- (-) Less customizable than React

---

### ADR-TS-005: LLM → OpenAI GPT-4o-mini

**Context:** Balance of quality, cost, and configurability.

**Decision:** GPT-4o-mini default, Ollama configurable

**Rationale:**
1. Best quality/cost ratio
2. Streaming support
3. Easy fallback to local
4. Proper tokenizer

**Consequences:**
- (+) High quality responses
- (+) Low latency
- (-) Requires internet (mitigated)

---

## Migration Paths

### v1 → v2+ (Future Considerations)

| Component | v1 | v2 Potential |
|-----------|-----|--------------|
| Embeddings | bge-small-en | bge-base-en (768d) or Qwen3 (4096d) |
| Vector Store | FAISS FlatIP | FAISS IVFFlat or Weaviate |
| Session | In-memory | SQLite or Redis |
| UI | Streamlit | React + Next.js |
| Deployment | Local | Docker + Cloud |

---

## License Compliance

| Package | License | Commercial Use |
|---------|---------|----------------|
| sentence-transformers | Apache 2.0 | ✅ |
| FAISS | MIT | ✅ |
| rank-bm25 | MIT | ✅ |
| LangChain | MIT | ✅ |
| OpenAI API | Commercial | ✅ |
| Streamlit | Apache 2.0 | ✅ |
| FastAPI | MIT | ✅ |

All dependencies are permissively licensed for commercial use.

---

## Performance Targets

| Component | Metric | Target |
|-----------|--------|--------|
| Embeddings | Throughput | >100 chunks/s |
| FAISS | Query latency | <50ms (10K docs) |
| BM25 | Query latency | <100ms (10K docs) |
| RRF Fusion | Overhead | <20ms |
| LLM | Response time | <1s (streaming) |
| UI | Render time | <100ms |

---

*Technology Stack - Finalized*

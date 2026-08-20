# Banking RAG Chatbot - Sprint-Ready Task Outline

## Overview

This document provides a prioritized, sprint-ready task outline for implementing the Banking RAG Chatbot, following TDD principles with clear acceptance criteria.

---

## Sprint 0: Foundation (Week 1)

### Priority: P0 - Blocker

### Objective: Establish core infrastructure and configuration management

---

### Task 0.1: Configuration Management System
**Status**: Ready to implement  
**Estimate**: 1 day  
**Assignee**: Forge  

#### Deliverables
- `config/__init__.py` - Configuration package initialization
- `config/loader.py` - YAML config loader with validation
- `config/schema.py` - Pydantic schemas for configuration
- `config/__init__.env` - Example environment file

#### Acceptance Criteria
- [ ] Can load `config.yaml` from project root
- [ ] Can override values from environment variables
- [ ] Validates required fields on load
- [ ] Provides type-safe access to configuration
- [ ] Gracefully handles missing optional fields

#### Technical Notes
- Use Pydantic for schema validation
- Support `.env` file loading
- Implement fallback chain (config.yaml → .env → defaults)

---

### Task 0.2: Language Model Interface
**Status**: Ready to implement  
**Estimate**: 1-2 days  
**Assignee**: Forge  

#### Deliverables
- `llm/__init__.py` - LLM interface package
- `llm/client.py` - OpenAI-compatible client
- `llm/providers.py` - Provider-specific implementations
- `tests/test_llm.py` - Unit tests

#### Acceptance Criteria
- [ ] Can initialize OpenAI-compatible client
- [ ] Can generate text with temperature control
- [ ] Can chat with message history
- [ ] Handles API errors gracefully
- [ ] Supports streaming mode (optional)

#### Provider Options
1. **OpenAI** (recommended for v1) - `GPT-4`, `GPT-3.5-turbo`
2. **Local** - llama.cpp (GGUF), Ollama
3. **Compatible** - Any OpenAI API-compatible endpoint

#### Technical Notes
- Use `openai` Python library
-抽象出通用接口: `generate()`, `chat()`
- Implement retry logic with exponential backoff

---

### Task 0.3: Basic FAISS Index (In-Memory)
**Status**: Ready to implement  
**Estimate**: 1 day  
**Assignee**: Forge  

#### Deliverables
- `faiss/__init__.py` - FAISS package
- `faiss/index.py` - Basic index creation and search
- `tests/test_faiss_basic.py` - Basic operation tests

#### Acceptance Criteria
- [ ] Creates FAISS index from embeddings
- [ ] Performs K-nearest neighbor search
- [ ] Returns distance scores
- [ ] Handles empty index gracefully

#### Technical Notes
- Start with `IndexFlatIP` (inner product)
- Use numpy arrays for embeddings
- No persistence yet (Sprint 1)

---

### Task 0.4: Simple Document Loader (PDF)
**Status**: Ready to implement  
**Estimate**: 1 day  
**Assignee**: Forge  

#### Deliverables
- `loaders/__init__.py` - Document loaders package
- `loaders/pdf.py` - PDF loader using PyPDFium2
- `tests/test_loaders.py` - Loader tests

#### Acceptance Criteria
- [ ] Loads PDF files from path
- [ ] Extracts text with page numbers
- [ ] Preserves document metadata
- [ ] Handles common errors (corrupt PDFs)

#### Technical Notes
- Use `pypdfium2` for faster PDF processing
- Extract each page as separate document
- Track source and page in metadata

---

### Sprint 0 Summary

| Task | Priority | Duration | Status |
|------|----------|----------|--------|
| Configuration System | P0 | 1 day | Ready |
| LLM Interface | P0 | 2 days | Ready |
| FAISS Basic Index | P0 | 1 day | Ready |
| Simple PDF Loader | P1 | 1 day | Ready |

**Total**: 5 days  
**Blockers**: None  
**Parallelizable**: Yes

---

## Sprint 1: Core RAG Pipeline (Weeks 1-2)

### Priority: P0 - Blocker

### Objective: Implement complete document ingestion and embedding pipeline

---

### Task 1.1: Extended Document Loaders
**Status**: Ready to implement  
**Estimate**: 1.5 days  
**Assignee**: Forge  

#### Deliverables
- `loaders/docx.py` - DOCX loader
- `loaders/txt.py` - TXT loader
- `loaders/html.py` - HTML loader (optional)
- `loaders/base.py` - Base loader interface

#### Acceptance Criteria
- [ ] Can load DOCX files
- [ ] Can load plain text files
- [ ] All loaders return Document objects
- [ ] Handles empty files gracefully
- [ ] Supports file URL inputs

#### Acceptance Tests
```python
def test_load_pdf():
    docs = load_pdf("tests/data/banking_policy.pdf")
    assert len(docs) == 1
    assert docs[0].metadata.source == "banking_policy.pdf"
    assert "banking" in docs[0].content.lower()

def test_load_docx():
    docs = load_docx("tests/data/product_details.docx")
    assert len(docs) == 1
```

---

### Task 1.2: Document Chunking System
**Status**: Ready to implement  
**Estimate**: 1.5 days  
**Assignee**: Forge  

#### Deliverables
- `chunking/__init__.py` - Chunking package
- `chunking/base.py` - Base chunker interface
- `chunking/fixed_size.py` - Fixed-size chunker
- `chunking/recursive.py` - Recursive chunker
- `tests/test_chunking.py` - Chunking tests

#### Acceptance Criteria
- [ ] Splits documents into chunks
- [ ] Configurable chunk size and overlap
- [ ] Preserves metadata
- [ ] Generates unique chunk IDs
- [ ] Respects semantic boundaries (sentences)

#### Chunking Strategy (Recommended)
- **Initial**: RecursiveCharacterTextSplitter
- **Chunk size**: 512 tokens (≈2048 characters)
- **Overlap**: 50 tokens
- **Semantics**: Preserve sentence boundaries

#### Acceptance Tests
```python
def test_chunking_respects_boundaries():
    chunker = RecursiveChunker(chunk_size=512, overlap=50)
    chunks = chunker.split_document(document)
    for chunk in chunks:
        assert chunk.content.endswith(('.', '!', '?')) or chunk == chunks[-1]

def test_chunk_metadata_preserved():
    assert all(c.metadata.source == document.metadata.source for c in chunks)
```

---

### Task 1.3: Embedding Generation Pipeline
**Status**: Ready to implement  
**Estimate**: 2 days  
**Assignee**: Forge  

#### Deliverables
- `embeddings/__init__.py` - Embeddings package
- `embeddings/generator.py` - Embedding generator
- `embeddings/embeddings.csv` (sample) - Expected format

#### Acceptance Criteria
- [ ] Generates embeddings for batch of chunks
- [ ] Handles rate limiting gracefully
- [ ] Caches embeddings (optional, for v1)
- [ ] Tracks embedding dimensions
- [ ] Maps chunks to embeddings

#### Configuration
```yaml
embeddings:
  provider: openai
  model: text-embedding-3-small
  dimensions: 1536
  batch_size: 100
  timeout: 60
```

#### Acceptance Tests
```python
def test_embedding_dimensions():
    generator = EmbeddingGenerator("text-embedding-3-small")
    embeddings = generator.generate(["test chunk"])
    assert len(embeddings[0]) == 1536

def test_batch_embedding():
    chunks = [f"chunk {i}" for i in range(100)]
    embeddings = generator.generate(chunks)
    assert len(embeddings) == 100
```

---

### Task 1.4: FAISS Index with Persistence
**Status**: Ready to implement  
**Estimate**: 1.5 days  
**Assignee**: Forge  

#### Deliverables
- `faiss/persistence.py` - Index persistence
- `faiss/metadata.py` - Metadata mapping
- `faiss/index.py` - Updated with load/save

#### Acceptance Criteria
- [ ] Saves FAISS index to disk
- [ ] Saves metadata mapping to disk
- [ ] Loads saved index and metadata
- [ ] Maintains chunk-to-vector mapping
- [ ] Handles missing files gracefully

#### File Structure
```
data/
├── index/
│   ├── faiss_indexflatip.index
│   └── metadata.json
└── chunks/
    └── chunk_001.json
```

#### Acceptance Tests
```python
def test_index_persistence():
    index = create_index(embeddings, chunks)
    save_index(index, "data/index")
    
    loaded = load_index("data/index")
    assert len(loaded) == len(index)

def test_metadata_mapping():
    index = create_index(embeddings, chunks)
    save_index(index, "data/index", chunks)
    
    loaded = load_index("data/index", "data/metadata.json")
    chunk_id = loaded.find_chunk_id(vector)
    assert chunk_id == chunks[0].chunk_id
```

---

### Task 1.5: Basic Retrieval Engine
**Status**: Ready to implement  
**Estimate**: 1 day  
**Assignee**: Forge  

#### Deliverables
- `retrieval/__init__.py` - Retrieval package
- `retrieval/basic.py` - Basic retrieval implementation
- `retrieval/base.py` - Base retriever interface
- `tests/test_retrieval.py` - Retrieval tests

#### Acceptance Criteria
- [ ] Embeds query and searches index
- [ ] Returns top-k results with scores
- [ ] Handles metadata filtering
- [ ] Applies score threshold filtering
- [ ] Returns chunk metadata

#### Interface
```python
class BaseRetriever(ABC):
    @abstractmethod
    def retrieve(self, query: str, k: int = 5) -> List[RetrievedChunk]:
        ...
```

#### Acceptance Tests
```python
def test_semantic_retrieval():
    chunks = chunk_documents(documents)
    index = create_faiss_index(chunks)
    retriever = BasicRetriever(index)
    
    results = retriever.retrieve("What is the interest rate?", k=3)
    assert len(results) == 3
    assert all(r.score > 0.5 for r in results)  # Reasonable threshold
```

---

### Sprint 1 Summary

| Task | Priority | Duration | Status |
|------|----------|----------|--------|
| Extended Document Loaders | P0 | 1.5 days | Ready |
| Document Chunking System | P0 | 1.5 days | Ready |
| Embedding Generation Pipeline | P0 | 2 days | Ready |
| FAISS Index with Persistence | P0 | 1.5 days | Ready |
| Basic Retrieval Engine | P0 | 1 day | Ready |

**Total**: 7.5 days  
**Blockers**: None  
**Parallelizable**: Yes

---

## Sprint 2: Workflow & Generation (Weeks 2-3)

### Priority: P0 - Blocker

### Objective: Implement LangGraph workflow and grounded generation

---

### Task 2.1: LangGraph Workflow Setup
**Status**: Ready to implement  
**Estimate**: 2 days  
**Assignee**: Forge  

#### Deliverables
- `workflow/__init__.py` - Workflow package
- `workflow/state.py` - RAGState TypedDict
- `workflow/graph.py` - LangGraph definition
- `workflow/nodes.py` - Node functions
- `tests/test_workflow.py` - Workflow tests

#### Acceptance Criteria
- [ ] Defines RAGState with all required fields
- [ ] Creates LangGraph with proper nodes and edges
- [ ] Handles parsing → retrieval → generation flow
- [ ] Manages state transitions correctly

#### State Schema
```python
class RAGState(TypedDict):
    query: str
    chat_history: List[ChatMessage]
    chunks: List[RetrievedChunk]
    response: str
    citations: List[Citation]
    confidence: float
    metadata: dict
```

#### Acceptance Tests
```python
def test_workflow_state_transitions():
    initial_state = RAGState(query="What is the interest rate?")
    
    # Parse query
    result = parse_query(initial_state)
    assert "intent" in result
    
    # Retrieval
    result = retrieval(result)
    assert len(result["chunks"]) > 0
```

---

### Task 2.2: Grounded Generation
**Status**: Ready to implement  
**Estimate**: 2 days  
**Assignee**: Forge  

#### Deliverables
- `generation/__init__.py` - Generation package
- `generation/prompts.py` - Prompt templates
- `generation/generator.py` - Main generation logic
- `tests/test_generation.py` - Generation tests

#### Acceptance Criteria
- [ ] Assembles context-aware prompt
- [ ] Generates response with citations
- [ ] Calculates confidence score
- [ ] Abstains when confidence is low
- [ ] Formats response with citations

#### Prompt Template
```
You are a helpful banking assistant. Use the following context to answer the question.

Context:
{context}

Question:
{query}

Instructions:
1. Answer based ONLY on the provided context
2. Include citations in [1], [2] format
3. If context is insufficient, say "I don't know"
4. Be concise and accurate

Answer:
```

#### Acceptance Tests
```python
def test_citation_extraction():
    response = "The interest rate is 5% [1]. For loans, see [2]."
    citations = extract_citations(response)
    assert citations == ["[1]", "[2]"]

def test_abstention_logic():
    chunks = [RetrievedChunk(content="Unrelated text", score=0.1)]
    response, confidence = generate_answer("How do I open an account?", chunks)
    assert response == "I don't know"
    assert confidence < 0.5
```

---

### Task 2.3: Session Management
**Status**: Ready to implement  
**Estimate**: 1 day  
**Assignee**: Forge  

#### Deliverables
- `sessions/__init__.py` - Session package
- `sessions/store.py` - In-memory session store
- `sessions/manager.py` - Session manager
- `tests/test_sessions.py` - Session tests

#### Acceptance Criteria
- [ ] Creates new sessions with unique IDs
- [ ] Stores and retrieves chat history
- [ ] Manages context window (max tokens)
- [ ] Supports session reset
- [ ] Handles concurrent sessions

#### Acceptance Tests
```python
def test_session_create_and_add():
    store = InMemorySessionStore()
    session_id = store.create_session()
    
    store.add_message(session_id, ChatMessage(role="user", content="Hello"))
    history = store.get_history(session_id)
    assert len(history) == 1

def test_context_window():
    store = InMemorySessionStore(max_tokens=2048)
    # Add messages until limit exceeded
    # Verify oldest messages are removed
```

---

### Task 2.4: End-to-End Query Flow
**Status**: Ready to implement  
**Estimate**: 1.5 days  
**Assignee**: Forge  

#### Deliverables
- `app.py` - Main application entry point
- `tests/test_e2e_query.py` - End-to-end tests

#### Acceptance Criteria
- [ ] Accepts user query
- [ ] Processes through full RAG pipeline
- [ ] Returns response with citations
- [ ] Handles errors gracefully
- [ ] Logs the request

#### Acceptance Tests
```python
def test_end_to_end_query():
    app = BankingRAGApp()
    
    response = app.query("What is the interest rate for savings accounts?")
    
    assert response.text is not None
    assert len(response.citations) > 0
    assert isinstance(response.confidence, float)
```

---

### Sprint 2 Summary

| Task | Priority | Duration | Status |
|------|----------|----------|--------|
| LangGraph Workflow Setup | P0 | 2 days | Ready |
| Grounded Generation | P0 | 2 days | Ready |
| Session Management | P1 | 1 day | Ready |
| End-to-End Query Flow | P0 | 1.5 days | Ready |

**Total**: 6.5 days  
**Blockers**: None  
**Parallelizable**: Yes

---

## Sprint 3: Enhancement & UI (Weeks 3-4)

### Priority: P1 - Enhancement

### Objective: Add reranking, UI, and polish

---

### Task 3.1: Streamlit UI
**Status**: Ready to implement  
**Estimate**: 2 days  
**Assignee**: Forge  

#### Deliverables
- `ui/__init__.py` - UI package
- `ui/app.py` - Streamlit main application
- `ui/components.py` - Reusable UI components
- `requirements-ui.txt` - UI dependencies

#### Acceptance Criteria
- [ ] Chat interface with message history
- [ ] Displays citations
- [ ] Shows confidence score
- [ ] Handles user input
- [ ] Session management UI

#### UI Components
- Chat input area
- Message display area
- Source citations panel
- Session sidebar
- Settings modal

#### Acceptance Tests
```python
# Manual UI test checklist
- [ ] User can send message
- [ ] Response displays with citations
- [ ] Confidence score shows
- [ ] Previous messages persist in session
- [ ] Can start new session
```

---

### Task 3.2: Reranking Implementation
**Status**: Ready to implement  
**Estimate**: 2 days  
**Assignee**: Forge  

#### Deliverables
- `rerank/__init__.py` - Reranking package
- `rerank/cross_encoder.py` - Cross-encoder reranker
- `rerank/hybrid.py` - Hybrid retrieval (BM25)
- `tests/test_rerank.py` - Reranking tests

#### Acceptance Criteria
- [ ] Reranks retrieved chunks
- [ ] Improves retrieval quality
- [ ] Handles both cross-encoder and hybrid
- [ ] Configurable reranking strategy

#### Acceptance Tests
```python
def test_reranking_improves_quality():
    chunks = initial_retrieve(query, k=20)
    reranked = cross_encoder_rerank(query, chunks)
    
    # Verify top chunks are more relevant
    assert reranked[0].score > chunks[0].score
```

---

### Task 3.3: Error Handling & Validation
**Status**: Ready to implement  
**Estimate**: 1 day  
**Assignee**: Forge  

#### Deliverables
- `errors.py` - Custom exception types
- `validators.py` - Input validation functions
- `tests/test_validation.py` - Validation tests

#### Acceptance Criteria
- [ ] Validates query length
- [ ] Handles API timeouts
- [ ] Provides meaningful error messages
- [ ] Logs errors appropriately
- [ ] Graceful degradation

---

### Task 3.4: Performance Optimization
**Status**: Ready to implement  
**Estimate**: 1 day  
**Assignee**: Forge  

#### Deliverables
- `performance/__init__.py` - Performance module
- `performance/metrics.py` - Metrics collection
- `docs/performance.md` - Performance documentation

#### Acceptance Criteria
- [ ] Query to response: < 5 seconds
- [ ] Document ingestion: < 10 min for 100-page PDF
- [ ] Index load time: < 5 seconds
- [ ] Memory usage logged

#### Acceptance Tests
```python
def test_query_latency():
    app = BankingRAGApp()
    
    with Timer() as timer:
        response = app.query("Test query")
    
    assert timer.elapsed < 5.0  # seconds
```

---

### Sprint 3 Summary

| Task | Priority | Duration | Status |
|------|----------|----------|--------|
| Streamlit UI | P1 | 2 days | Ready |
| Reranking | P1 | 2 days | Ready |
| Error Handling | P2 | 1 day | Ready |
| Performance Optimization | P2 | 1 day | Ready |

**Total**: 6 days  
**Blockers**: None  
**Parallelizable**: Yes

---

## Sprint 4: Hardening & Documentation (Week 4-5)

### Priority: P1 - Enhancement

### Objective: Testing, monitoring, and documentation

---

### Task 4.1: Test Suite Expansion
**Status**: Ready to implement  
**Estimate**: 2 days  
**Assignee**: Sentinel (or Forge)  

#### Deliverables
- `tests/integration/` - Integration tests
- `tests/acceptance/` - Acceptance tests
- `tests/test_dataset.csv` - Test query dataset
- `Makefile` or `pyproject.toml` test scripts

#### Acceptance Criteria
- [ ] 80%+ code coverage
- [ ] Integration tests for full pipeline
- [ ] Acceptance tests for user scenarios
- [ ] CI/CD ready

---

### Task 4.2: Monitoring & Logging
**Status**: Ready to implement  
**Estimate**: 1 day  
**Assignee**: Forge  

#### Deliverables
- `logging/__init__.py` - Logging module
- `monitoring/__init__.py` - Monitoring module
- `logs/` directory structure

#### Acceptance Criteria
- [ ] Structured JSON logs
- [ ] Request/response logging
- [ ] Performance metrics
- [ ] Error tracking

---

### Task 4.3: Documentation
**Status**: Ready to implement  
**Estimate**: 2 days  
**Assignee**: Scribe (or Forge)  

#### Deliverables
- `README.md` - Project overview
- `docs/setup.md` - Setup guide
- `docs/configuration.md` - Configuration reference
- `docs/API.md` - API documentation

#### Acceptance Criteria
- [ ] Setup instructions clear
- [ ] Configuration documented
- [ ] API endpoints documented
- [ ] Examples provided

---

### Task 4.4: Evaluation Dataset
**Status**: Ready to implement  
**Estimate**: 1 day  
**Assignee**: Sentinel (or Forge)  

#### Deliverables
- `eval/` directory
- `eval/dataset.csv` - Test questions
- `eval/metrics.py` - Evaluation metrics
- `eval/report.md` - Evaluation report

#### Acceptance Criteria
- [ ] Retrieval quality measured
- [ ] Generation quality measured
- [ ] Abstention behavior tested
- [ ] Baseline established

---

### Sprint 4 Summary

| Task | Priority | Duration | Status |
|------|----------|----------|--------|
| Test Suite Expansion | P1 | 2 days | Ready |
| Monitoring & Logging | P1 | 1 day | Ready |
| Documentation | P1 | 2 days | Ready |
| Evaluation Dataset | P1 | 1 day | Ready |

**Total**: 6 days  
**Blockers**: None  
**Parallelizable**: Yes

---

## Total Implementation Timeline

| Sprint | Duration | Focus |
|--------|----------|-------|
| Sprint 0 | 5 days | Foundation |
| Sprint 1 | 7.5 days | Core RAG Pipeline |
| Sprint 2 | 6.5 days | Workflow & Generation |
| Sprint 3 | 6 days | Enhancement & UI |
| Sprint 4 | 6 days | Hardening & Docs |
| **TOTAL** | **31 days** | **~6 weeks** |

---

## Task Dependencies

```
Sprint 0
├── 0.1 Configuration ──┐
├── 0.2 LLM Interface ──┼──► 2.1 Workflow
├── 0.3 FAISS Basic ────┼──► 1.4 FAISS Persistence
└── 0.4 PDF Loader ─────┴──► 1.1 Extended Loaders

Sprint 1
├── 1.1 Extended Loaders ──► 1.2 Chunking
├── 1.2 Chunking ──────────► 1.3 Embedding
├── 1.3 Embedding ─────────► 1.4 FAISS Persistence
└── 1.4 FAISS Persistence ─► 1.5 Basic Retrieval

Sprint 2
├── 1.5 Basic Retrieval ────► 2.1 Workflow
├── 0.2 LLM Interface ──────┤
└── 2.1 Workflow ───────────► 2.2 Generation

Sprint 3
├── 2.2 Generation ─────────► 3.1 Streamlit UI
└── 1.5 Basic Retrieval ────► 3.2 Reranking

Sprint 4
├── All previous sprints ──► 4.1 Test Suite
└── All previous sprints ──► 4.2 Monitoring
```

---

## Acceptance Testing Strategy

### Unit Tests
- Each module has dedicated test file
- 80%+ coverage target
- Uses pytest and mock for external dependencies

### Integration Tests
- End-to-end queries
- Document ingestion pipeline
- Persistence/reload cycles
- Session management

### Acceptance Tests
- User scenarios documented
- Test dataset with known answers
- Manual testing checklist

---

## Risk Mitigation in Sprint Planning

| Risk | Mitigation in Sprints |
|------|----------------------|
| Embedding quality issues | Sprint 1 - Test with sample queries early |
| Retrieval not finding docs | Sprint 1 - Debug检索 with sample data |
| Hallucination | Sprint 2 - Grounded generation with citations |
| Slow performance | Sprint 3 - Profile and optimize |
| UI complexity | Sprint 3 - Start simple, iterate |

---

*Task Outline version: 1.0*
*Last updated: 2026-08-20*

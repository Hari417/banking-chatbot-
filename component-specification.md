# Banking RAG Chatbot: Component Specification

**Version:** 1.0  
**Status:** Draft  
**Last Updated:** 2026-08-20

---

## 1. User Interface Layer

### 1.1 Streamlit Chat Interface
**Responsibility:** Primary user interaction channel

**Components:**
- Chat message display (user/assistant bubbles)
- Source citation panel (collapsible)
- New session button
- Model configuration sidebar (optional)

**Technology:** Streamlit (Python)
**Configuration:**
```yaml
ui:
  port: 8501
  theme: "light"
  page_title: "Banking FAQ Assistant"
  show_source_citations: true
```

**Acceptance Criteria:**
- [ ] Displays chat messages sequentially
- [ ] Shows source documents with excerpts
- [ ] Allows new session creation
- [ ] Responsive on desktop browsers

---

## 2. Backend API Layer

### 2.1 FastAPI Application
**Responsibility:** HTTP API for chat operations

**Endpoints:**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/chat` | POST | Main chat endpoint with streaming support |
| `/ingest` | POST | Document ingestion endpoint |
| `/health` | GET | Health check |
| `/config` | GET/POST | Configuration management |

**Request/Response Models:**
```python
class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    context: dict | None = None

class ChatResponse(BaseModel):
    response: str
    sources: list[SourceCitation]
    confidence: float
    session_id: str
```

**Technology:** FastAPI, Uvicorn, Pydantic

---

## 3. Security Layer

### 3.1 Input Guard
**Responsibility:** Pre-process user input for security

**Functions:**
- Pattern matching for PII (credit card numbers, SSN)
- Prompt injection detection
- Input length validation
- Profanity/content filtering

**Implementation Options:**
1. **PII Detection:** Presidio (Microsoft) or regex patterns
2. **Injection Detection:** Keyword lists + heuristics
3. **Rate Limiting:** SlowAPI or Redis-backed limiter

**Configuration:**
```yaml
security:
  rate_limit: "10/minute"
  max_input_length: 1000
  pii_detection: true
  injection_filter: true
```

---

## 4. RAG Pipeline (LangGraph)

### 4.1 Query Router (Intent Classification)
**Responsibility:** Determine query type and route accordingly

**Approaches:**
- **Simple:** Keyword-based routing
- **Advanced:** Lightweight classifier (DistilBERT)

**Query Types:**
- `FAQ_QUERY`: Knowledge retrieval
- `GREETING`: Small talk handler
- `IRRELEVANT`: Out-of-scope
- `CLARIFICATION`: Follow-up question

**State Output:**
```python
{"query_type": "FAQ_QUERY", "needs_retrieval": True}
```

### 4.2 Hybrid Retriever
**Responsibility:** Retrieve relevant documents from multiple sources

**Architecture:**
```
Query
  ├─→ FAISS (Dense) ──→ Dense Results
  └─→ BM25 (Sparse) ──→ Sparse Results
            ↓
      Fusion Algorithm
            ↓
     Combined Results
```

**Fusion Options:**
1. **Reciprocal Rank Fusion (RRF):** Recommended
   - Score = Σ(1 / (k + rank))
   - k = 60 (standard)
2. **Linear Combination:** Weights sum at 1.0
3. **Simple Concatenation:** Take top-N from each

**Technology:**
- Dense: FAISS (IndexFlatIP or IndexIVFFlat)
- Sparse: Rank-BM25 or Whoosh

### 4.3 Reranker
**Responsibility:** Reorder retrieved documents by relevance

**Options:**
1. **Cross-Encoder (Recommended):** ms-marco-MiniLM-L-6-v2
2. **ColBERT:** For better accuracy, higher compute
3. **Skip for v1:** Simpler, slightly lower accuracy

**Input/Output:**
```python
# Input: Query + List of Documents
rerank(query: str, docs: list[Document]) -> list[Document, score]

# Output: Reordered by cross-attention score
```

### 4.4 Context Assembler
**Responsibility:** Build input context for LLM prompt

**Functions:**
1. Deduplicate near-identical chunks
2. Sort by relevance score
3. Truncate to token budget (max_context_tokens)
4. Format with separators

**Format:**
```
[Document 1]
Title: {source}
Excerpt: {text}

[Document 2]
Title: {source}
Excerpt: {text}
```

### 4.5 Prompt Builder
**Responsibility:** Construct system and user prompts

**System Prompt Template:**
```
You are BankingBot, an AI assistant for general banking FAQs.
Answer questions based ONLY on the provided documents.
If the answer is not in the documents, say "I don't have information about that."

RULES:
1. Use only the provided documents
2. Cite sources with [1], [2], etc.
3. Keep answers concise (2-4 sentences)
4. Do NOT make up information
5. NEVER provide banking transaction advice
```

**Configuration:**
```yaml
prompts:
  system: "path/to/system_template.txt"
  max_context_tokens: 3000
  max_response_tokens: 500
```

### 4.6 LLM Client
**Responsibility:** Generate responses via LLM API

**Interface:** OpenAI-compatible API

**Providers:**
- OpenAI API (GPT-4o-mini, GPT-4o)
- Ollama (local models: Llama3, Mistral)
- Other compatible endpoints

**Configuration:**
```yaml
llm:
  provider: "openai"  # or "ollama"
  model: "gpt-4o-mini"
  temperature: 0.1
  max_retries: 3
  timeout: 30
```

### 4.7 Response Validator
**Responsibility:** Check response quality

**Checks:**
1. **Grounding:** Response mentions sourced docs
2. **Hallucination:** Detect made-up info (basic heuristics)
3. **Length:** Within token budget
4. **Safe Content:** No disallowed content

**Action on Fail:**
- Retry with higher temperature
- Return abstention message
- Log for review

### 4.8 Citation Generator
**Responsibility:** Format source citations for UI

**Output Format:**
```python
class SourceCitation:
    index: int
    source: str  # Document filename
    page: int | None
    excerpt: str
    score: float
```

**UI Formatting:**
- Superscript citation markers [1], [2]
- Collapsible panel with full excerpts

---

## 5. Session Memory Layer

### 5.1 Session State Manager
**Responsibility:** Track conversation context

**Storage Options:**
- **v1:** In-memory dictionary (Python)
- **v2:** SQLite with TTL

**Data Structure:**
```python
SessionState:
    session_id: str (UUID)
    created_at: datetime
    last_active: datetime
    messages: list[Message]  # Full history
    context: dict  # Retrieved docs from last turn
```

**TTL:** 30 minutes idle → auto-cleanup

---

## 6. Vector Store Layer

### 6.1 FAISS Index
**Responsibility:** Store and retrieve document embeddings

**Index Types:**
| Type | Best For | Notes |
|------|----------|-------|
| IndexFlatIP | <10K docs | Exact, slow, high recall |
| IndexIVFFlat | 10K-100K | Approximate, fast, tune nlist |
| IndexHNSW | >100K | Graph-based, high recall |

**Recommendation:** IndexFlatIP for v1 (simplicity)

**Metadata Mapping:**
```python
# FAISS ID -> Metadata
{
    "faiss_id": 0,
    "source": "loan_policy_2024.pdf",
    "page": 12,
    "section": "Interest Rates",
    "text": "content..."
}
```

**Persistence:**
- FAISS index: `banking_index.faiss`
- Metadata: `banking_metadata.pkl` or JSON

### 6.2 Embedding Model
**Responsibility:** Convert text to dense vectors

**Recommended Models:**

| Model | Size | Speed | Quality |
|-------|------|-------|---------|
| all-MiniLM-L6-v2 | 22M | Fast | Good |
| all-mpnet-base-v2 | 110M | Medium | Better |
| BAAI/bge-small-en | 33M | Fast | Good |
| BAAI/bge-base-en | 110M | Medium | Best |

**Recommendation:** all-MiniLM-L6-v2 for v1 speed

**Technology:** sentence-transformers

### 6.3 BM25 Index
**Responsibility:** Sparse lexical retrieval

**Implementation:**
- `rank_bm25` library (pure Python)
- Or Whoosh (inverted index)
- Or skip for v1 (optional)

**Process:**
1. Tokenize chunks
2. Build inverted index
3. Score documents at query time

---

## 7. Document Store Layer

### 7.1 Document Loader
**Responsibility:** Read various document formats

**Formats:**
- PDF (PyPDF2, pdfplumber)
- HTML/TXT (built-in)
- DOCX (python-docx)

**Configuration:**
```yaml
loader:
  supported_formats: [".pdf", ".html", ".txt"]
  extract_images: false
  timeout: 60
```

### 7.2 Chunker
**Responsibility:** Split documents into retrievable chunks

**Strategy:** Recursive Character Text Splitter

**Parameters:**
```yaml
chunking:
  mode: "recursive"
  chunk_size: 512
  chunk_overlap: 50
  separators: ["\n\n", "\n", ". ", " " ]
```

**Considerations:**
- Banking docs: Paragraph-level works well
- Overlap helps continuity
- Size matches embedding model token limit

### 7.3 Metadata Extractor
**Responsibility:** Extract document metadata

**Fields:**
- `source`: Filename
- `title`: Document title
- `page`: Page number (PDF only)
- `section`: Section header (if detectable)
- `created`: Document date
- `ingested`: Timestamp

---

## 8. Configuration Architecture

### 8.1 Config File (YAML)
**Path:** `config.yaml` or `config/settings.yaml`

**Structure:**
```yaml
app:
  name: "Banking FAQ Bot"
  version: "1.0.0"
  environment: "local"

paths:
  documents: "./data/documents"
  index: "./data/index"
  logs: "./logs"

security:
  rate_limit: "10/minute"
  max_input_length: 1000

retrieval:
  top_k_dense: 10
  top_k_sparse: 10
  top_k_final: 5
  rerank: true

llm:
  provider: "openai"
  model: "gpt-4o-mini"
  temperature: 0.1
  max_retries: 3

embeddings:
  model: "all-MiniLM-L6-v2"
  device: "cpu"
  batch_size: 32

session:
  ttl_minutes: 30
  max_history: 10

ui:
  port: 8501
  show_sources: true
```

**Environment Variables:**
```bash
OPENAI_API_KEY="..."
# or
OLLAMA_HOST="http://localhost:11434"
```

---

## 9. Evaluation Architecture

### 9.1 Evaluation Dataset
**Format:** JSONL with (question, expected_chunks, acceptable_answers)

**Categories:**
- Retrieval accuracy
- Answer relevance
- Hallucination detection
- Abstention correctness

### 9.2 Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| Recall@K | Relevant docs in top-K | >0.8 @K=5 |
| MRR | Mean Reciprocal Rank | >0.7 |
| Answer F1 | Overlap with reference | >0.6 |
| Hallucination Rate | False info in answers | <0.05 |
| Abstention Accuracy | Correct "I don't know" | >0.9 |

---

## 10. Error Handling Strategy

### 10.1 Error Hierarchy

| Level | Action | Example |
|-------|--------|---------|
| Input | Reject with message | PII detected |
| Retrieval | Return high-confidence only | Empty results |
| LLM | Retry with fallback | Timeout |
| System | Log + graceful degradation | Index missing |

### 10.2 Abstention Triggers
- No retrieved documents above threshold
- Response validator fails
- Multiple retries exhausted

**Abstention Message:**
> "I don't have enough information to answer that question based on available banking documents."

---

## 11. Deployment Model

### 11.1 Local Deployment (v1)
```
User Machine
├── Python 3.9+
├── FastAPI backend (port 8000)
├── Streamlit UI (port 8501)
├── FAISS index (local file)
└── LLM connection (OpenAI or Ollama)
```

### 11.2 Future Deployment (v2+)
- Containerization (Docker)
- Cloud deployment with persistent storage
- Separate vector database (Pinecone, Weaviate)

---

## Appendix A: Technology Decisions

| Decision | Options | Chosen | Rationale |
|----------|---------|--------|-----------|
| UI Framework | Streamlit vs Gradio vs Flask | Streamlit | Speed, built-in chat components |
| Vector DB | FAISS vs Chroma vs Weaviate | FAISS | Local-first, no external deps |
| LLM API | OpenAI vs Ollama vs Anthropic | OpenAI-compatible | Flexibility, configurable |
| Chunking | Fixed vs Recursive vs Semantic | Recursive | Balance of simplicity/effectiveness |
| Retriever | Dense vs Hybrid | Hybrid | Best recall for FAQ domain |
| Reranker | Cross-encoder vs None | Cross-encoder | Better precision, acceptable latency |

---

## Appendix B: Trade-offs Summary

### Latency vs Accuracy
- **Fast path:** Dense-only retrieval, no rerank (lower latency)
- **Accurate path:** Hybrid + rerank (higher latency, better results)
- **v1 default:** Hybrid + cross-encoder rerank (balanced)

### Simplicity vs Features
- **Simple:** Single retriever, basic prompts
- **Feature-rich:** Multi-retriever, query rewriting, advanced validation
- **v1 scope:** Intentionally simple for reliability

### Local vs Cloud
- **All-local:** Ollama + FAISS (offline operation)
- **Hybrid:** FAISS local + OpenAI API (requires internet)
- **v1 default:** Configurable, user chooses

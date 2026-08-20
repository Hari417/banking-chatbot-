# Banking RAG Chatbot: Ingestion and Preprocessing Pipeline Spec

**Version:** 1.0  
**Date:** 2026-08-20  
**Author:** Archer (System Architecture)
**Scope:** Knowledge base ingestion, chunking, cleaning, and preparation for embedding

---

## Executive Summary

This document specifies the complete pipeline for ingesting, preprocessing, and preparing banking policy documents, FAQs, and product sheets for the RAG chatbot. The pipeline ensures documents are safely processed, appropriately chunked, and ready for vector search while maintaining strict PII compliance.

**Key Non-Negotiables:**
- ❌ **No PII processing:** Documents containing PII are rejected or redacted
- ✅ **Audit trail:** All ingestion events are logged with timestamps and checksums
- ✅ **Versioning:** Document versions must be tracked and retrievable

---

## 1. Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    INGESTION PIPELINE                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Raw Documents                                                  │
│       │                                                         │
│       ▼                                                         │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────────┐  │
│  │ Stage 1:    │────►│ Stage 2:    │────►│ Stage 3:        │  │
│  │ FORMAT      │     │ CONTENT     │     │ CHUNKING &      │  │
│  │ DETECTION   │     │ EXTRACTION  │     │ TRANSFORMATION  │  │
│  └─────────────┘     └─────────────┘     └─────────────────┘  │
│       success              success              success        │
│       │                    │                    │              │
│       ▼                    ▼                    ▼              │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────────┐  │
│  │ Stage 4:    │────►│ Stage 5:    │────►│ Stage 6:        │  │
│  │ PII         │     │ METADATA    │     │ EMBEDDING &     │  │
│  │ VALIDATION  │     │ ENRICHMENT  │     │ INDEX BUILDING  │  │
│  └─────────────┘     └─────────────┘     └─────────────────┘  │
│       │                    │                    │              │
│       ▼                    ▼                    ▼              │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                    STAGE 7: PERSISTENCE                  │  │
│  │          (FAISS + Metadata Store + Audit Log)          │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

                           │
                           ▼
              ┌────────────────────────┐
              │  STAGE 8: POST-PROCESS  │
              │  (Validation & Cleanup)  │
              └────────────────────────┘
```

### Pipeline Flow Summary

| Stage | Purpose | Input | Output | Failure Action |
|-------|---------|-------|--------|----------------|
| 1 | Format Detection | Raw file bytes | Detected format | Reject unsupported |
| 2 | Content Extraction | Detected format | Raw text chunks | Log error, skip file |
| 3 | Chunking | Raw text | Processed chunks | Artifact for retry |
| 4 | PII Validation | Processed chunks | PII-free chunks | Quarantine document |
| 5 | Metadata Enrichment | Chunks + original | Enriched chunks | Continue with basic meta |
| 6 | Embedding | Chunks + model | Vectors + index | Incremental index build |
| 7 | Persistence | Vectors + metadata | Stored artifacts | Rollback transaction |
| 8 | Post-Process | Stored artifacts | Validation report | Alert admin |

---

## 2. Stage 1: Format Detection

### Purpose
Automatically determine document format and select appropriate parser.

### Supported Formats

| Format | Extension | Detection Method | Parser Library |
|--------|-----------|------------------|----------------|
| PDF | .pdf | Magic bytes (PDF header) | pdfplumber, PyMuPDF |
| Microsoft Word | .docx | ZIP + OOXML structure | python-docx |
| HTML | .html, .htm | DOCTYPE or tag patterns | BeautifulSoup4 |
| Plain Text | .txt | Fallback, heuristic check | Built-in |
| Markdown | .md | Extension, frontmatter | markdown-it-py |

### Detection Implementation

```python
class FormatDetector:
    """
    Detect document format using magic bytes and heuristics.
    """
    MAGIC_BYTES = {
        b'%PDF': 'pdf',
        b'PK\x03\x04': 'zip',  # May be docx
    }
    
    def detect(self, file_path: str, content: bytes) -> FormatDetection:
        """
        Returns detected format with confidence score.
        
        Raises:
            UnsupportedFormatError: If format cannot be determined
        """
        # Check magic bytes
        for magic, fmt in self.MAGIC_BYTES.items():
            if content.startswith(magic):
                if fmt == 'zip':
                    return self._check_ooxml(content)
                return FormatDetection(format=fmt, confidence=1.0)
        
        # Heuristic detection for text formats
        return self._heuristic_detect(file_path, content)
```

### Output Schema

```python
class FormatDetection:
    format: str          # pdf, docx, html, txt, md
    confidence: float    # 0.0 to 1.0
    mime_type: str       # application/pdf, etc.
    detected_encoding: str  # UTF-8, Latin-1, etc.
```

### Validation Rules

- Format confidence must be >= 0.8 for automatic processing
- Low confidence (< 0.8) requires manual review
- Unknown formats are rejected with detailed logging

---

## 3. Stage 2: Content Extraction

### Purpose
Extract clean, structured text content from documents while preserving semantic structure.

### PDF Extraction

**Library:** pdfplumber (primary), PyMuPDF (fallback for scanned docs)

```python
class PDFExtractor:
    """
    Extract text from PDF with page-level structure.
    """
    
    def extract(self, file_path: str) -> Iterator[PageContent]:
        """
        Yield pages with extracted text and metadata.
        """
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                tables = page.extract_tables()  # Preserve tabular data
                
                yield PageContent(
                    page_number=page_num,
                    text=text,
                    bbox=page.bbox,
                    has_tables=len(tables) > 0,
                    table_text=self._tables_to_markdown(tables)
                )
    
    def _tables_to_markdown(self, tables: list) -> str:
        """Convert tables to markdown format for better chunking."""
        return convert_tables_to_markdown(tables)
```

### HTML Extraction

**Library:** BeautifulSoup4

```python
class HTMLExtractor:
    """
    Extract text from HTML, preserving heading structure.
    """
    
    def extract(self, content: str) -> Iterator[Section]:
        """
        Extract sections based on heading hierarchy.
        """
        soup = BeautifulSoup(content, 'html.parser')
        
        # Remove script/style elements
        for element in soup(['script', 'style', 'nav', 'footer']):
            element.decompose()
        
        # Extract by heading structure
        current_section = None
        for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li']):
            if element.name.startswith('h'):
                if current_section:
                    yield current_section
                current_section = Section(
                    heading_level=int(element.name[1]),
                    heading_text=element.get_text(strip=True),
                    content=[]
                )
            else:
                if current_section:
                    current_section.content.append(element.get_text(strip=True))
```

### DOCX Extraction

**Library:** python-docx

```python
class DOCXExtractor:
    """
    Extract text from Word documents with paragraph structure.
    """
    
    def extract(self, file_path: str) -> Iterator[Paragraph]:
        """
        Yield paragraphs with style information.
        """
        doc = Document(file_path)
        
        for para in doc.paragraphs:
            if para.text.strip():
                yield Paragraph(
                    text=para.text,
                    style=para.style.name,
                    is_heading=para.style.name.startswith('Heading')
                )
```

### Extraction Output

```python
class ExtractedContent:
    """Common format for all document types."""
    source_file: str
    total_pages: int | None
    sections: list[Section]
    tables: list[Table]
    extraction_metadata: ExtractionMetadata

class Section:
    heading: str | None
    heading_level: int
    content: str
    page_number: int | None
    word_count: int

class ExtractionMetadata:
    extractor_version: str
    extraction_timestamp: str
    processing_time_ms: float
    warnings: list[str]
```

---

## 4. Stage 3: Chunking and Transformation

### Purpose
Split documents into semantically coherent chunks optimized for retrieval.

### Chunking Strategy: Recursive Character Text Splitter

**Rationale:** Banking documents have varied structures—some are dense paragraphs, others are FAQ lists or tables. Recursive splitting respects natural boundaries while maintaining chunk size limits.

```python
class RecursiveTextSplitter:
    """
    Split text recursively using hierarchical separators.
    Order of separation: paragraphs, sentences, words, characters.
    """
    
    DEFAULT_SEPARATORS = [
        "\n\n",      # Paragraph breaks
        "\n",       # Line breaks  
        ". ",       # Sentence boundaries
        "? ",       # Question boundaries
        "! ",       # Exclamation boundaries
        " ",        # Word boundaries
        ""          # Character fallback
    ]
    
    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        separators: list[str] | None = None
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or self.DEFAULT_SEPARATORS
    
    def split(self, text: str, metadata: dict) -> Iterator[Chunk]:
        """
        Split text into chunks with overlapping windows.
        
        Args:
            text: Text to split
            metadata: Source metadata to attach to chunks
        """
        if len(text) <= self.chunk_size:
            yield self._create_chunk(text, metadata)
            return
        
        current_chunk = ""
        
        for separator in self.separators:
            segments = text.split(separator)
            
            for segment in segments:
                segment = segment.strip()
                if not segment:
                    continue
                
                if len(current_chunk) + len(segment) + len(separator) <= self.chunk_size:
                    current_chunk += (separator if current_chunk else "") + segment
                else:
                    if current_chunk:
                        yield self._create_chunk(current_chunk, metadata)
                        # Preserve overlap for context
                        current_chunk = self._get_overlap(current_chunk) + separator + segment
                    else:
                        # Segment itself exceeds chunk_size, force split
                        yield self._create_chunk(segment, metadata)
                        current_chunk = ""
        
        if current_chunk:
            yield self._create_chunk(current_chunk, metadata)
```

### Chunking Parameters by Document Type

| Document Type | Chunk Size | Overlap | Strategy |
|--------------|------------|---------|----------|
| Policies (dense text) | 512 tokens | 50 tokens | Paragraph + sentence |
| FAQs (Q&A pairs) | 256 tokens | 0 tokens | Keep Q+A together |
| Product sheets | 384 tokens | 40 tokens | Section-based |
| Tables | 300 tokens | 30 tokens | Row group + header |
| Procedures (step-by-step) | 400 tokens | 40 tokens | Step boundary |

### Semantic Chunking for FAQs

```python
class FAQChunker:
    """
    Handle FAQ documents intelligently—keep questions with answers.
    """
    
    FAQ_PATTERNS = [
        r'Q[:.\s]+(.+?)\nA[:.\s]+(.+?)(?=\nQ[:.\s]|\Z)',  # "Q: ..., A: ..."
        r'\d+\.\s+(.+?)\n(.+?)(?=\n\d+\.\s|\Z)',          # "1. ..." 
        r'FAQ\s*[-:]\s*(.+?)\n(.+?)(?=\nFAQ\s*[-:]|\Z)',   # "FAQ - ..."
    ]
    
    def split_faqs(self, text: str) -> Iterator[Chunk]:
        """
        Extract FAQ pairs that fit in token budget.
        """
        for pattern in self.FAQ_PATTERNS:
            matches = re.finditer(pattern, text, re.DOTALL | re.IGNORECASE)
            for match in matches:
                question = match.group(1).strip()
                answer = match.group(2).strip()
                
                combined = f"Q: {question}\nA: {answer}"
                
                if self._token_count(combined) <= self.max_tokens:
                    yield Chunk(
                        content=combined,
                        chunk_type="faq_pair",
                        metadata={"question": question, "answer": answer}
                    )
                else:
                    # Oversized FAQ—split answer
                    yield from self._split_oversized_faq(question, answer)
```

### Table Transformation

```python
class TableTransformer:
    """
    Convert tables to text representations for embedding.
    """
    
    def to_text(self, table: Table) -> str:
        """
        Convert table to structured text.
        """
        # Option 1: Markdown table
        md = self._to_markdown(table)
        
        # Option 2: Key-value pairs (for smaller tables)
        kv = self._to_keyvalue(table)
        
        # Option 3: Sentence description (for very wide tables)
        desc = self._to_description(table)
        
        return md  # Default to markdown
    
    def _to_keyvalue(self, table: Table) -> str:
        """Convert to key-value format—great for retrieval."""
        rows = []
        headers = table.headers
        for row in table.rows:
            pairs = [f"{h}: {v}" for h, v in zip(headers, row)]
            rows.append("; ".join(pairs))
        return "\n".join(rows)
```

### Chunk Output Schema

```python
class Chunk:
    """A document chunk ready for embedding."""
    content: str                      # The actual text
    chunk_id: str                     # UUID
    source_document: str               # Original filename
    chunk_index: int                 # Position in document
    chunk_type: str                  # paragraph, faq_pair, table, procedure
    
    # Character positions (for highlighting in source)
    start_char: int
    end_char: int
    
    # Section hierarchy
    section_path: list[str]          # ["Section 1", "Subsection 1.2"]
    
    # Metrics
    token_count: int
    word_count: int
    
    # Processing metadata
    processed_at: str
    processing_version: str
```

---

## 5. Stage 4: PII Validation and Sanitization

### Purpose
Detect and either reject or redact documents containing Personally Identifiable Information.

### PII Detection Scope

| Category | Examples | Detection Method |
|----------|----------|------------------|
| Names | Customer names | Pattern + NER |
| Account Numbers | 1234-5678-9012 | Regex + checksum validation |
| Credit Cards | 4532-... | Luhn checksum + pattern |
| SSN/National IDs | XXX-XX-XXXX | Regex patterns |
| Phone Numbers | +1-555-... | International format regex |
| Emails | user@domain.com | Email pattern |
| Addresses | Street addresses | Address pattern + validation |
| Dates of Birth | MM/DD/YYYY | Date pattern + context |
| Transaction Amounts | $1,234.56 | Currency pattern + context |

### Implementation

```python
class PIIDetector:
    """
    Detect PII in text chunks using pattern matching and ML.
    """
    
    def __init__(self, use_ml: bool = True):
        self.use_ml = use_ml
        self.patterns = self._load_patterns()
        if use_ml:
            self.ner_pipeline = self._load_ner_model()
    
    def scan(self, chunks: list[Chunk]) -> PIIReport:
        """
        Scan chunks for PII. Returns detailed findings.
        """
        findings = []
        
        for chunk in chunks:
            chunk_findings = self._scan_chunk(chunk)
            if chunk_findings:
                findings.extend(chunk_findings)
        
        return PIIReport(
            total_chunks=len(chunks),
            affected_chunks=len(set(f.chunk_id for f in findings)),
            findings=findings,
            risk_level=self._calculate_risk(findings)
        )
    
    def _scan_chunk(self, chunk: Chunk) -> list[PIIFinding]:
        """Scan individual chunk for PII."""
        findings = []
        
        # Pattern-based detection
        for pattern in self.patterns:
            for match in pattern.regex.finditer(chunk.content):
                findings.append(PIIFinding(
                    chunk_id=chunk.chunk_id,
                    pii_type=pattern.pii_type,
                    position=match.span(),
                    confidence=pattern.confidence,
                    redacted=pattern.redact(match.group())
                ))
        
        # ML-based NER detection
        if self.use_ml:
            entities = self.ner_pipeline(chunk.content)
            for entity in entities:
                if entity['entity'] in SENSITIVE_ENTITIES:
                    findings.append(PIIFinding(
                        chunk_id=chunk.chunk_id,
                        pii_type=entity['entity'],
                        position=(entity['start'], entity['end']),
                        confidence=entity['score'],
                        redacted="[REDACTED]"
                    ))
        
        return findings
```

### Handling Policies

| PII Type | Action | Rationale |
|----------|--------|-----------|
| Email addresses | Redact | Common in examples |
| Customer names | Reject document | Likely real customer data |
| Account numbers | Reject document | Definitely sensitive |
| Phone numbers | Reject document | Could be customer data |
| Generic examples | Allow with flags | "example@bank.com" is OK |
| Sample data | Redact + flag | Mark as synthetic |

### Rejection Flow

```
PII Detection
     │
     ├─► No PII found ──► Continue processing
     │
     ├─► Low-risk PII detected ──► Redact + flag ──► Continue
     │
     └─► High-risk PII detected ──► Reject document
                │
                ▼
         Quarantine document
                │
                ├─► Log rejection
                ├─► Alert admin
                └─► Move to quarantine/ folder
```

### PII Report Schema

```python
class PIIReport:
    total_chunks: int
    affected_chunks: int
    findings: list[PIIFinding]
    risk_level: str  # none, low, medium, high
    recommended_action: str  # proceed, redact, reject
    redacted_content: dict[str, str]  # chunk_id -> redacted_text

class PIIFinding:
    chunk_id: str
    pii_type: str
    position: tuple[int, int]
    confidence: float
    redacted: str  # Replacement text
```

---

## 6. Stage 5: Metadata Enrichment

### Purpose
Attach rich metadata to chunks for improved retrieval and filtering.

### Metadata Schema

```python
class ChunkMetadata:
    # Source Information
    source_file: str
    source_hash: str  # SHA-256 of original file
    file_size_bytes: int
    document_type: str  # policy, faq, product_sheet, procedure
    
    # Temporal
    document_created: str | None  # From file metadata
    document_modified: str | None
    ingested_at: str
    
    # Structural
    page_number: int | None
    section_path: list[str]
    heading_level: int
    chunk_index: int
    total_chunks_in_doc: int
    
    # Content Classification
    content_type: str  # paragraph, faq_question, faq_answer, table, list
    topic_tags: list[str]  # Auto-generated via keyword extraction
    
    # Banking Domain Specific
    product_category: str | None  # loans, savings, credit_cards, etc.
    document_category: str | None  # policy, terms, faq, guide
    audience: str | None  # customer, employee, internal
    
    # Versioning
    version: str
    replaces_chunks: list[str] | None  # Previous versions
    is_current: bool
    
    # Retrieval Hints
    boost_factors: dict  # {recency: 1.0, authority: 1.0}
    expiration_date: str | None
```

### Automatic Metadata Extraction

```python
class MetadataEnricher:
    """
    Automatically enrich chunks with derived metadata.
    """
    
    BANKING_KEYWORDS = {
        'loans': ['loan', 'mortgage', 'lending', 'interest rate', 'APR'],
        'savings': ['savings', 'deposit', 'interest', 'APY', 'account'],
        'credit_cards': ['credit card', 'APR', 'limit', 'statement'],
        'checking': ['checking', 'debit', 'overdraft'],
        'insurance': ['insurance', 'policy', 'coverage', 'claim'],
        'investments': ['investment', 'fund', 'portfolio', 'brokerage']
    }
    
    def enrich(self, chunk: Chunk, source_doc: Document) -> Chunk:
        """
        Enrich chunk with automatic metadata.
        """
        enriched = chunk.copy()
        
        # Extract topic tags from content
        enriched.topic_tags = self._extract_keywords(chunk.content)
        
        # Detect product category
        enriched.product_category = self._detect_category(chunk.content)
        
        # Determine document category from filename and content
        enriched.document_category = self._classify_document(source_doc.filename)
        
        # Set audience based on language patterns
        enriched.audience = self._detect_audience(chunk.content)
        
        # Calculate boost factors
        enriched.boost_factors = self._calculate_boosts(enriched)
        
        return enriched
    
    def _extract_keywords(self, text: str) -> list[str]:
        """Extract keywords using TF-IDF or similar."""
        # Implementation using scikit-learn or keybert
        extractor = KeyBERT()
        keywords = extractor.extract_keywords(
            text, 
            keyphrase_ngram_range=(1, 2),
            top_n=5
        )
        return [kw for kw, score in keywords if score > 0.3]
    
    def _detect_category(self, text: str) -> str | None:
        """Detect banking product category."""
        text_lower = text.lower()
        scores = {}
        
        for category, keywords in self.BANKING_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            scores[category] = score
        
        best = max(scores.items(), key=lambda x: x[1])
        return best[0] if best[1] > 0 else None
```

### Filename-Based Metadata

| Filename Pattern | Document Type | Product Category |
|------------------|---------------|------------------|
| `*loan*.pdf` | policy | loans |
| `*savings*.pdf` | policy | savings |
| `*FAQ*.html` | faq | mixed |
| `*product_sheet*.docx` | product_sheet | varies |
| `*procedure*.pdf` | procedure | varies |
| `*terms*.pdf` | terms | varies |

---

## 7. Stage 6: Embedding Generation

### Purpose
Generate dense vector embeddings for chunks using sentence-transformers.

### Model Selection

| Model | Dimensions | Speed | Quality | Use Case |
|-------|------------|-------|---------|----------|
| all-MiniLM-L6-v2 | 384 | Fast | Good | v1 default |
| all-mpnet-base-v2 | 768 | Medium | Better | Quality priority |
| BAAI/bge-small-en | 384 | Fast | Good | Alternative |
| BAAI/bge-base-en | 768 | Medium | Best | Maximum quality |

### Embedding Configuration

```yaml
# config.yaml
embeddings:
  model: "all-MiniLM-L6-v2"
  device: "cpu"  # or "cuda" if available
  batch_size: 32
  normalize: true  # Normalize vectors for cosine similarity
  
  # Quantization options
  quantization: null  # "int8" or "binary" for memory reduction
```

### Implementation

```python
from sentence_transformers import SentenceTransformer

class EmbeddingGenerator:
    """
    Generate embeddings for text chunks.
    """
    
    def __init__(self, config: EmbeddingConfig):
        self.model = SentenceTransformer(config.model)
        if config.device == "cuda" and torch.cuda.is_available():
            self.model = self.model.cuda()
        
        self.batch_size = config.batch_size
        self.normalize = config.normalize
    
    def generate(self, chunks: list[Chunk]) -> list[ChunkWithEmbedding]:
        """
        Generate embeddings for chunks in batches.
        """
        texts = [chunk.content for chunk in chunks]
        
        embeddings = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            batch_embeddings = self.model.encode(
                batch,
                convert_to_numpy=True,
                normalize_embeddings=self.normalize,
                show_progress_bar=False
            )
            embeddings.extend(batch_embeddings)
        
        return [
            ChunkWithEmbedding(
                chunk=chunk,
                embedding=embedding.astype('float32')
            )
            for chunk, embedding in zip(chunks, embeddings)
        ]
```

---

## 8. Stage 7: Persistence

### Purpose
Store embeddings in FAISS index with metadata mapping.

### FAISS Index Configuration

```python
class FAISSIndexManager:
    """
    Manage FAISS index for document embeddings.
    """
    
    def __init__(self, index_path: str, embedding_dim: int = 384):
        self.index_path = index_path
        self.embedding_dim = embedding_dim
        self.index = None
        self.metadata = {}
    
    def create_index(self) -> faiss.Index:
        """
        Create FAISS index. Start with IndexFlatIP.
        """
        # IndexFlatIP: Exact search, inner product (cosine for normalized)
        self.index = faiss.IndexFlatIP(self.embedding_dim)
        
        # Wrap with ID mapping for metadata tracking
        self.index = faiss.IndexIDMap(self.index)
        
        return self.index
    
    def add_chunks(self, chunks_with_embeddings: list[ChunkWithEmbedding]):
        """
        Add chunks to index with metadata tracking.
        """
        embeddings = np.array([
            cwe.embedding for cwe in chunks_with_embeddings
        ], dtype='float32')
        
        # Generate sequential IDs
        ids = np.array(range(
            len(self.metadata), 
            len(self.metadata) + len(chunks_with_embeddings)
        ), dtype='int64')
        
        # Add to FAISS
        self.index.add_with_ids(embeddings, ids)
        
        # Store metadata mapping
        for idx, cwe in zip(ids, chunks_with_embeddings):
            self.metadata[int(idx)] = cwe.chunk.metadata
    
    def save(self):
        """Persist index and metadata."""
        faiss.write_index(self.index, f"{self.index_path}/faiss.index")
        
        with open(f"{self.index_path}/metadata.json", 'w') as f:
            json.dump(self.metadata, f, indent=2)
    
    def load(self):
        """Load existing index and metadata."""
        self.index = faiss.read_index(f"{self.index_path}/faiss.index")
        
        with open(f"{self.index_path}/metadata.json", 'r') as f:
            self.metadata = json.load(f)
```

### Directory Structure

```
data/
├── documents/              # Original documents
│   ├── policies/
│   ├── faqs/
│   └── product_sheets/
├── index/                  # FAISS index and metadata
│   ├── faiss.index
│   ├── metadata.json
│   ├── document_registry.json
│   └── version_info.json
├── processed/              # Intermediate processed files
│   ├── chunks/
│   └── extractions/
├── quarantine/             # Rejected documents
│   └── rejected_*.pdf
└── logs/                   # Ingestion logs
    └── ingestion_YYYY-MM-DD.log
```

---

## 9. Stage 8: Post-Processing and Validation

### Purpose
Verify successful ingestion and generate reports.

### Validation Checks

```python
class IngestionValidator:
    """
    Validate ingestion completeness and accuracy.
    """
    
    def validate(self, job: IngestionJob) -> ValidationReport:
        """
        Run comprehensive validation on ingestion job.
        """
        checks = [
            self._check_document_count(job),
            self._check_chunk_count(job),
            self._check_embedding_dimensions(job),
            self._check_metadata_completeness(job),
            self._check_faiss_index_health(job),
            self._check_search_quality(job),
        ]
        
        return ValidationReport(
            job_id=job.job_id,
            passed=all(c.passed for c in checks),
            checks=checks,
            recommendations=self._generate_recommendations(checks)
        )
    
    def _check_search_quality(self, job: IngestionJob) -> ValidationCheck:
        """
        Verify search is working by querying known chunks.
        """
        # Sample a few chunks and verify they're retrievable
        samples = random.sample(job.chunks, min(10, len(job.chunks)))
        
        for chunk in samples:
            # Query with the chunk's own text
            results = self.index.search(chunk.embedding, k=1)
            if results[0][0] != chunk.chunk_id:
                return ValidationCheck(
                    name="search_quality",
                    passed=False,
                    message=f"Chunk {chunk.chunk_id} not top result for own query"
                )
        
        return ValidationCheck(
            name="search_quality",
            passed=True,
            message="All sampled chunks retrievable"
        )
```

### Ingestion Report

```python
class IngestionReport:
    """Summary of ingestion job."""
    
    job_id: str
    started_at: str
    completed_at: str
    
    # Input
    documents_submitted: int
    documents_by_format: dict[str, int]
    
    # Processing
    documents_extracted: int
    chunks_generated: int
    chunks_by_type: dict[str, int]
    
    # PII
    pii_scans_performed: int
    pii_violations_found: int
    documents_rejected: int
    documents_redacted: int
    
    # Output
    chunks_embedded: int
    vectors_in_index: int
    
    # Performance
    total_duration_seconds: float
    avg_processing_time_per_doc: float
    
    # Validation
    validation_passed: bool
    validation_warnings: list[str]
```

---

## 10. Update Strategy and Versioning

### Document Versioning

```python
class DocumentVersionManager:
    """
    Manage document versions and updates.
    """
    
    def upsert_document(self, file_path: str) -> DocumentVersion:
        """
        Hash-based document versioning.
        """
        file_hash = self._compute_hash(file_path)
        
        # Check if already exists
        existing = self.registry.get_by_path(file_path)
        
        if existing and existing.content_hash == file_hash:
            return DocumentVersion(
                action="unchanged",
                reason="Content hash matches existing",
                document_id=existing.id
            )
        
        if existing:
            # Update: mark old chunks as non-current
            self._deprecate_document(existing.id)
            action = "updated"
        else:
            action = "created"
        
        # Process new version
        new_version = self._process_document(file_path, file_hash)
        self.registry.add(new_version)
        
        return DocumentVersion(action=action, document_id=new_version.id)
```

### Update Strategies

| Strategy | Use Case | Implementation |
|----------|----------|----------------|
| Full Rebuild | Major schema changes | Wipe index, re-ingest all |
| Incremental | Routine updates | Process changed docs only |
| Scheduled Nightly | Production systems | Batch update overnight |
| On-Demand | Ad-hoc changes | CLI trigger for specific docs |

### Version Lifecycle

```
Document Ingested
       │
       ▼
  ┌─────────┐
  │ current │ ◄── Active for retrieval
  └────┬────┘
       │
       │ New version uploaded
       ▼
  ┌─────────┐
  │superseded│ ◄── Kept for audit, not retrieved
  └─────────┘
       │
       │ Expiration (configurable)
       ▼
  ┌─────────┐
  │ archived │ ◄── Moved to long-term storage
  └─────────┘
```

---

## 11. API and Interface

### Ingestion API

```python
# FastAPI endpoints

@app.post("/ingest/document", response_model=IngestionResponse)
async def ingest_document(
    file: UploadFile,
    document_type: str | None = Form(None),  # Override auto-detection
    metadata: dict | None = Form(None)
):
    """
    Ingest a single document.
    """
    pass

@app.post("/ingest/batch", response_model=BatchIngestionResponse)
async def ingest_batch(
    files: list[UploadFile],
    options: BatchIngestionOptions
):
    """
    Ingest multiple documents in a batch.
    """
    pass

@app.get("/ingest/status/{job_id}", response_model=IngestionJobStatus)
async def get_ingestion_status(job_id: str):
    """
    Check status of ingestion job.
    """
    pass

@app.delete("/documents/{document_id}")
async def remove_document(document_id: str):
    """
    Remove document from index (soft delete).
    """
    pass

@app.get("/documents/registry", response_model=DocumentRegistry)
async def list_documents(
    status: str | None = None,  # current, superseded, archived
    type: str | None = None
):
    """
    List all documents in registry.
    """
    pass
```

### CLI Interface

```bash
# Ingest single document
python -m banking_rag.ingest document.pdf --type policy

# Batch ingest directory
python -m banking_rag.ingest ./documents/ --recursive --dry-run

# Rebuild index
python -m banking_rag.ingest --rebuild

# Check status
python -m banking_rag.ingest --status

# View registry
python -m banking_rag.ingest --list --filter-type=faq
```

---

## 12. Error Handling and Recovery

### Error Categories

| Category | Examples | Response |
|----------|----------|----------|
| Format Error | Corrupted PDF | Log, skip, continue |
| Extraction Error | Scanned PDF, no text | OCR fallback or reject |
| PII Violation | Customer data detected | Quarantine, alert |
| Memory Error | File too large | Stream processing |
| FAISS Error | Index corruption | Rebuild from backup |

### Recovery Mechanisms

```python
class IngestionRecovery:
    """
    Recovery mechanisms for failed ingests.
    """
    
    def handle_format_error(self, file: Path, error: Exception) -> RecoveryAction:
        """
        Try alternative parsers or skip document.
        """
        for fallback in self.get_fallback_extractors(file.suffix):
            try:
                return fallback.extract(file)
            except Exception:
                continue
        
        return RecoveryAction.quarantine(
            reason="All extraction methods failed",
            original_error=str(error)
        )
    
    def handle_partial_failure(self, job: IngestionJob) -> None:
        """
        Job partially succeeded—roll back or commit partial.
        """
        if job.success_rate < 0.5:
            self.rollback_job(job)
        else:
            self.commit_partial(job)
```

---

## 13. Performance Considerations

### Throughput Targets

| Metric | Target | Implementation |
|--------|--------|----------------|
| Documents/minute | 60 | Parallel processing |
| Chunks/second | 100 | Batch embedding |
| PII scan speed | 10ms/chunk | Compiled regex + caching |
| Index update time | <1s | Incremental FAISS |

### Memory Management

```python
class StreamingIngestion:
    """
    Process large documents in streaming fashion.
    """
    
    def process_large_file(self, file_path: str):
        """
        Stream process files without loading entirely into memory.
        """
        # PDF: Process page by page
        # DOCX: Process paragraph by paragraph
        # HTML: Process element by element
        
        for chunk in self.chunk_stream(file_path):
            embedding = self.embed_single(chunk)
            self.index.add(embedding)
            # Don't keep embedding in memory
```

---

## 14. Security and Compliance

### Access Control

| Resource | Read | Write | Delete |
|----------|------|-------|--------|
| Documents | Any | Admin | Admin |
| Index | Any | System | System |
| Metadata | Any | System | Admin |
| Logs | Admin | System | Never |
| Quarantine | Admin | System | Admin |

### Audit Logging

```python
class AuditLogger:
    """
    Log all ingestion events for compliance.
    """
    
    def log_ingestion_event(self, event: IngestionEvent):
        """
        Permanent, tamper-resistant audit log.
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event.type,  # ingest, update, delete, reject
            "document_hash": event.document_hash,
            "user": event.user_id,
            "action": event.action,
            "result": event.result,
            "pii_scan_result": event.pii_result,
            "ip_address": event.ip_address
        }
        
        self._append_to_wal(entry)
        self._index_for_query(entry)
```

### Data Retention

| Data Type | Retention | Deletion |
|-----------|-----------|----------|
| Documents | 7 years | Soft delete, archive |
| Embeddings | Same as docs | Cascaded |
| Logs | 2 years | Rotate after retention |
| Quarantine | 90 days | Purge automatically |

---

## 15. Configuration Reference

```yaml
# config/ingestion.yaml

ingestion:
  # Processing
  max_file_size_mb: 100
  supported_formats: ["pdf", "docx", "html", "txt", "md"]
  parallel_workers: 4
  
  # Chunking
  chunking:
    default_strategy: "recursive"
    default_chunk_size: 512
    default_chunk_overlap: 50
    
    # Document-type overrides
    strategies:
      faq:
        chunk_size: 256
        overlap: 0
        preserve_pairs: true
      table:
        chunk_size: 300
        overlap: 30
  
  # PII
  pii_detection:
    enabled: true
    use_ml: true
    rejection_threshold: "high"  # low, medium, high
    auto_redact: false           # Reject instead
    quarantine_path: "./data/quarantine"
  
  # Embeddings
  embeddings:
    model: "all-MiniLM-L6-v2"
    device: "cpu"
    batch_size: 32
    normalize: true
  
  # FAISS
  faiss:
    index_path: "./data/index"
    index_type: "IndexFlatIP"  # IndexFlatIP, IndexIVFFlat
    nlist: 100                  # For IVF (if used)
  
  # Versioning
  versioning:
    enabled: true
    keep_superseded: true
    retention_days: 2555  # 7 years
  
  # Logging
  logging:
    level: "INFO"
    audit_enabled: true
    log_path: "./data/logs"
```

---

## 16. Testing Strategy

### Unit Tests

```python
def test_pdf_extraction():
    """Test PDF text extraction."""
    extractor = PDFExtractor()
    content = extractor.extract("test_data/sample.pdf")
    assert len(content.pages) > 0
    assert content.pages[0].text is not None

def test_chunking_consistency():
    """Test chunks can be reassembled."""
    splitter = RecursiveTextSplitter(chunk_size=100, overlap=10)
    text = "Test " * 50
    chunks = list(splitter.split(text, {}))
    
    # Verify overlap preserves continuity
    for i in range(len(chunks) - 1):
        overlap_text = chunks[i].content[-20:]
        next_start = chunks[i+1].content[:20]
        assert overlap_text in next_start or next_start in overlap_text

def test_pii_detection():
    """Test PII patterns are detected."""
    detector = PIIDetector(use_ml=False)
    
    test_cases = [
        ("SSN: 123-45-6789", "ssn", True),
        ("Email: user@test.com", "email", True),
        ("Call 555-555-5555", "phone", True),
        ("General banking policy", None, False),
    ]
    
    for text, expected_type, should_find in test_cases:
        report = detector.scan([Chunk(content=text)])
        assert (len(report.findings) > 0) == should_find
```

### Integration Tests

```python
def test_end_to_end_ingestion():
    """Test full pipeline with sample documents."""
    pipeline = IngestionPipeline(config=test_config)
    
    job = pipeline.ingest_batch([
        "test_data/policy.pdf",
        "test_data/faq.html",
        "test_data/sheet.docx"
    ])
    
    assert job.documents_processed == 3
    assert job.chunks_generated > 0
    assert job.pii_violations == 0
    assert job.validation_passed is True

def test_versioning():
    """Test document updates create versions."""
    # Ingest v1
    v1 = pipeline.ingest("doc.pdf")
    
    # Ingest same file (unchanged)
    v1_again = pipeline.ingest("doc.pdf")
    assert v1_again.action == "unchanged"
    
    # Modify file and re-ingest
    modify_file("doc.pdf")
    v2 = pipeline.ingest("doc.pdf")
    assert v2.action == "updated"
    assert v2.supersedes == v1.document_id
```

---

## 17. Deployment and Operations

### Production Checklist

- [ ] FAISS index backup scheduled
- [ ] Quarantine monitoring alerts configured
- [ ] Audit log rotation configured
- [ ] PII rejection thresholds reviewed
- [ ] Document retention policy documented
- [ ] Index rebuild procedure tested
- [ ] Rollback procedure documented

### Monitoring Metrics

| Metric | Alert Threshold | Action |
|--------|-----------------|--------|
| PII rejection rate | >5% | Review ingestion sources |
| Extraction failure rate | >2% | Check document formats |
| Index size | >10GB | Archive old versions |
| Ingestion latency | >5s/doc | Scale workers |
| Quarantine backlog | >10 docs | Admin notification |

---

## 18. Summary

This ingestion pipeline specification defines a production-ready system for processing banking documents into a searchable knowledge base. Key characteristics:

**Strengths:**
- PII detection and rejection prevent data leaks
- Flexible chunking handles varied document structures
- Versioning supports document lifecycle management
- Full audit trail for compliance
- Configurable via YAML for different environments

**Constraints:**
- Processing limited by available CPU/memory
- FAISS index size impacts memory usage
- OCR not included (assumes text-based PDFs)
- No real-time document synchronization

**Deliverables:**
1. `INGESTION_SPEC.md` - This document
2. Implementation guidance for Forge
3. Test requirements for Sentinel

---

*End of Ingestion Pipeline Specification*

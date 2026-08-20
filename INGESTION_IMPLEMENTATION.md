# Banking RAG Chatbot: Ingestion Pipeline Implementation Notes

**Companion to:** INGESTION_SPEC.md  
**Purpose:** Practical implementation guidance and validation checklist

---

## Core Module Structure

```
banking_rag/
├── __init__.py
├── config.py               # Configuration loading
├── ingestion/
│   ├── __init__.py
│   ├── pipeline.py         # Main IngestionPipeline class
│   ├── stages/
│   │   ├── __init__.py
│   │   ├── stage1_detection.py
│   │   ├── stage2_extraction.py
│   │   ├── stage3_chunking.py
│   │   ├── stage4_pii.py
│   │   ├── stage5_metadata.py
│   │   ├── stage6_embedding.py
│   │   ├── stage7_persistence.py
│   │   └── stage8_validation.py
│   ├── extractors/
│   │   ├── __init__.py
│   │   ├── pdf_extractor.py
│   │   ├── html_extractor.py
│   │   ├── docx_extractor.py
│   │   └── txt_extractor.py
│   └── chunkers/
│       ├── __init__.py
│       ├── recursive_splitter.py
│       ├── faq_chunker.py
│       └── table_transformer.py
├── models/
│   ├── __init__.py
│   ├── chunks.py           # Chunk dataclasses
│   ├── metadata.py         # Metadata schemas
│   └── pii.py              # PII-related classes
├── security/
│   ├── __init__.py
│   ├── pii_detector.py
│   └── audit_logger.py
├── storage/
│   ├── __init__.py
│   ├── faiss_manager.py
│   └── document_registry.py
└── cli/
    ├── __init__.py
    └── ingest.py           # CLI entry point
```

---

## Required Dependencies

```txt
# requirements-ingestion.txt
# Document processing
pdfplumber>=0.10.0
PyPDF2>=3.0.0
python-docx>=0.8.11
beautifulsoup4>=4.12.0
markdown-it-py>=3.0.0

# ML/NLP
sentence-transformers>=2.2.0
transformers>=4.30.0
torch>=2.0.0
faiss-cpu>=1.7.4  # Use faiss-gpu if CUDA available
keybert>=0.7.0

# PII detection (optional ML-based)
presidio-analyzer>=2.2.0
presidio-anonymizer>=2.2.0
spacy>=3.7.0

# Utilities
pydantic>=2.0.0
pyyaml>=6.0
python-magic>=0.4.27
tiktoken>=0.5.0
nltk>=3.8.0
scikit-learn>=1.3.0

# Dev/testing
pytest>=7.4.0
pytest-asyncio>=0.21.0
```

---

## PII Detection: Pattern-Based Implementation

When ML libraries (Presidio) are not available, use these patterns:

```python
import re
from dataclasses import dataclass
from typing import Optional

@dataclass
class PIIPattern:
    name: str
    regex: re.Pattern
    confidence: float
    requires_validation: bool = False

class PatternBasedPIIDetector:
    """
    Regex-based PII detection (no ML dependencies).
    """
    
    PATTERNS = [
        # Social Security Numbers (US)
        PIIPattern(
            name="SSN",
            regex=re.compile(r'\b\d{3}[-.]?\d{2}[-.]?\d{4}\b'),
            confidence=0.8,
            requires_validation=True
        ),
        
        # Credit Card Numbers (with Luhn check)
        PIIPattern(
            name="CREDIT_CARD",
            regex=re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b'),
            confidence=0.9,
            requires_validation=True
        ),
        
        # Email addresses
        PIIPattern(
            name="EMAIL",
            regex=re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            confidence=0.95
        ),
        
        # Phone numbers (US format)
        PIIPattern(
            name="PHONE",
            regex=re.compile(r'\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'),
            confidence=0.7,
            requires_validation=True
        ),
        
        # Account numbers (generic pattern - requires validation)
        PIIPattern(
            name="ACCOUNT_NUMBER",
            regex=re.compile(r'\b\d{8,17}\b'),
            confidence=0.3,
            requires_validation=True
        ),
        
        # Bank routing numbers (9 digits)
        PIIPattern(
            name="ROUTING_NUMBER",
            regex=re.compile(r'\b\d{9}\b'),
            confidence=0.4,
            requires_validation=True
        ),
    ]
    
    SAFE_EXAMPLES = [
        r'example@\w+\.com',
        r'test@\w+\.com',
        r'demo@\w+\.com',
        r'sample@\w+\.com',
        r'.*@example\..*',
        r'.*@test\..*',
    ]
    
    def __init__(self):
        self.safe_patterns = [re.compile(p) for p in self.SAFE_EXAMPLES]
    
    def is_safe_example(self, match: str) -> bool:
        """Check if match is a safe example/demo value."""
        return any(p.match(match) for p in self.safe_patterns)
    
    def validate_credit_card(self, card_number: str) -> bool:
        """Luhn algorithm validation."""
        digits = [int(d) for d in card_number if d.isdigit()]
        if len(digits) < 13 or len(digits) > 19:
            return False
        
        checksum = 0
        reverse_digits = digits[::-1]
        for i, d in enumerate(reverse_digits):
            if i % 2 == 1:
                d *= 2
                if d > 9:
                    d -= 9
            checksum += d
        return checksum % 10 == 0
    
    def scan(self, text: str) -> list[dict]:
        """Scan text for PII patterns."""
        findings = []
        
        for pattern in self.PATTERNS:
            for match in pattern.regex.finditer(text):
                value = match.group()
                
                # Skip safe examples
                if self.is_safe_example(value):
                    continue
                
                # Validate if required
                is_valid = True
                if pattern.requires_validation:
                    if pattern.name == "CREDIT_CARD":
                        is_valid = self.validate_credit_card(value)
                
                if is_valid:
                    findings.append({
                        "type": pattern.name,
                        "value": value,
                        "position": match.span(),
                        "confidence": pattern.confidence
                    })
        
        return findings
```

---

## Chunking: Token Count Estimation

```python
import tiktoken

def estimate_tokens(text: str, model: str = "cl100k_base") -> int:
    """
    Estimate token count for a text string.
    Uses tiktoken for accurate counting if available.
    """
    try:
        encoding = tiktoken.get_encoding(model)
        return len(encoding.encode(text))
    except:
        # Fallback: rough estimate (1 token ≈ 4 characters for English)
        return len(text) // 4

def chunk_fits_budget(text: str, max_tokens: int, buffer: int = 10) -> bool:
    """Check if text fits within token budget with safety buffer."""
    estimated = estimate_tokens(text)
    return estimated <= (max_tokens - buffer)
```

---

## Document Hashing for Versioning

```python
import hashlib
from pathlib import Path

def compute_file_hash(file_path: Path) -> str:
    """
    Compute SHA-256 hash of file content.
    Used for versioning and deduplication.
    """
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def compute_content_hash(content: str) -> str:
    """Compute hash of text content (for chunks)."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()
```

---

## Validation Checklist for Implementation

### Stage 1: Format Detection
- [ ] Detects PDF by magic bytes `%PDF`
- [ ] Detects ZIP/OOXML for DOCX
- [ ] Fallback to extension-based detection
- [ ] Rejects unsupported formats with clear error
- [ ] Detects text encoding (UTF-8, Latin-1)

### Stage 2: Content Extraction
- [ ] Extracts text from PDFs (pdfplumber)
- [ ] Preserves page numbers
- [ ] Extracts tables to markdown
- [ ] Extracts HTML with heading hierarchy
- [ ] Extracts DOCX with paragraph styles
- [ ] Handles empty documents gracefully

### Stage 3: Chunking
- [ ] Recursive splitter respects separators
- [ ] Overlap maintains context continuity
- [ ] FAQ chunker keeps Q+A together
- [ ] Table content transformed appropriately
- [ ] Chunk size within configured limits
- [ ] Unique chunk IDs generated

### Stage 4: PII Detection
- [ ] SSN pattern detection
- [ ] Credit card pattern + Luhn validation
- [ ] Email pattern detection
- [ ] Phone number pattern detection
- [ ] Safe examples excluded (example@, test@)
- [ ] High-risk PII triggers rejection
- [ ] Quarantine folder receives rejected docs

### Stage 5: Metadata
- [ ] Source file tracked
- [ ] Content hash computed
- [ ] Document type classified
- [ ] Product category auto-detected
- [ ] Timestamp recorded
- [ ] Section path preserved

### Stage 6: Embedding
- [ ] Model loads successfully
- [ ] Batch embedding implemented
- [ ] Vectors normalized if configured
- [ ] Error handling for failed batches

### Stage 7: Persistence
- [ ] FAISS index created
- [ ] Metadata mapping saved to JSON
- [ ] Document registry updated
- [ ] Incremental updates work
- [ ] Full rebuild works
- [ ] Index loads correctly on restart

### Stage 8: Validation
- [ ] Document count matches input
- [ ] Chunk count reasonable (>0 per doc)
- [ ] Embedding dimensions correct
- [ ] Search returns expected results
- [ ] No orphaned entries in metadata

### Integration
- [ ] End-to-end pipeline processes batch
- [ ] API endpoint accepts uploads
- [ ] CLI processes file/directory
- [ ] Status reporting works
- [ ] Error messages are informative

---

## Sample Test Documents

Create these test files for validation:

### test_policy.pdf
```
Banking Policy Document
Version 1.2 | Last Updated: 2024-01-15

1. Personal Loan Interest Rates

The current interest rates for personal loans are as follows:
- Excellent credit (750+): 6.99% APR
- Good credit (700-749): 8.99% APR  
- Fair credit (650-699): 12.99% APR

Rates are subject to change. No application fees.

2. Savings Account Options

Standard Savings: 0.50% APY, no minimum balance
High-Yield Savings: 4.25% APY, $10,000 minimum

Contact us at support@example-bank.com for details.
(all phone numbers in this doc are examples: 555-0100)
```

### test_faq.html
```html
<!DOCTYPE html>
<html>
<head><title>Banking FAQ</title></head>
<body>
<h1>Frequently Asked Questions</h1>

<h2>Loans</h2>

<p><strong>Q: What is the minimum credit score for a personal loan?</strong></p>
<p>A: We require a minimum credit score of 650 for personal loan applications. 
Higher scores qualify for better rates.</p>

<p><strong>Q: How long does loan approval take?</strong></p>
<p>A: Most applications receive a decision within 24-48 hours. 
Complex applications may take up to 5 business days.</p>

<h2>Savings</h2>

<p><strong>Q: Is there a monthly fee for savings accounts?</strong></p>
<p>A: Our Standard Savings has no monthly fee. High-Yield Savings requires 
a $10,000 minimum balance to avoid a $25 monthly fee.</p>

</body>
</html>
```

---

## Quick Start Commands

```bash
# Install dependencies
pip install -r requirements-ingestion.txt

# Download spaCy model (if using Presidio)
python -m spacy download en_core_web_lg

# Run ingestion on single file
python -m banking_rag.ingest /path/to/document.pdf

# Run batch ingestion
python -m banking_rag.ingest /path/to/documents/ --recursive

# Test ingestion (dry run—no changes)
python -m banking_rag.ingest /path/to/document.pdf --dry-run

# View ingestion status
python -m banking_rag.ingest --status

# Rebuild index from scratch
python -m banking_rag.ingest --rebuild
```

---

## Common Issues and Solutions

| Issue | Likely Cause | Solution |
|-------|--------------|----------|
| PDF extraction empty | Scanned image PDF | Use OCR (Tesseract) or reject file |
| FAISS index too large | Too many dimensions | Switch to IVF index or reduce vector precision |
| PII false positives | Aggressive patterns | Adjust confidence thresholds |
| Out of memory | Large files | Stream process page by page |
| Encoding errors | Non-UTF8 files | Use chardet or fallback to latin-1 |
| Chunk too large | Tables or lists | Split tables, respect structure |

---

## Performance Benchmarks (Reference)

On a typical development machine (4-core CPU, 16GB RAM):

| Task | Throughput | Memory |
|------|------------|--------|
| PDF extraction | 50 pages/sec | ~100MB |
| Text chunking | 1000 chunks/sec | ~50MB |
| PII scanning | 50 chunks/sec | ~200MB |
| Embedding (all-MiniLM) | 100 chunks/sec | ~500MB |
| FAISS update | 1000 vectors/sec | Index size dependent |

---

*End of Implementation Notes*

"""
Document Ingestion Pipeline for Banking RAG Chatbot.
8-stage pipeline for loading, processing, and indexing documents.
"""

import os
import json
import hashlib
import re
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
import logging

from .config import AppConfig, get_config
from .chunking import DocumentChunker
from .embeddings import get_embedding_model
from .vector_store import VectorStore, RetrievedChunk

logger = logging.getLogger(__name__)


@dataclass
class Document:
    """A document with content and metadata."""
    content: str
    metadata: Dict
    source: str
    document_id: str = ""


@dataclass
class IngestionResult:
    """Result of document ingestion."""
    documents: List[Document]
    chunks: int
    embeddings: int
    failed: int
    errors: List[str]


@dataclass
class PIIResult:
    """Result of PII detection."""
    has_pii: bool
    pii_types: List[str]
    redacted_content: Optional[str] = None
    action: str = "accept"  # "accept" or "reject"


class PIIDetector:
    """PII detection and redaction."""
    
    PATTERNS = {
        'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
        'credit_card': r'\b(?:\d{4}[- ]?){3}\d{4}\b',
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        'account_number': r'\b\d{8,20}\b',
    }
    
    REJECT_TYPES = ['ssn', 'account_number', 'credit_card']
    
    def __init__(self, reject_list: Optional[List[str]] = None):
        self.reject_list = reject_list or self.REJECT_TYPES
    
    def detect(self, text: str) -> PIIResult:
        """Detect PII in text."""
        found_types = []
        
        for pii_type, pattern in self.PATTERNS.items():
            if re.search(pattern, text):
                found_types.append(pii_type)
        
        return PIIResult(
            has_pii=len(found_types) > 0,
            pii_types=found_types,
            action="reject" if any(t in self.reject_list for t in found_types) else "accept"
        )
    
    def redact(self, text: str) -> str:
        """Redact PII from text."""
        redacted = text
        
        # Redact SSN
        redacted = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN_REDACTED]', redacted)
        # Redact credit cards
        redacted = re.sub(r'\b(?:\d{4}[- ]?){3}\d{4}\b', '[CARD_REDACTED]', redacted)
        # Redact emails
        redacted = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL_REDACTED]', redacted)
        # Redact phone numbers
        redacted = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE_REDACTED]', redacted)
        
        return redacted


class DocumentLoader:
    """Document loaders for various formats."""
    
    @staticmethod
    def from_text_file(path: str) -> Document:
        """Load from plain text file."""
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return Document(
            content=content,
            metadata={
                'source': path,
                'format': 'txt',
                'filename': os.path.basename(path)
            },
            source=path
        )
    
    @staticmethod
    def from_markdown(path: str) -> Document:
        """Load from Markdown file."""
        return DocumentLoader.from_text_file(path)
    
    @staticmethod
    def from_pdf(path: str) -> Document:
        """Load from PDF file."""
        try:
            import PyPDF2
            
            with open(path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                content = ""
                for page in reader.pages:
                    content += page.extract_text() + "\n\n"
            
            return Document(
                content=content,
                metadata={
                    'source': path,
                    'format': 'pdf',
                    'filename': os.path.basename(path),
                    'pages': len(reader.pages)
                },
                source=path
            )
        except ImportError:
            logger.warning("PyPDF2 not installed, PDF loading may fail")
            raise
    
    @staticmethod
    def from_html(path: str) -> Document:
        """Load from HTML file."""
        try:
            from bs4 import BeautifulSoup
            
            with open(path, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
                content = soup.get_text()
            
            return Document(
                content=content,
                metadata={
                    'source': path,
                    'format': 'html',
                    'filename': os.path.basename(path)
                },
                source=path
            )
        except ImportError:
            logger.warning("BeautifulSoup not installed, HTML loading may fail")
            raise


class DocumentIngestionPipeline:
    """
    8-stage document ingestion pipeline:
    1. Format Detection
    2. Content Extraction
    3. Chunking & Transformation
    4. PII Validation
    5. Metadata Enrichment
    6. Embedding Generation
    7. Persistence to FAISS
    8. Validation
    """
    
    def __init__(
        self,
        vector_store: VectorStore,
        config: Optional[AppConfig] = None,
        pii_detector: Optional[PIIDetector] = None
    ):
        """Initialize the ingestion pipeline."""
        self.config = config or get_config()
        self.vs_config = self.config.vector_store
        self.chunk_config = self.config.chunking
        
        self.vector_store = vector_store
        self.chunker = DocumentChunker(config)
        self.embedding_model = get_embedding_model(config=config)
        self.pii_detector = pii_detector or PIIDetector()
    
    def generate_document_id(self, content: str, source: str) -> str:
        """Generate a unique document ID."""
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        source_hash = hashlib.md5(source.encode()).hexdigest()[:8]
        return f"doc_{content_hash}_{source_hash}"
    
    def stage_1_format_detection(self, path: str) -> str:
        """Detect file format."""
        ext = Path(path).suffix.lower()
        
        format_map = {
            '.txt': 'text',
            '.md': 'markdown',
            '.pdf': 'pdf',
            '.html': 'html',
            '.docx': 'docx'
        }
        
        return format_map.get(ext, 'unknown')
    
    def stage_2_content_extraction(self, path: str, format_type: str) -> Document:
        """Extract content based on format."""
        extractors = {
            'text': DocumentLoader.from_text_file,
            'markdown': DocumentLoader.from_markdown,
            'pdf': DocumentLoader.from_pdf,
            'html': DocumentLoader.from_html,
            'docx': DocumentLoader.from_text_file  # Fallback
        }
        
        extractor = extractors.get(format_type)
        if not extractor:
            raise ValueError(f"Unsupported format: {format_type}")
        
        return extractor(path)
    
    def stage_3_chunking(self, document: Document) -> List[Document]:
        """Chunk the document."""
        chunking_result = self.chunker.chunk(document.content)
        
        chunk_docs = []
        for chunk in chunking_result.chunks:
            chunk_doc = Document(
                content=chunk.content,
                metadata={
                    **document.metadata,
                    'chunk_id': chunk.chunk_id,
                    'chunk_index': chunk.chunk_index,
                    'total_chunks': chunking_result.total_chunks,
                    'chunk_strategy': chunking_result.strategy
                },
                source=document.source
            )
            chunk_docs.append(chunk_doc)
        
        logger.info(f"Chunked {document.metadata.get('filename')} into {len(chunk_docs)} chunks")
        return chunk_docs
    
    def stage_4_pii_validation(self, chunks: List[Document]) -> List[Document]:
        """Validate chunks for PII."""
        valid_chunks = []
        
        for chunk in chunks:
            pii_result = self.pii_detector.detect(chunk.content)
            
            if pii_result.action == "reject":
                logger.warning(f"Chunk rejected due to PII: {chunk.metadata.get('chunk_id')}")
                # Store in quarantine folder instead of rejecting
                self._save_quarantined(chunk)
            else:
                if pii_result.has_pii and pii_result.redacted_content:
                    chunk.content = pii_result.redacted_content
                valid_chunks.append(chunk)
        
        logger.info(f"PII validation: {len(valid_chunks)} valid, {len(chunks) - len(valid_chunks)} quarantined")
        return valid_chunks
    
    def stage_5_metadata_enrichment(self, chunks: List[Document]) -> List[Document]:
        """Enrich chunk metadata."""
        for chunk in chunks:
            # Calculate token count
            chunk.metadata['token_count'] = len(chunk.content.split())
            
            # Add embedding model info
            chunk.metadata['embedding_model'] = self.config.embedding.model
            
            # Add ingestion timestamp
            chunk.metadata['ingested_at'] = str(self.config.embedding.model)
            
            # Add format info
            if 'format' not in chunk.metadata:
                chunk.metadata['format'] = 'text'
        
        return chunks
    
    def stage_6_embedding_generation(self, chunks: List[Document]) -> List[List[float]]:
        """Generate embeddings for chunks."""
        texts = [chunk.content for chunk in chunks]
        embeddings = self.embedding_model.generate_batch(texts)
        
        logger.info(f"Generated {len(embeddings)} embeddings")
        return embeddings
    
    def stage_7_persistence(self, chunks: List[Document], embeddings: List[List[float]], document_id: str) -> List[str]:
        """Persist chunks and embeddings to vector store."""
        metadatas = [chunk.metadata for chunk in chunks]
        
        chunk_ids = self.vector_store.add_chunks(
            embeddings=embeddings,
            contents=[c.content for c in chunks],
            metadatas=metadatas,
            document_id=document_id
        )
        
        logger.info(f"Persisted {len(chunk_ids)} chunks to vector store")
        return chunk_ids
    
    def stage_8_validation(self, chunks: List[Document], chunk_ids: List[str]) -> bool:
        """Validate ingestion result."""
        if len(chunks) != len(chunk_ids):
            logger.error(f"Chunk count mismatch: {len(chunks)} chunks vs {len(chunk_ids)} IDs")
            return False
        
        for chunk_id in chunk_ids:
            if not self.vector_store.get_chunk(chunk_id):
                logger.error(f"Chunk {chunk_id} not found in store")
                return False
        
        logger.info("Ingestion validation passed")
        return True
    
    def _save_quarantined(self, chunk: Document):
        """Save quarantined chunk to quarantine folder."""
        quarantine_dir = Path(self.config.data_dir) / "quarantine"
        quarantine_dir.mkdir(parents=True, exist_ok=True)
        
        chunk_id = chunk.metadata.get('chunk_id', 'unknown')
        path = quarantine_dir / f"quarantined_{chunk_id}.json"
        
        with open(path, 'w') as f:
            json.dump({
                'chunk_id': chunk_id,
                'content': chunk.content,
                'metadata': chunk.metadata,
                'pii_types': chunk.metadata.get('pii_types', [])
            }, f)
        
        logger.info(f"Quarantined chunk: {chunk_id}")
    
    def ingest_file(self, path: str) -> IngestionResult:
        """Ingest a single file through the pipeline."""
        documents = []
        chunks_count = 0
        embeddings_count = 0
        failed = 0
        errors = []
        
        try:
            # Stage 1: Format Detection
            format_type = self.stage_1_format_detection(path)
            
            if format_type == 'unknown':
                raise ValueError(f"Unknown file format: {path}")
            
            # Stage 2: Content Extraction
            document = self.stage_2_content_extraction(path, format_type)
            documents.append(document)
            
            # Stage 3: Chunking
            chunks = self.stage_3_chunking(document)
            
            # Stage 4: PII Validation
            chunks = self.stage_4_pii_validation(chunks)
            
            # Stage 5: Metadata Enrichment
            chunks = self.stage_5_metadata_enrichment(chunks)
            
            # Generate document ID
            doc_id = self.generate_document_id(document.content, document.source)
            
            # Store document metadata
            self.vector_store._REGISTRY[doc_id] = {
                'source': path,
                'format': format_type,
                'chunk_ids': [],
                **document.metadata
            }
            
            # Stage 6: Embedding Generation
            embeddings = self.stage_6_embedding_generation(chunks)
            embeddings_count += len(embeddings)
            
            # Stage 7: Persistence
            chunk_ids = self.stage_7_persistence(chunks, embeddings, doc_id)
            chunks_count += len(chunk_ids)
            
            # Stage 8: Validation
            self.stage_8_validation(chunks, chunk_ids)
            
        except Exception as e:
            logger.error(f"Failed to ingest {path}: {e}")
            errors.append(str(e))
            failed += 1
        
        return IngestionResult(
            documents=documents,
            chunks=chunks_count,
            embeddings=embeddings_count,
            failed=failed,
            errors=errors
        )
    
    def ingest_directory(self, directory: str) -> IngestionResult:
        """Ingest all documents in a directory."""
        total_result = IngestionResult(
            documents=[], chunks=0, embeddings=0, failed=0, errors=[]
        )
        
        supported_extensions = {'.txt', '.md', '.pdf', '.html'}
        
        for root, dirs, files in os.walk(directory):
            for filename in files:
                if Path(filename).suffix.lower() not in supported_extensions:
                    continue
                
                path = os.path.join(root, filename)
                result = self.ingest_file(path)
                
                total_result.documents.extend(result.documents)
                total_result.chunks += result.chunks
                total_result.embeddings += result.embeddings
                total_result.failed += result.failed
                total_result.errors.extend(result.errors)
        
        return total_result


def create_ingestion_pipeline(
    vector_store: VectorStore,
    config: Optional[AppConfig] = None
) -> DocumentIngestionPipeline:
    """Factory function to create ingestion pipeline."""
    return DocumentIngestionPipeline(vector_store, config)


if __name__ == '__main__':
    # Example usage
    from banking_rag.config import load_config
    from banking_rag.vector_store import VectorStore
    
    config = load_config()
    vector_store = VectorStore(config)
    pipeline = create_ingestion_pipeline(vector_store, config)
    
    # Ingest a sample file
    # result = pipeline.ingest_file("path/to/document.pdf")
    # print(f"Ingested {result.chunks} chunks, {result.embeddings} embeddings")

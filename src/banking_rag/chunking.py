"""
Document Chunking module for Banking RAG Chatbot.
Splits documents into semantically meaningful chunks with various strategies.
"""

import re
from typing import List, Dict, Optional
from dataclasses import dataclass
import logging

from .config import AppConfig, get_config

logger = logging.getLogger(__name__)


@dataclass
class Document:
    """A document chunk."""
    content: str
    metadata: Dict
    chunk_id: str
    chunk_index: int


@dataclass
class ChunkingResult:
    """Result of chunking operation."""
    chunks: List[Document]
    total_chunks: int
    total_tokens: int
    strategy: str


class DocumentChunker:
    """
    Document chunker supporting multiple strategies:
    - Recursive: Recursively split by paragraph, sentence, word, character
    - FAQ preserved: Split FAQs as single chunks
    - Table aware: Preserve table structures
    """
    
    def __init__(self, config: Optional[AppConfig] = None):
        """Initialize the chunker."""
        self.config = config or get_config()
        self.chunk_config = self.config.chunking
    
    def chunk_recursive(
        self,
        text: str,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ) -> List[Document]:
        """
        Recursively split text by paragraph, sentence, word, character.
        
        Args:
            text: Input text
            chunk_size: Maximum chunk size (overrides config)
            chunk_overlap: Chunk overlap (overrides config)
            
        Returns:
            List of Document chunks
        """
        chunk_size = chunk_size or self.chunk_config.chunk_size
        chunk_overlap = chunk_overlap or self.chunk_config.chunk_overlap
        
        # First split by paragraphs
        paragraphs = self._split_by_paragraphs(text)
        
        chunks = []
        current_chunk = ""
        chunk_index = 0
        
        for paragraph in paragraphs:
            if not paragraph.strip():
                continue
            
            # Check if paragraph fits in current chunk
            if len(current_chunk) + len(paragraph) <= chunk_size:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
            else:
                # Current chunk is full, save it
                if current_chunk:
                    chunks.append(self._create_document(current_chunk, chunk_index))
                    chunk_index += 1
                
                # Handle oversized paragraph by splitting further
                if len(paragraph) > chunk_size:
                    current_chunk = self._split_long_paragraph(
                        paragraph, chunk_size, chunk_overlap
                    )
                    chunks.extend(current_chunk)
                    chunk_index += len(current_chunk)
                    current_chunk = ""
                else:
                    current_chunk = paragraph
        
        # Don't forget the last chunk
        if current_chunk:
            chunks.append(self._create_document(current_chunk, chunk_index))
        
        return chunks
    
    def _split_by_paragraphs(self, text: str) -> List[str]:
        """Split text by paragraphs."""
        # Split on double newlines
        paragraphs = re.split(r'\n\s*\n', text)
        return [p.strip() for p in paragraphs if p.strip()]
    
    def _split_long_paragraph(
        self,
        paragraph: str,
        chunk_size: int,
        chunk_overlap: int
    ) -> List[Document]:
        """Split an oversized paragraph into multiple chunks."""
        # Split by sentences first
        sentences = re.split(r'(?<=[.!?])\s+', paragraph)
        
        chunks = []
        current_chunk = ""
        chunk_index = 0
        
        for sentence in sentences:
            if len(sentence) > chunk_size:
                # Very long sentence - split by words
                words = sentence.split()
                for word in words:
                    if len(current_chunk) + len(word) + 1 <= chunk_size:
                        if current_chunk:
                            current_chunk += " " + word
                        else:
                            current_chunk = word
                    else:
                        if current_chunk:
                            chunks.append(self._create_document(current_chunk, chunk_index))
                            chunk_index += 1
                            current_chunk = word
                        else:
                            current_chunk = word[:chunk_size]
                            chunks.append(self._create_document(current_chunk, chunk_index))
                            chunk_index += 1
                            current_chunk = word[chunk_size:]
            else:
                if len(current_chunk) + len(sentence) + 2 <= chunk_size:
                    if current_chunk:
                        current_chunk += " " + sentence
                    else:
                        current_chunk = sentence
                else:
                    if current_chunk:
                        chunks.append(self._create_document(current_chunk, chunk_index))
                        chunk_index += 1
                        # Add overlap
                        overlap_words = current_chunk.split()[-(chunk_overlap // 5):]
                        current_chunk = " ".join(overlap_words) + " " + sentence
                    else:
                        current_chunk = sentence
        
        if current_chunk:
            chunks.append(self._create_document(current_chunk, chunk_index))
        
        return chunks
    
    def _create_document(self, content: str, index: int) -> Document:
        """Create a Document object."""
        return Document(
            content=content,
            metadata={
                'chunk_type': 'recursive',
                'content_length': len(content)
            },
            chunk_id=f"chunk_{index}",
            chunk_index=index
        )
    
    def chunk_faq_preserved(
        self,
        faq_entries: List[Dict[str, str]],
        chunk_size: Optional[int] = None
    ) -> List[Document]:
        """
        Chunk FAQs, preserving question-answer pairs.
        
        Args:
            faq_entries: List of {'question': str, 'answer': str}
            chunk_size: Maximum chunk size (overrides config)
            
        Returns:
            List of Document chunks (each FAQ as single chunk)
        """
        chunk_size = chunk_size or self.chunk_config.chunk_size
        
        chunks = []
        for idx, entry in enumerate(faq_entries):
            question = entry.get('question', '')
            answer = entry.get('answer', '')
            
            # Combine Q&A
            content = f"Q: {question}\n\nA: {answer}"
            
            # If too long, use recursive chunking
            if len(content) > chunk_size:
                recursive_chunks = self.chunk_recursive(content)
                for rc in recursive_chunks:
                    rc.metadata['chunk_type'] = 'faq_preserved'
                    chunks.append(rc)
            else:
                chunks.append(Document(
                    content=content,
                    metadata={
                        'chunk_type': 'faq_preserved',
                        'question': question,
                        'answer': answer
                    },
                    chunk_id=f"faq_{idx}",
                    chunk_index=idx
                ))
        
        return chunks
    
    def chunk_table_aware(
        self,
        text: str,
        chunk_size: Optional[int] = None
    ) -> List[Document]:
        """
        Chunk text while preserving table structures.
        
        Args:
            text: Input text with potential tables
            chunk_size: Maximum chunk size (overrides config)
            
        Returns:
            List of Document chunks
        """
        chunk_size = chunk_size or self.chunk_config.chunk_size
        
        # Extract tables (simple pattern matching)
        tables = self._extract_tables(text)
        
        # Split text into sections
        sections = re.split(r'\n\n+', text)
        
        chunks = []
        current_chunk = ""
        chunk_index = 0
        
        for section in sections:
            # Check if section is a table
            if any(t in section for t in tables):
                # Preserve table as separate chunk
                if current_chunk:
                    chunks.append(self._create_document(current_chunk, chunk_index))
                    chunk_index += 1
                    current_chunk = ""
                
                chunks.append(Document(
                    content=section,
                    metadata={
                        'chunk_type': 'table',
                        'is_table': True
                    },
                    chunk_id=f"chunk_{chunk_index}",
                    chunk_index=chunk_index
                ))
                chunk_index += 1
            else:
                # Regular text
                if len(current_chunk) + len(section) + 2 <= chunk_size:
                    if current_chunk:
                        current_chunk += "\n\n" + section
                    else:
                        current_chunk = section
                else:
                    if current_chunk:
                        chunks.append(self._create_document(current_chunk, chunk_index))
                        chunk_index += 1
                    current_chunk = section
        
        if current_chunk:
            chunks.append(self._create_document(current_chunk, chunk_index))
        
        return chunks
    
    def _extract_tables(self, text: str) -> List[str]:
        """Extract table-like structures from text."""
        tables = []
        
        # Pattern for pipe tables (Markdown-style)
        table_pattern = r'\|.*\|(?:\n\|.*\|)+'
        matches = re.findall(table_pattern, text, re.MULTILINE)
        tables.extend(matches)
        
        # Pattern for ASCII tables
        ascii_pattern = r'\+[-+]+\+(?:\n\|[^|]+\|)+\+[-+]+\+'
        matches = re.findall(ascii_pattern, text)
        tables.extend(matches)
        
        return tables
    
    def chunk(self, text: str, strategy: Optional[str] = None) -> ChunkingResult:
        """
        Chunk text using specified strategy.
        
        Args:
            text: Input text
            strategy: Chunking strategy (overrides config)
            
        Returns:
            ChunkingResult with chunks and metadata
        """
        strategy = strategy or self.chunk_config.strategy
        
        if strategy == 'recursive':
            chunks = self.chunk_recursive(text)
        elif strategy == 'faq_preserved':
            # For FAQs, expected format is question-answer pairs
            faqs = self._parse_faq_format(text)
            chunks = self.chunk_faq_preserved(faqs)
        elif strategy == 'table_aware':
            chunks = self.chunk_table_aware(text)
        else:
            chunks = self.chunk_recursive(text)
        
        total_tokens = sum(len(c.content.split()) for c in chunks)
        
        return ChunkingResult(
            chunks=chunks,
            total_chunks=len(chunks),
            total_tokens=total_tokens,
            strategy=strategy
        )
    
    def _parse_faq_format(self, text: str) -> List[Dict[str, str]]:
        """Parse FAQ format text."""
        faqs = []
        
        # Pattern: "Q: question\nA: answer" or "Question: ... Answer: ..."
        patterns = [
            r'Q:\s*(.+?)\s*\n\s*A:\s*(.+?)(?=\n\s*Q:|\n\s*$)',
            r'[Qq]uestion:\s*(.+?)\s*\n\s*[Aa]nswer:\s*(.+?)(?=\n\s*[Qq]uestion:|\n\s*$)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for question, answer in matches:
                faqs.append({
                    'question': question.strip(),
                    'answer': answer.strip()
                })
        
        return faqs


class MockDocumentChunker(DocumentChunker):
    """Mock document chunker for testing."""
    
    def chunk_recursive(self, text: str, chunk_size=None, chunk_overlap=None):
        # Return single chunk for testing
        return [Document(
            content=text[:500],
            metadata={'chunk_type': 'mock', 'content_length': len(text[:500])},
            chunk_id="chunk_0",
            chunk_index=0
        )]
    
    def chunk_faq_preserved(self, faq_entries, chunk_size=None):
        chunks = []
        for idx, entry in enumerate(faq_entries):
            chunks.append(Document(
                content=f"Q: {entry.get('question', '')}\n\nA: {entry.get('answer', '')}",
                metadata={'chunk_type': 'faq_preserved', 'chunk_index': idx},
                chunk_id=f"faq_{idx}",
                chunk_index=idx
            ))
        return chunks

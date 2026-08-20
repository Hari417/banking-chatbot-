"""
FAISS Vector Database Interface for Banking RAG Chatbot.
Handles index creation, persistence, and vector similarity search.
"""

import os
import json
import pickle
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import logging

from .config import AppConfig, get_config

logger = logging.getLogger(__name__)


def _import_faiss():
    """Lazy import of faiss and numpy."""
    try:
        import faiss
        import numpy as np
        return faiss, np
    except ImportError:
        raise ImportError(
            "faiss-cpu is required but not installed. "
            "Install with: pip install faiss-cpu"
        )


@dataclass
class RetrievedChunk:
    """A retrieved chunk from the vector store."""
    content: str
    score: float
    metadata: Dict
    chunk_id: str


class VectorStore:
    """
    Vector store using FAISS for local vector similarity search.
    Supports persistence to disk.
    """
    
    def __init__(self, config: Optional[AppConfig] = None):
        """Initialize the vector store."""
        self.config = config or get_config()
        self.vs_config = self.config.vector_store
        
        # Create data directories
        self._ensure_directories()
        
        # Initialize FAISS index
        self.index = None
        self.metadata: Dict[str, Dict] = {}  # chunk_id -> metadata
        self._REGISTRY: Dict[str, Dict] = {}  # document_id -> document info
        self.index_counter = 0  # Track FAISS index size
        self._load_or_create_index()
    
    def _ensure_directories(self):
        """Ensure data directories exist."""
        for path in [
            os.path.dirname(self.vs_config.persist_path),
            os.path.dirname(self.vs_config.metadata_path),
            os.path.dirname(self.vs_config.registry_path)
        ]:
            Path(path).mkdir(parents=True, exist_ok=True)
    
    def _load_or_create_index(self):
        """Load existing index or create new one."""
        persist_path = self.vs_config.persist_path
        
        self.metadata = {}
        self._REGISTRY = {}
        
        if os.path.exists(persist_path) and os.path.exists(self.vs_config.metadata_path):
            self._load_index(persist_path)
            self._load_metadata()
            self._load_registry()
            logger.info(f"Loaded existing FAISS index from {persist_path}")
        else:
            self._create_index()
            logger.info("Created new FAISS index")
    
    def _create_index(self):
        """Create a new FAISS index."""
        faiss, np = _import_faiss()
        dimensions = self.config.embedding.dimensions
        
        if self.vs_config.index_type == 'IndexFlatIP':
            self.index = faiss.IndexFlatIP(dimensions)
        elif self.vs_config.index_type == 'IndexIVFFlat':
            nlist = self.vs_config.nlist
            quantizer = faiss.IndexFlatIP(dimensions)
            self.index = faiss.IndexIVFFlat(quantizer, dimensions, nlist)
            self.index.nprobe = min(10, nlist)
        else:
            raise ValueError(f"Unknown index type: {self.vs_config.index_type}")
    
    def _load_index(self, path: str):
        """Load FAISS index from disk."""
        faiss, np = _import_faiss()
        self.index = faiss.read_index(path)
    
    def _save_index(self, path: str):
        """Save FAISS index to disk."""
        faiss, np = _import_faiss()
        faiss.write_index(self.index, path)
    
    def _load_metadata(self):
        """Load metadata from disk."""
        try:
            with open(self.vs_config.metadata_path, 'r') as f:
                self.metadata = json.load(f)
        except FileNotFoundError:
            self.metadata = {}
    
    def _save_metadata(self):
        """Save metadata to disk."""
        with open(self.vs_config.metadata_path, 'w') as f:
            json.dump(self.metadata, f, indent=2, default=str)
    
    def _load_registry(self):
        """Load document registry from disk."""
        try:
            with open(self.vs_config.registry_path, 'r') as f:
                self._REGISTRY = json.load(f)
        except FileNotFoundError:
            self._REGISTRY = {}
    
    def _save_registry(self):
        """Save document registry to disk."""
        with open(self.vs_config.registry_path, 'w') as f:
            json.dump(self._REGISTRY, f, indent=2, default=str)
    
    def add_chunks(
        self,
        embeddings: List[List[float]],
        contents: List[str],
        metadatas: List[Dict],
        document_id: Optional[str] = None
    ) -> List[str]:
        """
        Add chunks to the vector store.
        
        Args:
            embeddings: List of embedding vectors
            contents: List of chunk contents
            metadatas: List of metadata dicts
            document_id: Optional parent document ID
            
        Returns:
            List of created chunk IDs
        """
        if len(embeddings) != len(contents) or len(embeddings) != len(metadatas):
            raise ValueError("Embeddings, contents, and metadatas must have same length")
        
        chunk_ids = []
        faiss, np = _import_faiss()
        numpy_embeddings = np.array(embeddings, dtype=np.float32)
        
        # Add to FAISS index
        start_idx = self.index.ntotal
        self.index.add(numpy_embeddings)
        
        # Store metadata
        for i, (content, metadata) in enumerate(zip(contents, metadatas)):
            chunk_id = f"chunk_{start_idx + i}"
            chunk_ids.append(chunk_id)
            
            self.metadata[chunk_id] = {
                'content': content,
                'chunk_id': chunk_id,
                'index': start_idx + i,  # Store FAISS index
                **metadata
            }
        
        # Update metadata and persist
        self._save_metadata()
        self._save_registry()
        self._save_index(self.vs_config.persist_path)
        
        # Update document registry if document_id provided
        if document_id:
            if document_id not in self._REGISTRY:
                self._REGISTRY[document_id] = {
                    'chunk_ids': [],
                    **metadatas[0]  # Copy parent metadata
                }
            self._REGISTRY[document_id]['chunk_ids'].extend(chunk_ids)
        
        # Persist
        self._save_metadata()
        self._save_registry()
        self._save_index(self.vs_config.persist_path)
        
        logger.info(f"Added {len(chunk_ids)} chunks to vector store")
        return chunk_ids
    
    def search(
        self,
        query_embedding: List[float],
        k: int,
        filter_metadata: Optional[Dict] = None
    ) -> List[RetrievedChunk]:
        """
        Search for similar chunks.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results
            filter_metadata: Optional metadata filter
            
        Returns:
            List of retrieved chunks with scores
        """
        faiss, np = _import_faiss()
        query_array = np.array([query_embedding], dtype=np.float32)
        scores, indices = self.index.search(query_array, k)
        
        results = []
        for i in range(len(indices[0])):
            idx = int(indices[0][i])
            if idx < 0:  # -1 indicates no retrieval
                continue
            score = float(scores[0][i])
            
            # Find the chunk_id for this index
            chunk_id = None
            for cid, meta in self.metadata.items():
                chunk_id_parts = cid.split('_')
                if len(chunk_id_parts) == 2 and chunk_id_parts[0] == 'chunk':
                    try:
                        chunk_index = int(chunk_id_parts[1])
                        if chunk_index == idx:
                            chunk_id = cid
                            break
                    except ValueError:
                        continue
            
            if chunk_id and chunk_id in self.metadata:
                # Apply filter if provided
                if filter_metadata:
                    if not self._matches_filter(self.metadata[chunk_id], filter_metadata):
                        continue
                
                results.append(RetrievedChunk(
                    content=self.metadata[chunk_id]['content'],
                    score=score,
                    metadata=self.metadata[chunk_id],
                    chunk_id=chunk_id
                ))
        
        # Re-rank by score descending
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:k]
    
    def _matches_filter(self, metadata: Dict, filter_metadata: Dict) -> bool:
        """Check if metadata matches filter criteria."""
        for key, value in filter_metadata.items():
            if metadata.get(key) != value:
                return False
        return True
    
    def delete_chunk(self, chunk_id: str) -> bool:
        """Delete a chunk by ID."""
        if chunk_id not in self.metadata:
            return False
        
        # Simple deletion - rebuild index without the chunk
        # This is inefficient for large indices but works for prototype
        self.metadata.pop(chunk_id, None)
        self._save_metadata()
        
        logger.info(f"Deleted chunk {chunk_id}")
        return True
    
    def get_chunk(self, chunk_id: str) -> Optional[Dict]:
        """Get a chunk's metadata by ID."""
        return self.metadata.get(chunk_id)
    
    def get_all_chunks(self) -> List[Dict]:
        """Get all chunks."""
        return list(self.metadata.values())
    
    def get_document_chunks(self, document_id: str) -> List[str]:
        """Get all chunk IDs for a document."""
        doc = self._REGISTRY.get(document_id)
        if doc:
            return doc.get('chunk_ids', [])
        return []
    
    def count(self) -> int:
        """Return number of stored chunks."""
        return len(self.metadata)
    
    def clear(self):
        """Clear all data from the vector store."""
        self.metadata = {}
        self._REGISTRY = {}
        self._create_index()
        self._save_metadata()
        self._save_registry()
        self._save_index(self.vs_config.persist_path)
        logger.info("Vector store cleared")


class MockVectorStore:
    """Mock vector store for testing."""
    
    def __init__(self, config: Optional[AppConfig] = None):
        self.config = config or get_config()
        self.vs_config = self.config.vector_store
        self.metadata = {}
        self._REGISTRY = {}
        self.index_type = 'mock'
    
    def add_chunks(self, embeddings, contents, metadatas, document_id=None):
        chunk_ids = []
        for i, (content, metadata) in enumerate(zip(contents, metadatas)):
            chunk_id = f"chunk_{len(self.metadata) + i}"
            chunk_ids.append(chunk_id)
            self.metadata[chunk_id] = {
                'content': content,
                'chunk_id': chunk_id,
                **metadata
            }
        return chunk_ids
    
    def search(self, query_embedding, k, filter_metadata=None):
        # Return mock results
        results = []
        for chunk_id, metadata in list(self.metadata.items())[:k]:
            results.append(RetrievedChunk(
                content=metadata['content'],
                score=0.5,
                metadata=metadata,
                chunk_id=chunk_id
            ))
        return results
    
    def count(self):
        return len(self.metadata)

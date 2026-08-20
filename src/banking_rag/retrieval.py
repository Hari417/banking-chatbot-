"""
Retrieval Engine module for Banking RAG Chatbot.
Implements hybrid retrieval (dense + sparse) with reranking.
"""

import os
import heapq
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
import logging

from .config import AppConfig, get_config
from .vector_store import VectorStore, RetrievedChunk

logger = logging.getLogger(__name__)


@dataclass
class RetrievedDocument:
    """A retrieved document from hybrid retrieval."""
    content: str
    dense_score: float
    sparse_score: float
    combined_score: float
    metadata: Dict
    chunk_id: str


class HybridRetriever:
    """
    Hybrid retriever combining dense (vector) and sparse (BM25) retrieval.
    Uses Reciprocal Rank Fusion (RRF) to combine scores.
    """
    
    def __init__(
        self,
        vector_store: VectorStore,
        config: Optional[AppConfig] = None
    ):
        """Initialize the hybrid retriever."""
        self.config = config or get_config()
        self.retrieval_config = self.config.retrieval
        self.vector_store = vector_store
        
        # Sparse retrieval (BM25) - will be initialized if available
        self._bm25 = None
        self._initialize_bm25()
    
    def _initialize_bm25(self):
        """Initialize BM25 sparse retriever if available."""
        try:
            from rank_bm25 import BM25Okapi
            self._bm25 = None  # Initialize as None
            self._bm25_ready = False
        except ImportError:
            logger.warning("rank-bm25 not installed, using dense-only retrieval")
            self._bm25 = None
            self._bm25_ready = False
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization."""
        return text.lower().split()
    
    def _update_bm25_index(self, documents: List[str]):
        """Update BM25 index with new documents."""
        if self._bm25 is None or not documents:  # Check for empty documents
            return
        
        try:
            from rank_bm25 import BM25Okapi
            tokenized_docs = [self._tokenize(doc) for doc in documents]
            self._bm25 = BM25Okapi(tokenized_docs)
            self._bm25_ready = True
        except Exception as e:
            logger.warning(f"Failed to initialize BM25: {e}")
            self._bm25 = None
            self._bm25_ready = False
    
    def _sparse_search(self, query: str, k: int) -> List[Tuple[int, float]]:
        """Search using sparse (BM25) retrieval."""
        if not self._bm25_ready:
            # Fallback to empty results
            return []
        
        try:
            tokenized_query = self._tokenize(query)
            scores = self._bm25.get_scores(tokenized_query)
            top_indices = heapq.nlargest(k, range(len(scores)), key=lambda i: scores[i])
            return [(i, scores[i]) for i in top_indices if scores[i] > 0]
        except Exception as e:
            logger.warning(f"BM25 search failed: {e}")
            return []
    
    def _dense_search(self, query_embedding: List[float], k: int, filter_metadata: Optional[Dict] = None) -> List[RetrievedChunk]:
        """Search using dense (vector) retrieval."""
        return self.vector_store.search(query_embedding, k)
    
    def _reciprocal_rank_fusion(
        self,
        dense_results: List[RetrievedChunk],
        sparse_results: List[Tuple[int, float]],
        dense_docs: List[str]
    ) -> List[RetrievedDocument]:
        """
        Combine dense and sparse results using Reciprocal Rank Fusion (RRF).
        
        RRF score = 1/(k + dense_rank) + 1/(k + sparse_rank)
        where k is a constant (usually 60).
        """
        k = 60
        
        # Build rank maps
        dense_rank_map = {chunk.chunk_id: i for i, chunk in enumerate(dense_results)}
        sparse_rank_map = {dense_docs[doc_idx]: i for i, (doc_idx, _) in enumerate(sparse_results)}
        
        # Get all unique chunk IDs
        all_ids = set(dense_rank_map.keys()) | set(sparse_rank_map.keys())
        
        # Compute RRF scores
        fused_results = []
        for chunk_id in all_ids:
            dense_rank = dense_rank_map.get(chunk_id, float('inf'))
            sparse_rank = sparse_rank_map.get(chunk_id, float('inf'))
            
            dense_score = 1.0 / (k + dense_rank) if dense_rank != float('inf') else 0
            sparse_score = 1.0 / (k + sparse_rank) if sparse_rank != float('inf') else 0
            combined_score = dense_score + sparse_score
            
            if chunk_id in dense_rank_map:
                chunk = dense_results[dense_rank_map[chunk_id]]
                fused_results.append(RetrievedDocument(
                    content=chunk.content,
                    dense_score=chunk.score,
                    sparse_score=sparse_score,
                    combined_score=combined_score,
                    metadata=chunk.metadata,
                    chunk_id=chunk_id
                ))
        
        # Sort by combined score descending
        fused_results.sort(key=lambda x: x.combined_score, reverse=True)
        return fused_results[:self.retrieval_config.final_k]
    
    def retrieve(
        self,
        query: str,
        query_embedding: List[float],
        k: Optional[int] = None,
        filter_metadata: Optional[Dict] = None
    ) -> List[RetrievedDocument]:
        """
        Retrieve relevant chunks using hybrid search.
        
        Args:
            query: Raw query text
            query_embedding: Query embedding
            k: Number of dense results (overrides config)
            filter_metadata: Optional metadata filter
            
        Returns:
            List of RetrievedDocument objects
        """
        k = k or self.retrieval_config.dense_k
        
        # Dense search
        dense_results = self._dense_search(query_embedding, k, filter_metadata)
        
        if not dense_results:
            return []
        
        # Get documents for sparse retrieval
        dense_docs = [chunk.content for chunk in dense_results]
        
        # Update BM25 index if needed
        if self._bm25 and not self._bm25_ready:
            self._update_bm25_index(dense_docs)
        
        # Sparse search
        sparse_results = self._sparse_search(query, k)
        
        # RRF fusion
        fused_results = self._score_fusion(
            dense_results, sparse_results, dense_docs
        )
        
        return fused_results
    
    def _score_fusion(
        self,
        dense_results: List[RetrievedChunk],
        sparse_results: List[Tuple[int, float]],
        dense_docs: List[str]
    ) -> List[RetrievedDocument]:
        """
        Fuse dense and sparse scores using normalized weighting.
        
        Args:
            dense_results: Dense search results
            sparse_results: Sparse search results
            dense_docs: List of dense document texts
            
        Returns:
            Fused retrieval results
        """
        # Normalize scores
        if not dense_results:
            return []
        
        dense_scores = [c.score for c in dense_results]
        max_dense = max(dense_scores) if dense_scores else 1.0
        min_dense = min(dense_scores) if dense_scores else 0.0
        dense_range = max_dense - min_dense if max_dense != min_dense else 1.0
        
        normalized_dense = [
            (c.score - min_dense) / dense_range for c in dense_results
        ]
        
        # Build sparse score map
        sparse_scores = {}
        for doc_idx, score in sparse_results:
            if doc_idx < len(dense_docs):
                sparse_scores[dense_docs[doc_idx]] = score
        
        # Normalize sparse scores
        sparse_values = list(sparse_scores.values()) if sparse_scores else [0]
        max_sparse = max(sparse_values) if sparse_values else 0
        min_sparse = min(sparse_values) if sparse_values else 0
        sparse_range = max_sparse - min_sparse if max_sparse != min_sparse else 1
        
        # Combine scores
        fused_results = []
        for i, chunk in enumerate(dense_results):
            dense_norm = normalized_dense[i]
            sparse_norm = (sparse_scores.get(chunk.content, 0) - min_sparse) / sparse_range
            
            # Weighted combination (configurable)
            weight_dense = 0.7
            weight_sparse = 0.3
            combined = weight_dense * dense_norm + weight_sparse * sparse_norm
            
            fused_results.append(RetrievedDocument(
                content=chunk.content,
                dense_score=chunk.score,
                sparse_score=sparse_scores.get(chunk.content, 0),
                combined_score=combined,
                metadata=chunk.metadata,
                chunk_id=chunk.chunk_id
            ))
        
        # Sort by combined score
        fused_results.sort(key=lambda x: x.combined_score, reverse=True)
        return fused_results[:self.retrieval_config.final_k]


class MockHybridRetriever(HybridRetriever):
    """Mock hybrid retriever for testing."""
    
    def _dense_search(self, query_embedding, k, filter_metadata=None):
        # Return mock results
        return [
            RetrievedChunk(
                content="This is a mock retrieved document.",
                score=0.8,
                metadata={'source': 'mock'},
                chunk_id="chunk_0"
            )
        ]
    
    def retrieve(self, query, query_embedding, k=None, filter_metadata=None):
        return [
            RetrievedDocument(
                content="This is a mock retrieved document.",
                dense_score=0.8,
                sparse_score=0.5,
                combined_score=0.65,
                metadata={'source': 'mock'},
                chunk_id="chunk_0"
            )
        ]


def get_retriever(
    vector_store: VectorStore,
    config: Optional[AppConfig] = None,
    mock: bool = False
) -> HybridRetriever:
    """
    Factory function to get hybrid retriever.
    
    Args:
        vector_store: VectorStore instance
        config: Configuration instance
        mock: Whether to use mock retriever
        
    Returns:
        HybridRetriever instance
    """
    if mock:
        return MockHybridRetriever(vector_store, config)
    return HybridRetriever(vector_store, config)

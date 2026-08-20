"""
Banking RAG Chatbot - Core Package
A RAG-based chatbot for banking FAQ support with local-first architecture.
"""

from .config import AppConfig, get_config, load_config, reload_config
from .llm import LLMClient, get_llm_client
from .embeddings import EmbeddingModel, get_embedding_model
from .vector_store import VectorStore
from .retrieval import HybridRetriever, get_retriever
from .rag_workflow import RAGWorkflow, get_rag_workflow

def chunking():
    """Lazy import for chunking module to avoid circular dependencies."""
    from .chunking import DocumentChunker
    return DocumentChunker

def ingestion():
    """Lazy import for ingestion module to avoid circular dependencies."""
    from .ingestion import DocumentIngestionPipeline
    return DocumentIngestionPipeline

__all__ = [
    'AppConfig', 'get_config', 'load_config', 'reload_config',
    'LLMClient', 'get_llm_client',
    'EmbeddingModel', 'get_embedding_model',
    'VectorStore',
    'HybridRetriever', 'get_retriever',
    'RAGWorkflow', 'get_rag_workflow',
    'chunking', 'ingestion',
]
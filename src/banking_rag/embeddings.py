"""
Embedding Generation module for Banking RAG Chatbot.
Generates embeddings for text chunks using local or API models.
"""

import os
import requests
from typing import List, Dict, Optional
from dataclasses import dataclass
import numpy as np
import logging

from .config import AppConfig, get_config

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingResult:
    """Result of embedding generation."""
    embeddings: List[List[float]]
    text: str
    model: str
    tokens_used: int


class EmbeddingModel:
    """
    Embedding model supporting multiple providers:
    - Sentence Transformers (local)
    - OpenAI embedding models
    - OpenAI-compatible embedding endpoints
    """
    
    def __init__(self, config: Optional[AppConfig] = None):
        """Initialize the embedding model."""
        self.config = config or get_config()
        self.em_config = self.config.embedding
        
        # Initialize based on provider
        self.provider = self.em_config.provider
        self._model = None
        
        if self.provider == 'local':
            self._load_local_model()
        elif self.provider in ['openai', 'openai_compatible']:
            logger.info(f"Using {self.provider} embedding API")
        else:
            raise ValueError(f"Unsupported embedding provider: {self.provider}")
    
    def _load_local_model(self):
        """Load local sentence-transformers model."""
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.em_config.model)
            logger.info(f"Loaded local embedding model: {self.em_config.model}")
        except ImportError as e:
            logger.error(f"sentence-transformers not installed: {e}")
            raise
    
    def _get_openai_embedding(self, text: str) -> List[float]:
        """Get embedding from OpenAI API."""
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f"Bearer {os.environ.get(self.em_config.api_key_env, '')}"
        }
        
        payload = {
            'model': self.em_config.model,
            'input': text
        }
        
        try:
            response = requests.post(
                url=f"{self.em_config.api_base}/embeddings",
                headers=headers,
                json=payload,
                timeout=self.em_config.timeout
            )
            response.raise_for_status()
            data = response.json()
            return data['data'][0]['embedding']
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenAI embedding API request failed: {e}")
            raise
    
    def _get_openai_compatible_embedding(self, text: str) -> List[float]:
        """Get embedding from OpenAI-compatible endpoint."""
        api_key = os.environ.get(self.em_config.api_key_env)
        headers = {'Content-Type': 'application/json'}
        if api_key:
            headers['Authorization'] = f"Bearer {api_key}"
        
        payload = {
            'model': self.em_config.model,
            'input': text
        }
        
        try:
            response = requests.post(
                url=f"{self.em_config.api_base}/embeddings",
                headers=headers,
                json=payload,
                timeout=self.em_config.timeout
            )
            response.raise_for_status()
            data = response.json()
            return data['data'][0]['embedding']
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenAI-compatible embedding API request failed: {e}")
            raise
    
    def _generate_local_embedding(self, text: str) -> List[float]:
        """Generate embedding using local model."""
        if self._model is None:
            raise RuntimeError("Local model not loaded")
        
        embedding = self._model.encode(text).tolist()
        return embedding
    
    def generate(self, text: str) -> EmbeddingResult:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text
            
        Returns:
            EmbeddingResult with embeddings and metadata
        """
        if self.provider == 'local':
            embedding = self._generate_local_embedding(text)
        elif self.provider == 'openai':
            embedding = self._get_openai_embedding(text)
        elif self.provider == 'openai_compatible':
            embedding = self._get_openai_compatible_embedding(text)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
        
        return EmbeddingResult(
            embeddings=[embedding],
            text=text,
            model=self.em_config.model,
            tokens_used=len(text) // 4  # Approximate token count
        )
    
    def generate_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a batch of texts.
        
        Args:
            texts: List of input texts
            
        Returns:
            List of embedding vectors
        """
        if self.provider == 'local':
            if self._model is None:
                raise RuntimeError("Local model not loaded")
            
            # Process in batches
            embeddings = []
            for i in range(0, len(texts), self.em_config.batch_size):
                batch = texts[i:i + self.em_config.batch_size]
                batch_embeddings = self._model.encode(
                    batch,
                    convert_to_tensor=False,
                    show_progress_bar=False
                )
                embeddings.extend(batch_embeddings.tolist())
            
            return embeddings
        
        elif self.provider == 'openai':
            # OpenAI supports batching
            embeddings = []
            for text in texts:
                embedding = self._get_openai_embedding(text)
                embeddings.append(embedding)
            return embeddings
        
        elif self.provider == 'openai_compatible':
            embeddings = []
            for text in texts:
                embedding = self._get_openai_compatible_embedding(text)
                embeddings.append(embedding)
            return embeddings
        
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
    
    def get_dimension(self) -> int:
        """Get embedding dimension."""
        if self.provider == 'local' and self._model:
            return self._model.get_sentence_embedding_dimension()
        return self.em_config.dimensions


class MockEmbeddingModel(EmbeddingModel):
    """Mock embedding model for testing."""
    
    def __init__(self, config: Optional[AppConfig] = None):
        self.config = config or get_config()
        self.em_config = self.config.embedding
    
    def generate(self, text: str) -> EmbeddingResult:
        # Return mock embeddings
        mock_embedding = [0.1] * self.em_config.dimensions
        return EmbeddingResult(
            embeddings=[mock_embedding],
            text=text,
            model='mock_embedding_model',
            tokens_used=len(text)
        )
    
    def generate_batch(self, texts: List[str]) -> List[List[float]]:
        return [[0.1] * self.em_config.dimensions for _ in texts]
    
    def get_dimension(self) -> int:
        return self.em_config.dimensions


def get_embedding_model(mock: bool = False, config: Optional[AppConfig] = None) -> EmbeddingModel:
    """
    Factory function to get embedding model.
    
    Args:
        mock: Whether to use mock model for testing
        config: Configuration instance (uses global if not provided)
        
    Returns:
        EmbeddingModel or MockEmbeddingModel instance
    """
    if mock:
        return MockEmbeddingModel(config)
    return EmbeddingModel(config)

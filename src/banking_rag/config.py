"""
Configuration module for Banking RAG Chatbot.
Handles loading, validation, and access to configuration settings.
"""

import os
import yaml
from typing import Any, Dict, Optional
from pathlib import Path
from dataclasses import dataclass, field
from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    """LLM provider configuration."""
    provider: str = Field(default="openai")
    model: str = Field(default="gpt-4o-mini")
    api_base: str = Field(default="https://api.openai.com/v1")
    api_key_env: str = Field(default="OPENAI_API_KEY")
    ollama_base_url: str = Field(default="http://localhost:11434")
    ollama_model: str = Field(default="llama3")
    temperature: float = Field(default=0.7)
    max_tokens: int = Field(default=1000)
    timeout: int = Field(default=30)

    def get_api_key(self) -> Optional[str]:
        """Get API key from environment or return None."""
        return os.environ.get(self.api_key_env)


class EmbeddingConfig(BaseModel):
    """Embedding model configuration."""
    model: str = Field(default="all-MiniLM-L6-v2")
    dimensions: int = Field(default=384)
    provider: str = Field(default="local")
    api_base: str = Field(default="https://api.openai.com/v1/embeddings")
    api_key_env: str = Field(default="OPENAI_API_KEY")
    batch_size: int = Field(default=32)
    timeout: int = Field(default=60)


class VectorStoreConfig(BaseModel):
    """FAISS vector store configuration."""
    index_type: str = Field(default="IndexFlatIP")
    nlist: int = Field(default=100)
    persist_path: str = Field(default="./data/index/faiss.index")
    metadata_path: str = Field(default="./data/index/metadata.json")
    registry_path: str = Field(default="./data/index/document_registry.json")


class RetrievalConfig(BaseModel):
    """Retrieval engine configuration."""
    dense_k: int = Field(default=10)
    sparse_k: int = Field(default=10)
    final_k: int = Field(default=5)
    score_threshold: float = Field(default=0.5)
    rerank_enabled: bool = Field(default=True)
    rerank_model: str = Field(default="cross-encoder/ms-marco-MiniLM-L-6-v2")


class SecurityConfig(BaseModel):
    """Security layer configuration."""
    rate_limit_enabled: bool = Field(default=True)
    rate_limit_requests: int = Field(default=10)
    rate_limit_window: int = Field(default=60)
    pii_detection_enabled: bool = Field(default=True)
    input_guard_enabled: bool = Field(default=True)
    prompt_injection_check_enabled: bool = Field(default=True)


class ChunkingConfig(BaseModel):
    """Document chunking configuration."""
    chunk_size: int = Field(default=512)
    chunk_overlap: int = Field(default=50)
    strategy: str = Field(default="recursive")


class SessionConfig(BaseModel):
    """Session management configuration."""
    memory_limit: int = Field(default=100)
    ttl_minutes: int = Field(default=30)
    persistence: bool = Field(default=False)


class FeatureConfig(BaseModel):
    """Feature flags."""
    enable_transactions: bool = Field(default=False)
    enable_premium_reranker: bool = Field(default=False)


@dataclass
class AppConfig:
    """Main application configuration."""
    # System settings
    debug: bool = False
    log_level: str = "INFO"
    data_dir: str = "./data"
    cache_dir: str = "./cache"
    
    # Sub-configurations
    llm: LLMConfig = field(default_factory=LLMConfig)
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    vector_store: VectorStoreConfig = field(default_factory=VectorStoreConfig)
    retrieval: RetrievalConfig = field(default_factory=RetrievalConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    chunking: ChunkingConfig = field(default_factory=ChunkingConfig)
    session: SessionConfig = field(default_factory=SessionConfig)
    features: FeatureConfig = field(default_factory=FeatureConfig)

    # paths
    persist_path: str = field(init=False)
    metadata_path: str = field(init=False)
    registry_path: str = field(init=False)
    
    def __post_init__(self):
        """Post-initialization to set derived paths."""
        self.persist_path = os.path.join(self.data_dir, "index", "faiss.index")
        self.metadata_path = os.path.join(self.data_dir, "index", "metadata.json")
        self.registry_path = os.path.join(self.data_dir, "index", "document_registry.json")


def load_config(config_path: str = "config.yaml") -> AppConfig:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        AppConfig instance with loaded values
    """
    try:
        with open(config_path, 'r') as f:
            raw_config = yaml.safe_load(f)
    except FileNotFoundError:
        # Return default config if file not found
        return AppConfig()
    
    # Create config objects
    config = AppConfig(
        debug=raw_config.get('system', {}).get('debug', False),
        log_level=raw_config.get('system', {}).get('log_level', 'INFO'),
        data_dir=raw_config.get('system', {}).get('data_dir', './data'),
        cache_dir=raw_config.get('system', {}).get('cache_dir', './cache'),
    )
    
    # Load sub-configurations
    if 'llm' in raw_config:
        config.llm = LLMConfig(**raw_config['llm'])
    if 'embedding' in raw_config:
        config.embedding = EmbeddingConfig(**raw_config['embedding'])
    if 'vector_store' in raw_config:
        config.vector_store = VectorStoreConfig(**raw_config['vector_store'])
    if 'retrieval' in raw_config:
        config.retrieval = RetrievalConfig(**raw_config['retrieval'])
    if 'security' in raw_config:
        config.security = SecurityConfig(**raw_config['security'])
    if 'chunking' in raw_config:
        config.chunking = ChunkingConfig(**raw_config['chunking'])
    if 'session' in raw_config:
        config.session = SessionConfig(**raw_config['session'])
    if 'features' in raw_config:
        config.features = FeatureConfig(**raw_config['features'])
    
    # Set derived paths
    config.persist_path = config.vector_store.persist_path
    config.metadata_path = config.vector_store.metadata_path
    config.registry_path = config.vector_store.registry_path
    
    return config


# Global configuration instance
_config: Optional[AppConfig] = None


def get_config(config_path: str = "config.yaml") -> AppConfig:
    """
    Get or create the global configuration instance.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Global AppConfig instance
    """
    global _config
    if _config is None:
        _config = load_config(config_path)
    return _config


def reload_config(config_path: str = "config.yaml") -> AppConfig:
    """
    Reload the global configuration from file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        New AppConfig instance
    """
    global _config
    _config = load_config(config_path)
    return _config

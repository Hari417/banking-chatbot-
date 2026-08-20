"""
RAG Workflow module for Banking RAG Chatbot.
Implements LangGraph-based orchestration for the RAG pipeline.
"""

import os
from typing import List, Dict, Optional, TypedDict, Annotated, Tuple, Any
from dataclasses import dataclass, field
import logging
import operator

from .config import AppConfig, get_config
from .llm import LLMClient, ChatMessage
from .vector_store import VectorStore, RetrievedChunk
from .embeddings import EmbeddingModel, get_embedding_model
from .retrieval import HybridRetriever, get_retriever, RetrievedDocument

logger = logging.getLogger(__name__)


# LangGraph state types
class RAGState(TypedDict):
    """State for the RAG workflow."""
    query: str
    query_embedding: Optional[List[float]]
    retrieved_docs: List[RetrievedDocument]
    context: List[str]
    messages: List[ChatMessage]
    response: str
    citations: List[str]
    confidence: float
    abstained: bool
    metadata: Dict


class RAGWorkflow:
    """
    RAG workflow using LangGraph-style state machine.
    Orchestrates the complete RAG pipeline.
    """
    
    def __init__(
        self,
        vector_store: VectorStore,
        config: Optional[AppConfig] = None
    ):
        """Initialize the RAG workflow."""
        self.config = config or get_config()
        self.llm_config = self.config.llm
        self.embedding_config = self.config.embedding
        self.retrieval_config = self.config.retrieval
        
        # Initialize components
        self.llm_client = LLMClient(self.config)
        self.embedding_model = get_embedding_model(mock=False, config=self.config)
        self.retriever = get_retriever(vector_store, self.config, mock=False)
        
        # System prompt template
        self.system_prompt = self._load_system_prompt()
    
    def _load_system_prompt(self) -> str:
        """Load the system prompt template."""
        return """You are a helpful banking assistant. Your task is to answer questions about banking policies, products, fees, loans, and procedures based on the provided context.

Rules:
1. Always answer based on the provided context
2. If the context doesn't contain relevant information, say "I don't know" rather than making up an answer
3. Provide citations to the source documents
4. Keep answers concise and relevant
5. Do not provide transactional services or access to personal account information
6. If asked about transactions, balances, or account-specific information, explain that you can only provide general information about banking products and policies

Context will be provided below in the format:
DOCUMENT [ID]: Content"""
    
    def _embed_query(self, query: str) -> List[float]:
        """Generate query embedding."""
        result = self.embedding_model.generate(query)
        return result.embeddings[0]
    
    def _retrieve(self, query: str, query_embedding: List[float]) -> List[RetrievedDocument]:
        """Retrieve relevant documents."""
        return self.retriever.retrieve(query, query_embedding)
    
    def _build_context(self, docs: List[RetrievedDocument]) -> List[str]:
        """Build context strings from retrieved documents."""
        context = []
        for i, doc in enumerate(docs):
            context.append(f"DOCUMENT [{i}]: {doc.content}")
        return context
    
    def _build_prompt(self, query: str, context: List[str]) -> str:
        """Build the LLM prompt."""
        context_str = "\n\n".join(context)
        
        prompt = f"""{self.system_prompt}

[START CONTEXT]
{context_str}
[END CONTEXT]

---

User Query: {query}

Answer:"""
        return prompt
    
    def _validate_grounding(
        self,
        response: str,
        context: List[str]
    ) -> Tuple[bool, float]:
        """
        Validate that the response is grounded in the context.
        
        Returns:
            Tuple of (is_grounded, confidence_score)
        """
        response_lower = response.lower()
        
        # Check for common phrases indicating lack of grounding
        ungrounded_phrases = [
            "based on my knowledge",
            "I believe",
            "I think",
            "possibly",
            "maybe",
            "could be",
            "according to general knowledge"
        ]
        
        found_phrases = [p for p in ungrounded_phrases if p in response_lower]
        
        if found_phrases:
            return False, 0.3
        
        # Check for response length (too long = likely hallucination)
        if len(response.split()) > 500:
            return False, 0.4
        
        # Calculate simple grounding score based on context overlap
        response_tokens = set(response.lower().split())
        context_text = " ".join(context).lower()
        context_tokens = set(context_text.split())
        
        overlap = len(response_tokens & context_tokens)
        total_response = len(response_tokens)
        
        if total_response == 0:
            return False, 0.0
        
        grounding_score = min(overlap / total_response, 1.0)
        
        return grounding_score > 0.2, grounding_score
    
    def _generate_citations(self, docs: List[RetrievedDocument]) -> List[str]:
        """Generate citation strings for retrieved documents."""
        citations = []
        for i, doc in enumerate(docs):
            source = doc.metadata.get('source', 'unknown')
            chunk_id = doc.chunk_id
            citations.append(f"[{i}]: {source} (chunk: {chunk_id})")
        return citations
    
    def _should_abstain(self, response: str) -> bool:
        """Determine if the response should indicate inability to answer."""
        abstain_triggers = [
            "i don't know",
            "cannot answer",
            "not enough information",
            "i cannot provide",
            "outside my knowledge",
            "transactional",
            "account-specific",
            "personal information"
        ]
        
        response_lower = response.lower()
        return any(trigger in response_lower for trigger in abstain_triggers)
    
    def run(
        self,
        query: str,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Run the complete RAG workflow.
        
        Args:
            query: User query
            max_retries: Maximum number of retry attempts for LLM calls
            
        Returns:
            Dictionary with query, response, citations, and confidence
        """
        try:
            # Generate embeddings for query
            query_embedding = self.embedding_model.generate(query).embeddings[0]
            
            # Retrieve relevant chunks
            retrieved = self.retriever.retrieve(query, query_embedding)
            
            # Construct prompt with context
            context = "\n\n".join([f"Source {i+1}: {r.content}" for i, r in enumerate(retrieved)])
            
            # Create prompt
            prompt = f"You are a helpful banking assistant. Use the following information to answer the user's question. If the information is not sufficient, say so and don't make up an answer.\n\n{context}\n\nQuestion: {query}\nAnswer:"
            
            # Generate response with citations
            response = self.llm_client.generate(prompt)
            
            # Extract citations
            citations = []
            if retrieved:
                for r in retrieved:
                    citations.append({
                        'content': r.content,
                        'metadata': r.metadata,
                        'score': r.combined_score
                    })
            
            abstained = self._should_abstain(response.content)
            grounded, grounding_score = self._validate_grounding(response.content, [r.content for r in retrieved])

            return {
                'query': query,
                'response': response.content,
                'citations': citations,
                'confidence': min(1.0, len(citations) / 3),
                'abstained': abstained,
                'metadata': {
                    'grounding_score': grounding_score,
                    'grounded': grounded,
                    'num_retrieved': len(retrieved),
                }
            }
        except Exception as e:
            logger.error(f"RAG workflow failed: {e}")
            
            # Return fallback response with empty citations
            return {
                'query': query,
                'response': "I'm sorry, I'm having trouble accessing the information right now. Please try again later.",
                'citations': [],
                'confidence': 0.0
            }


class MockRAGWorkflow(RAGWorkflow):
    """Mock RAG workflow for testing."""
    
    def __init__(self, config: Optional[AppConfig] = None):
        self.config = config or get_config()
    
    def run(self, query: str) -> RAGState:
        return {
            'query': query,
            'query_embedding': [0.1] * 384,
            'retrieved_docs': [
                RetrievedDocument(
                    content="Mock document content for testing.",
                    dense_score=0.8,
                    sparse_score=0.7,
                    combined_score=0.75,
                    metadata={'source': 'test'},
                    chunk_id="chunk_0"
                )
            ],
            'context': ["Mock document content for testing."],
            'messages': [],
            'response': "This is a mock response for testing purposes.",
            'citations': ["[0]: test (chunk: chunk_0)"],
            'confidence': 0.9,
            'abstained': False,
            'metadata': {'test': True}
        }


def get_rag_workflow(
    vector_store: VectorStore,
    config: Optional[AppConfig] = None,
    mock: bool = False
) -> RAGWorkflow:
    """
    Factory function to get RAG workflow.
    
    Args:
        vector_store: VectorStore instance
        config: Configuration instance
        mock: Whether to use mock workflow
        
    Returns:
        RAGWorkflow instance
    """
    if mock:
        return MockRAGWorkflow(config)
    return RAGWorkflow(vector_store, config)

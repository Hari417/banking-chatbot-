"""Vector database service for RAG (Retrieval-Augmented Generation)."""
from typing import List, Dict
import re
from data import LOAN_FAQS, POLICY_DOCUMENTS


class VectorDBService:
    """Service for managing vector database for loan FAQs and policy documents.
    
    This is a simplified implementation using keyword matching for demonstration.
    In production, use ChromaDB or similar with proper embeddings.
    """
    
    def __init__(self):
        """Initialize the vector database."""
        self.faqs = LOAN_FAQS
        self.policies = POLICY_DOCUMENTS
    
    def _calculate_relevance(self, query: str, text: str) -> float:
        """
        Calculate simple keyword-based relevance score.
        
        Args:
            query: Search query
            text: Text to compare
            
        Returns:
            Relevance score (0-1)
        """
        query_lower = query.lower()
        text_lower = text.lower()
        
        # Extract keywords from query (words longer than 2 characters)
        query_words = set(word for word in re.findall(r'\b\w+\b', query_lower) if len(word) > 2)
        text_words = set(re.findall(r'\b\w+\b', text_lower))
        
        if not query_words:
            return 0.0
        
        # Calculate overlap
        common_words = query_words.intersection(text_words)
        score = len(common_words) / len(query_words)
        
        # Boost score if query substring appears in text
        if query_lower in text_lower:
            score = min(1.0, score + 0.5)
        
        return score
    
    def search_faqs(self, query: str, n_results: int = 3) -> List[Dict]:
        """
        Search FAQs using keyword matching.
        
        Args:
            query: User query
            n_results: Number of results to return
            
        Returns:
            List of relevant FAQ documents with metadata
        """
        results = []
        
        for faq in self.faqs:
            content = f"Q: {faq['question']}\nA: {faq['answer']}"
            score = self._calculate_relevance(query, content)
            
            results.append({
                "content": content,
                "metadata": {"question": faq["question"], "type": "faq"},
                "score": score
            })
        
        # Sort by score and return top results
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:n_results]
    
    def search_policies(self, query: str, n_results: int = 3) -> List[Dict]:
        """
        Search policy documents using keyword matching.
        
        Args:
            query: User query
            n_results: Number of results to return
            
        Returns:
            List of relevant policy documents with metadata
        """
        results = []
        
        for policy in self.policies:
            content = f"Title: {policy['title']}\nSection: {policy['section']}\nContent: {policy['content']}"
            score = self._calculate_relevance(query, content)
            
            results.append({
                "content": content,
                "metadata": {
                    "title": policy["title"],
                    "section": policy["section"],
                    "type": "policy"
                },
                "score": score
            })
        
        # Sort by score and return top results
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:n_results]
    
    def search_all(self, query: str, n_results: int = 5) -> Dict[str, List[Dict]]:
        """
        Search both FAQs and policies.
        
        Args:
            query: User query
            n_results: Number of results per collection
            
        Returns:
            Dictionary with FAQ and policy results
        """
        return {
            "faqs": self.search_faqs(query, n_results // 2 + 1),
            "policies": self.search_policies(query, n_results // 2 + 1)
        }
    
    def reset_collections(self):
        """Reset all collections (useful for testing)."""
        # No-op for this simple implementation
        pass

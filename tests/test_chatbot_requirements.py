import sys
import os
import pytest
from unittest.mock import Mock, patch
import json

current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, '..', 'src')
sys.path.insert(0, src_path)

from banking_rag.config import AppConfig
from banking_rag.llm import MockLLMClient
from banking_rag.rag_workflow import MockRAGWorkflow


class TestChatbotRequirements:
    """Test cases for verifying chatbot requirements and specifications."""
    
    def test_chatbot_respects_banking_domain(self):
        """Test that the chatbot stays within banking domain and rejects non-banking queries."""
        config = AppConfig()
        workflow = MockRAGWorkflow(config)
        
        # Test non-banking queries
        non_banking_queries = [
            "What's the weather like today?",
            "How do I bake a cake?",
            "Tell me a joke.",
            "What are the latest movie releases?"
        ]
        
        for query in non_banking_queries:
            result = workflow.run(query)
            response_lower = result['response'].lower()
            
            # Verify the response indicates banking domain
            assert any(phrase in response_lower for phrase in [
                "banking", "financial", "banking assistant"
            ])
    
    def test_chatbot_handles_prohibited_queries(self):
        """Test that the chatbot properly handles prohibited queries like balance checks."""
        config = AppConfig()
        workflow = MockRAGWorkflow(config)
        
        # Test prohibited queries
        prohibited_queries = [
            "What is my account balance?",
            "Transfer money to another account.",
            "Change my PIN.",
            "Close my account."
        ]
        
        for query in prohibited_queries:
            result = workflow.run(query)
            response_lower = result['response'].lower()
            
            # Verify the response denies the request
            assert any(phrase in response_lower for phrase in [
                "cannot", "unable", "not authorized", "not permitted"
            ])
    
    def test_chatbot_abstains_from_unanswerable_questions(self):
        """Test that the chatbot abstains from answering unanswerable questions."""
        config = AppConfig()
        workflow = MockRAGWorkflow(config)
        
        # Test unanswerable questions
        unanswerable_questions = [
            "What is the interest rate on cryptocurrency accounts?",
            "What are the fees for time travel services?",
            "How do I open a bank account on Mars?"
        ]
        
        for query in unanswerable_questions:
            result = workflow.run(query)
            response_lower = result['response'].lower()
            
            # Verify the response indicates lack of knowledge
            assert any(phrase in response_lower for phrase in [
                "don't know", "not sure", "cannot tell", "do not have"
            ])
    
    def test_chatbot_provides_citations(self):
        """Test that the chatbot provides citations for its responses."""
        config = AppConfig()
        workflow = MockRAGWorkflow(config)
        
        # Test with a query that should have a citation
        result = workflow.run("What are the bank's operating hours?")
        
        # Verify citations are included
        assert len(result['citations']) > 0
        assert isinstance(result['citations'], list)
        
        # Verify citation formatting
        for citation in result['citations']:
            assert isinstance(citation, str)
            assert any(char in citation for char in ['[', ']', '(', ')', ':', '.'])
    
    def test_chatbot_includes_confidence_score(self):
        """Test that the chatbot includes a confidence score in its responses."""
        config = AppConfig()
        workflow = MockRAGWorkflow(config)
        
        # Test with a query
        result = workflow.run("What are the fees for overdraft?")
        
        # Verify confidence score is included and valid
        assert 'confidence' in result
        assert isinstance(result['confidence'], float)
        assert 0.0 <= result['confidence'] <= 1.0
    
    def test_chatbot_handles_edge_cases(self):
        """Test that the chatbot handles edge cases like long queries and typos."""
        config = AppConfig()
        workflow = MockRAGWorkflow(config)
        
        # Test long query
        long_query = "What are the fees " * 20  # 20 repeats
        result = workflow.run(long_query)
        
        # Verify response is generated
        assert len(result['response']) > 0
        
        # Test query with typos
        typo_query = "What are teh feez for overdraf?"
        result = workflow.run(typo_query)
        
        # Verify response is generated
        assert len(result['response']) > 0
    
    def test_chatbot_security_features(self):
        """Test that the chatbot implements security features like PII protection."""
        config = AppConfig()
        workflow = MockRAGWorkflow(config)
        
        # Test queries with PII
        pii_queries = [
            "My account number is 123456789, what is my balance?",
            "My password is 'secret123', can you help me reset it?",
            "I'm John Doe, SSN 123-45-6789, can you verify my identity?"
        ]
        
        for query in pii_queries:
            result = workflow.run(query)
            response_lower = result['response'].lower()
            
            # Verify the response denies the request and doesn't echo PII
            assert any(phrase in response_lower for phrase in [
                "cannot", "not permitted", "security reasons"
            ])
            
            # Verify PII is not leaked in the response
            assert "123456789" not in result['response']
            assert "secret123" not in result['response']
            assert "john doe" not in result['response']
            assert "123-45-6789" not in result['response']
    
    def test_chatbot_compliance_with_disclaimers(self):
        """Test that the chatbot includes appropriate disclaimers in its responses."""
        config = AppConfig()
        workflow = MockRAGWorkflow(config)
        
        # Test financial advice query
        result = workflow.run("What mortgage rate can I get?")
        response_lower = result['response'].lower()
        
        # Verify disclaimer is included
        assert any(phrase in response_lower for phrase in [
            "not financial advice", "consult a financial advisor", "for informational purposes"
        ])
    
    def test_chatbot_handles_ambiguous_queries(self):
        """Test that the chatbot handles ambiguous queries appropriately."""
        config = AppConfig()
        workflow = MockRAGWorkflow(config)
        
        # Test ambiguous query
        result = workflow.run("What is the fee for a checking account?")
        response_lower = result['response'].lower()
        
        # Verify the response recognizes ambiguity
        assert any(phrase in response_lower for phrase in [
            "different types", "depends on", "it varies", "multiple options"
        ])
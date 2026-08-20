#!/usr/bin/env python3
"""Quick verification script for Banking RAG Chatbot."""

import sys
sys.path.insert(0, '/home/hari/Desktop/Banking/src')

from banking_rag.config import AppConfig, get_config

# Test 1: Config
print("Test 1: Config...")
config = AppConfig()
assert config.data_dir == "./data"
assert config.llm.provider == "openai"
print("  PASS: Config works correctly")

# Test 2: Mock LLM
print("Test 2: Mock LLM...")
from banking_rag.llm import MockLLMClient
client = MockLLMClient(config)
result = client.generate("Test")
assert result.content == "This is a mock response for testing purposes."
print("  PASS: Mock LLM works")

# Test 3: Mock Embeddings
print("Test 3: Mock Embeddings...")
from banking_rag.embeddings import MockEmbeddingModel
model = MockEmbeddingModel(config)
embedding = model.generate("Test text")
assert len(embedding.embeddings[0]) == 384
print("  PASS: Mock embeddings work")

# Test 4: Mock Chunking
print("Test 4: Mock Chunking...")
from banking_rag.chunking import MockDocumentChunker
chunker = MockDocumentChunker(config)
result = chunker.chunk("Test document")
assert result.total_chunks > 0
print("  PASS: Mock chunking works")

# Test 5: Mock Vector Store
print("Test 5: Mock Vector Store...")
from banking_rag.vector_store import MockVectorStore
store = MockVectorStore(config)
chunks = store.add_chunks(
    [[0.1] * 384],
    ["Test content"],
    [{'source': 'test'}]
)
assert len(chunks) == 1
print("  PASS: Mock vector store works")

# Test 6: Mock Retrieval
print("Test 6: Mock Retrieval...")
from banking_rag.retrieval import MockHybridRetriever
retriever = MockHybridRetriever(store, config)
docs = retriever.retrieve("Test query", [0.1] * 384)
assert len(docs) > 0
print("  PASS: Mock retrieval works")

# Test 7: Mock RAG Workflow
print("Test 7: Mock RAG Workflow...")
from banking_rag.rag_workflow import MockRAGWorkflow
workflow = MockRAGWorkflow(config)
result = workflow.run("Test query")
assert result['query'] == "Test query"
assert result['response']
assert result['citations']
print("  PASS: Mock RAG workflow works")

print("\n" + "="*50)
print("ALL TESTS PASSED!")
print("="*50)

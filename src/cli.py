"""
CLI interface for Banking RAG Chatbot.
Command-line access to the RAG system.
"""

import argparse
import json
import sys
from typing import Optional
from pathlib import Path
import logging

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from banking_rag.config import load_config, get_config
from banking_rag.vector_store import VectorStore, MockVectorStore
from banking_rag.embeddings import get_embedding_model, MockEmbeddingModel
from banking_rag.retrieval import get_retriever, MockHybridRetriever
from banking_rag.rag_workflow import get_rag_workflow, MockRAGWorkflow


def setup_logging(debug: bool = False):
    """Configure logging."""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def create_interface(
    config_path: Optional[str] = None,
    mock: bool = False
):
    """Create the RAG workflow interface."""
    config = load_config(config_path) if config_path else get_config()
    
    # Initialize components
    if mock:
        vector_store = MockVectorStore(config)
        embedding_model = MockEmbeddingModel(config)
        retriever = MockHybridRetriever(vector_store, config)
        workflow = MockRAGWorkflow(config)
    else:
        vector_store = VectorStore(config)
        embedding_model = get_embedding_model(config=config)
        retriever = get_retriever(vector_store, config)
        workflow = get_rag_workflow(vector_store, config)
    
    return workflow


def chat_mode(workflow, interactive: bool = True):
    """Run the chat interface."""
    print("=" * 60)
    print("Banking RAG Chatbot - Interactive Mode")
    print("Ask questions about banking policies, products, fees, loans.")
    print("=" * 60)
    print("Type 'quit', 'exit', or Ctrl+C to end the session.")
    print()
    
    if interactive:
        while True:
            try:
                query = input("You: ").strip()
                
                if not query:
                    continue
                
                if query.lower() in ['quit', 'exit', 'q']:
                    print("Goodbye!")
                    break
                
                # Run RAG workflow
                result = workflow.run(query)
                
                # Display response
                print(f"\nAssistant: {result['response']}")
                print()
                
                # Display citations if available
                if result['citations']:
                    print("Sources:")
                    for citation in result['citations']:
                        print(f"  {citation}")
                    print()
                
                # Display confidence
                if 'metadata' in result:
                    metadata = result['metadata']
                    print(f"Confidence: {metadata.get('confidence', 0):.2%}")
                    print()
                
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except EOFError:
                print("\nGoodbye!")
                break
    else:
        # Single query mode
        query = sys.stdin.read().strip()
        result = workflow.run(query)
        
        # Output as JSON
        output = {
            'query': result['query'],
            'response': result['response'],
            'citations': result['citations'],
            'confidence': result['metadata'].get('confidence', 0) if result['metadata'] else 0,
            'metadata': result['metadata']
        }
        print(json.dumps(output, indent=2))


def single_query(workflow, query: str, output_format: str = 'text'):
    """Run a single query."""
    result = workflow.run(query)
    
    if output_format == 'json':
        output = {
            'query': result['query'],
            'response': result['response'],
            'citations': result['citations'],
            'confidence': result['metadata'].get('confidence', 0) if result['metadata'] else 0,
            'abstained': result['abstained'],
            'metadata': result['metadata']
        }
        print(json.dumps(output, indent=2))
    else:
        print(f"Query: {result['query']}")
        print()
        print(f"Response: {result['response']}")
        print()
        
        if result['citations']:
            print("Sources:")
            for citation in result['citations']:
                print(f"  {citation}")
            print()
        
        if result['metadata']:
            print(f"Confidence: {result['metadata'].get('confidence', 0):.2%}")
            print(f"Abstained: {result['abstained']}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Banking RAG Chatbot - CLI Interface'
    )
    
    # Mode selection
    subparsers = parser.add_subparsers(dest='mode', help='Mode of operation')
    
    # Chat mode
    chat_parser = subparsers.add_parser('chat', help='Interactive chat mode')
    chat_parser.add_argument('--config', '-c', help='Path to config file')
    chat_parser.add_argument('--mock', action='store_true', help='Use mock mode for testing')
    
    # Query mode
    query_parser = subparsers.add_parser('query', help='Single query mode')
    query_parser.add_argument('query', nargs='?', help='Query text')
    query_parser.add_argument('--config', '-c', help='Path to config file')
    query_parser.add_argument('--mock', action='store_true', help='Use mock mode for testing')
    query_parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    # Global options
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--version', action='store_true', help='Show version info')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.debug)
    
    if args.version:
        print("Banking RAG Chatbot v0.1.0")
        return 0
    
    # Validate arguments
    if not args.mode:
        parser.print_help()
        return 1
    
    try:
        # Create interface
        workflow = create_interface(
            config_path=args.config,
            mock=args.mock
        )
        
        if args.mode == 'chat':
            chat_mode(workflow, interactive=True)
        elif args.mode == 'query':
            if not args.query:
                # Read from stdin
                query = sys.stdin.read().strip()
            else:
                query = args.query
            
            single_query(workflow, query, 'json' if args.json else 'text')
        
        return 0
        
    except Exception as e:
        logging.error(f"Error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())

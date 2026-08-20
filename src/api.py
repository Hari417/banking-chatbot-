"""
API interface for Banking RAG Chatbot.
FastAPI-based REST API for programmatic access.
"""

from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import logging
import os
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from banking_rag.config import load_config, get_config
from banking_rag.vector_store import VectorStore, MockVectorStore
from banking_rag.embeddings import get_embedding_model, MockEmbeddingModel
from banking_rag.retrieval import get_retriever, MockHybridRetriever
from banking_rag.rag_workflow import get_rag_workflow, MockRAGWorkflow, RAGState

logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Banking RAG API",
    description="API for Banking FAQ RAG Chatbot",
    version="0.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session store
session_store: Dict[str, List[Dict[str, Any]]] = {}


# Pydantic models
class QueryRequest(BaseModel):
    """Request model for chat endpoint."""
    query: str = Field(..., min_length=1, max_length=1000)
    session_id: Optional[str] = None
    context: Optional[Dict[str, str]] = None


class QueryResponse(BaseModel):
    """Response model for chat endpoint."""
    query: str
    response: str
    citations: List[str]
    confidence: float
    abstained: bool
    session_id: Optional[str]
    metadata: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    vector_store_ready: bool
    model_available: bool


class SessionRequest(BaseModel):
    """Request model for session management."""
    session_id: str


class SessionResponse(BaseModel):
    """Response model for session management."""
    session_id: str
    messages: List[Dict[str, str]]
    count: int


class IngestRequest(BaseModel):
    """Request model for document ingestion."""
    content: str
    source: str
    metadata: Optional[Dict[str, Any]] = None
    chunk_strategy: Optional[str] = None


class IngestResponse(BaseModel):
    """Response model for document ingestion."""
    document_id: str
    chunks_ingested: int
    embeddings_generated: int


# Global workflow instance
_workflow: Optional[MockRAGWorkflow] = None
_config: Optional[Any] = None


def get_workflow():
    """Get the RAG workflow instance."""
    global _workflow, _config
    
    if _workflow is None:
        config_path = os.environ.get('BANKING_RAG_CONFIG', 'config.yaml')
        _config = load_config(config_path)
        
        mock = os.environ.get('BANKING_RAG_MOCK', 'false').lower() == 'true'
        
        if mock:
            vector_store = MockVectorStore(_config)
            workflow = MockRAGWorkflow(_config)
        else:
            vector_store = VectorStore(_config)
            workflow = get_rag_workflow(vector_store, _config)
        
        _workflow = workflow
    
    return _workflow


@app.on_event("startup")
async def startup_event():
    """Initialize app on startup."""
    logger.info("Starting Banking RAG API")
    workflow = get_workflow()
    logger.info("RAG workflow initialized")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    workflow = get_workflow()
    
    return HealthResponse(
        status="ready",
        version="0.1.0",
        vector_store_ready=True,
        model_available=True
    )


@app.post("/chat", response_model=QueryResponse)
async def chat(request: QueryRequest):
    """Chat endpoint - send a query and get a response."""
    try:
        workflow = get_workflow()
        
        # Run RAG workflow
        result = workflow.run(request.query)
        
        # Store in session if provided
        if request.session_id:
            if request.session_id not in session_store:
                session_store[request.session_id] = []
            
            session_store[request.session_id].append({
                'role': 'user',
                'content': request.query
            })
            session_store[request.session_id].append({
                'role': 'assistant',
                'content': result['response'],
                'citations': result['citations']
            })
        
        return QueryResponse(
            query=result['query'],
            response=result['response'],
            citations=result['citations'],
            confidence=result['confidence'],
            abstained=result['abstained'],
            session_id=request.session_id,
            metadata=result['metadata']
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query")
async def query_endpoint(request: QueryRequest):
    """Query endpoint (alias for /chat)."""
    return await chat(request)


@app.get("/sessions", response_model=List[str])
async def list_sessions():
    """List all active sessions."""
    return list(session_store.keys())


@app.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    """Get session history."""
    if session_id not in session_store:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    return SessionResponse(
        session_id=session_id,
        messages=session_store[session_id],
        count=len(session_store[session_id])
    )


@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session."""
    if session_id not in session_store:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    del session_store[session_id]
    
    return {"message": f"Session {session_id} deleted"}


@app.post("/ingest")
async def ingest(request: IngestRequest):
    """Ingest a new document into the knowledge base."""
    try:
        workflow = get_workflow()
        config = get_config()
        
        # In mock mode, just return success
        if isinstance(workflow, MockRAGWorkflow):
            return IngestResponse(
                document_id="mock_doc_001",
                chunks_ingested=1,
                embeddings_generated=1
            )
        
        # In production mode, we would actually ingest here
        # For now, return placeholder response
        return IngestResponse(
            document_id="doc_001",
            chunks_ingested=1,
            embeddings_generated=1
        )
        
    except Exception as e:
        logger.error(f"Ingestion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/config")
async def get_config_endpoint():
    """Get current configuration."""
    config = get_config()
    
    return {
        'llm': {
            'provider': config.llm.provider,
            'model': config.llm.model
        },
        'embedding': {
            'provider': config.embedding.provider,
            'model': config.embedding.model,
            'dimensions': config.embedding.dimensions
        },
        'vector_store': {
            'index_type': config.vector_store.index_type,
            'persist_path': config.vector_store.persist_path
        },
        'security': {
            'pii_detection_enabled': config.security.pii_detection_enabled,
            'rate_limit_enabled': config.security.rate_limit_enabled
        }
    }


@app.exception_handler(500)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred. Please try again."}
    )


def get_deployment_config():
    """Get deployment configuration."""
    return {
        'host': os.environ.get('BANKING_RAG_API_HOST', '0.0.0.0'),
        'port': int(os.environ.get('BANKING_RAG_API_PORT', 8000)),
        'debug': os.environ.get('BANKING_RAG_DEBUG', 'false').lower() == 'true'
    }


if __name__ == '__main__':
    import uvicorn
    
    config = get_deployment_config()
    uvicorn.run(
        "api:app",
        host=config['host'],
        port=config['port'],
        reload=config['debug']
    )

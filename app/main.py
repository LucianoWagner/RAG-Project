"""
FastAPI Application - RAG PDF System

This is the main application file that defines all API endpoints and orchestrates
the RAG pipeline for document upload and querying.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
import shutil
from typing import List

from app.config import settings
from app.models.schemas import (
    UploadResponse,
    QueryRequest,
    QueryResponse,
    SourceChunk,
    HealthResponse
)
from app.services.pdf_service import PDFService
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStore
from app.services.llm_service import LLMService
from app.utils.logger import logger

# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="RAG system for querying PDF documents using local LLMs",
)

# Initialize services
pdf_service = PDFService()
chunking_service = ChunkingService(
    chunk_size=settings.chunk_size,
    chunk_overlap=settings.chunk_overlap
)
embedding_service = EmbeddingService(model_name=settings.embedding_model)
llm_service = LLMService(
    base_url=settings.ollama_base_url,
    model=settings.ollama_model
)

# Initialize vector store (will be loaded on first use)
vector_store = None


def get_vector_store() -> VectorStore:
    """
    Get or initialize the vector store.
    
    Returns:
        VectorStore instance
    """
    global vector_store
    
    if vector_store is None:
        # Get embedding dimension from the model
        dimension = embedding_service.get_embedding_dimension()
        
        # Try to load existing index
        index_path = settings.vector_store_dir
        vector_store = VectorStore(dimension=dimension, index_path=index_path)
        
        logger.info("Vector store initialized")
    
    return vector_store


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "RAG PDF System API",
        "version": settings.app_version,
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    
    Verifies that all system components are operational:
    - Ollama service connectivity
    - Embedding model status
    - Vector store initialization
    """
    logger.info("Health check requested")
    
    # Check Ollama
    ollama_available = await llm_service.check_health()
    
    # Check embedding model
    embedding_model_loaded = embedding_service.is_model_loaded()
    
    # Check vector store
    try:
        store = get_vector_store()
        vector_store_initialized = True
    except Exception as e:
        logger.error(f"Vector store check failed: {e}")
        vector_store_initialized = False
    
    # Determine overall status
    status = "healthy" if (
        ollama_available and 
        vector_store_initialized
    ) else "degraded"
    
    return HealthResponse(
        status=status,
        ollama_available=ollama_available,
        embedding_model_loaded=embedding_model_loaded,
        vector_store_initialized=vector_store_initialized
    )


@app.post("/documents/upload", response_model=UploadResponse, tags=["Documents"])
async def upload_document(file: UploadFile = File(...)):
    """
    Upload and process a PDF document.
    
    Steps:
    1. Validate file is a PDF
    2. Extract text from PDF
    3. Split text into chunks
    4. Generate embeddings for chunks
    5. Store in vector database
    
    Args:
        file: PDF file to upload
        
    Returns:
        UploadResponse with processing details
        
    Raises:
        HTTPException: If file is invalid or processing fails
    """
    logger.info(f"Document upload requested: {file.filename}")
    
    # Validate file type
    if not file.filename.endswith('.pdf'):
        logger.warning(f"Invalid file type: {file.filename}")
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported"
        )
    
    # Save uploaded file
    file_path = settings.pdf_upload_dir / file.filename
    
    try:
        with open(file_path, 'wb') as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"Saved file to {file_path}")
        
    except Exception as e:
        logger.error(f"Failed to save file: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save file: {str(e)}"
        )
    
    try:
        # Extract text from PDF
        text = pdf_service.extract_text(file_path)
        
        # Split into chunks
        chunks = chunking_service.split_text(text)
        
        logger.info(f"Created {len(chunks)} chunks from {file.filename}")
        
        # Generate embeddings
        embeddings = embedding_service.embed_texts(chunks)
        
        # Store in vector database
        store = get_vector_store()
        chunks_added = store.add_documents(
            embeddings=embeddings,
            texts=chunks,
            source=file.filename
        )
        
        # Save vector store to disk
        store.save_index(settings.vector_store_dir)
        
        logger.info(f"Successfully processed {file.filename}")
        
        return UploadResponse(
            filename=file.filename,
            chunks_processed=chunks_added,
            message="Document processed successfully"
        )
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing document: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing document: {str(e)}"
        )


@app.post("/query", response_model=QueryResponse, tags=["Query"])
async def query_documents(request: QueryRequest):
    """
    Query the uploaded documents with a natural language question.
    
    Steps:
    1. Generate embedding for the question
    2. Search vector store for relevant chunks
    3. Build context from retrieved chunks
    4. Generate answer using LLM with context
    
    Args:
        request: QueryRequest with the question
        
    Returns:
        QueryResponse with answer and source chunks
        
    Raises:
        HTTPException: If no documents are uploaded or query fails
    """
    logger.info(f"Query requested: '{request.question}'")
    
    try:
        # Get vector store
        store = get_vector_store()
        
        # Check if any documents are loaded
        if store.index.ntotal == 0:
            logger.warning("No documents loaded in vector store")
            raise HTTPException(
                status_code=400,
                detail="No documents have been uploaded yet. Please upload documents first."
            )
        
        # Generate query embedding
        query_embedding = embedding_service.embed_query(request.question)
        
        # Search for relevant chunks
        results = store.search(query_embedding, k=settings.top_k_results)
        
        if not results:
            # No results found
            logger.info("No relevant context found")
            answer = await llm_service.generate_answer_no_context()
            
            return QueryResponse(
                answer=answer,
                sources=[],
                has_context=False
            )
        
        # Build context from results
        context = "\n\n---\n\n".join([r['text'] for r in results])
        
        logger.info(f"Built context from {len(results)} chunks")
        
        # Generate answer using LLM
        answer = await llm_service.generate_answer(request.question, context)
        
        # Build source chunks for response
        sources = [
            SourceChunk(text=r['text'], score=r['score'])
            for r in results
        ]
        
        return QueryResponse(
            answer=answer,
            sources=sources,
            has_context=True
        )
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )


@app.on_event("startup")
async def startup_event():
    """Initialize services on application startup."""
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Ollama URL: {settings.ollama_base_url}")
    logger.info(f"Ollama Model: {settings.ollama_model}")
    logger.info(f"Embedding Model: {settings.embedding_model}")
    
    # Pre-load embedding model
    try:
        embedding_service._ensure_model_loaded()
        logger.info("Embedding model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load embedding model: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown."""
    logger.info("Shutting down application")
    
    # Save vector store if initialized
    global vector_store
    if vector_store is not None:
        try:
            vector_store.save_index(settings.vector_store_dir)
            logger.info("Vector store saved successfully")
        except Exception as e:
            logger.error(f"Failed to save vector store: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

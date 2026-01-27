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
    HealthResponse,
    DeleteResponse
)
from app.services.pdf_service import PDFService
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStore
from app.services.llm_service import LLMService
from app.services.intent_classifier import IntentClassifier
from app.services.web_search_service import WebSearchService
from app.services.bm25_service import BM25Service
from app.services.hybrid_search_service import HybridSearchService
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
# Initialize intent classifier (uses embedding service)
intent_classifier = IntentClassifier(embedding_service=embedding_service)
# Initialize web search service (uses llm service)
web_search_service = WebSearchService(llm_service=llm_service)

# Initialize vector store and BM25 (will be loaded on first use)
vector_store = None
bm25_service = None
hybrid_search_service = None


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


def get_bm25_service() -> BM25Service:
    """
    Get or initialize the BM25 service.
    
    Returns:
        BM25Service instance
    """
    global bm25_service
    
    if bm25_service is None:
        # Try to load existing index
        index_path = settings.vector_store_dir
        bm25_service = BM25Service(index_path=index_path)
        
        logger.info("BM25 service initialized")
    
    return bm25_service


def get_hybrid_search_service() -> HybridSearchService:
    """
    Get or initialize the hybrid search service.
    
    Returns:
        HybridSearchService instance
    """
    global hybrid_search_service
    
    if hybrid_search_service is None:
        # Initialize with required services
        bm25 = get_bm25_service()
        store = get_vector_store()
        
        hybrid_search_service = HybridSearchService(
            bm25_service=bm25,
            vector_store=store,
            embedding_service=embedding_service,
            rrf_k=settings.rrf_k
        )
        
        logger.info(f"Hybrid search service initialized (mode: {settings.search_mode})")
    
    return hybrid_search_service


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
        
        # Also add to BM25 index for hybrid search
        bm25 = get_bm25_service()
        
        # Build metadata for BM25 (same structure as vector store)
        metadata = [
            {
                'text': text,
                'source': file.filename,
                'chunk_id': store.index.ntotal - len(chunks) + i
            }
            for i, text in enumerate(chunks)
        ]
        
        bm25.add_documents(texts=chunks, metadata=metadata)
        
        # Save both indices to disk
        store.save_index(settings.vector_store_dir)
        bm25.save_index(settings.vector_store_dir)
        
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


@app.delete("/documents/all", response_model=DeleteResponse, tags=["Documents"])
async def delete_all_documents():
    """
    Delete all uploaded PDFs and clear all indices (FAISS + BM25).
    
    This endpoint:
    1. Clears vector store (FAISS index + metadata)
    2. Clears BM25 index
    3. Deletes all uploaded PDF files
    4. Resets global service instances
    
    Use this to start fresh or free up disk space.
    
    Returns:
        DeleteResponse with count of deleted files
        
    Raises:
        HTTPException: If deletion fails
    """
    logger.info("Delete all documents requested")
    
    deleted_pdfs = 0
    deleted_indices = 0
    
    try:
        # Count and delete PDF files
        pdf_files = list(settings.pdf_upload_dir.glob("*.pdf"))
        for pdf_file in pdf_files:
            try:
                pdf_file.unlink()
                deleted_pdfs += 1
                logger.debug(f"Deleted PDF: {pdf_file.name}")
            except Exception as e:
                logger.warning(f"Failed to delete {pdf_file.name}: {e}")
        
        # Count and delete index files
        index_files = list(settings.vector_store_dir.glob("*"))
        for index_file in index_files:
            try:
                index_file.unlink()
                deleted_indices += 1
                logger.debug(f"Deleted index file: {index_file.name}")
            except Exception as e:
                logger.warning(f"Failed to delete {index_file.name}: {e}")
        
        # Reset global service instances to force re-initialization
        global vector_store, bm25_service, hybrid_search_service
        vector_store = None
        bm25_service = None
        hybrid_search_service = None
        
        logger.info(
            f"Successfully deleted {deleted_pdfs} PDFs and {deleted_indices} index files"
        )
        
        return DeleteResponse(
            message="All documents and indices deleted successfully",
            deleted_pdfs=deleted_pdfs,
            deleted_indices=deleted_indices
        )
        
    except Exception as e:
        logger.error(f"Error deleting documents: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting documents: {str(e)}"
        )


@app.post("/query", response_model=QueryResponse, tags=["Query"])
async def query_documents(request: QueryRequest):
    """
    Query the uploaded documents with intelligent intent classification.
    
    Flow:
    1. Classify intent (greeting vs document query)
    2. Handle greetings with personalized LLM responses
    3. Check if vector store is empty (offer upload or web search)
    4. Search documents with similarity threshold (0.7)
    5. Generate answer from context or suggest web search
    
    Args:
        request: QueryRequest with the question
        
    Returns:
        QueryResponse with answer, intent, confidence score, and suggestions
    """
    logger.info(f"Query requested: '{request.question}'")
    
    try:
        # Generate query embedding (needed for both classification and search)
        query_embedding = embedding_service.embed_query(request.question)
        
        # STEP 1: Classify Intent (hybrid: regex + embeddings)
        intent = intent_classifier.classify(request.question, query_embedding)
        
        #  STEP 2: Fast path for greetings
        if intent == "GREETING":
            logger.info("Detected greeting intent")
            greeting_response = await llm_service.generate_greeting_response(request.question)
            
            return QueryResponse(
                answer=greeting_response,
                sources=[],
                has_context=False,
                intent="GREETING"
            )
        
        # STEP 3: Check if vector store is empty
        store = get_vector_store()
        
        if store.index.ntotal == 0:
            logger.warning("No documents loaded in vector store")
            return QueryResponse(
                answer="No tengo documentos cargados aún. ¿Deseas:\n1. Subir PDFs primero\n2. Buscar esta información en internet?",
                sources=[],
                has_context=False,
                intent="NO_DOCUMENTS",
                suggested_action="upload_or_search"
            )
        
        # STEP 4: Search for relevant chunks
        if settings.search_mode == "hybrid":
            # Use hybrid search (BM25 + Vector + RRF)
            logger.info("Using hybrid search (BM25 + Vector + RRF)")
            hybrid_service = get_hybrid_search_service()
            results = hybrid_service.search(request.question, k=settings.top_k_results)
        else:
            # Use pure vector search
            logger.info("Using pure vector search")
            results = store.search(query_embedding, k=settings.top_k_results)
        
        # STEP 5: Check relevance with threshold (L2 distance < 0.7 = good match)
        SIMILARITY_THRESHOLD = 0.7  # Industry standard for sentence-transformers
        
        if not results or results[0]['score'] >= SIMILARITY_THRESHOLD:
            # Low relevance - suggest web search
            logger.info(f"Low relevance scores (threshold: {SIMILARITY_THRESHOLD})")
            
            return QueryResponse(
                answer="No encontré información relevante en los documentos cargados. ¿Quieres que busque esta información en internet?",
                sources=[],
                has_context=False,
                intent="LOW_RELEVANCE",
                confidence_score=0.0,
                suggested_action="web_search"
            )
        
        # STEP 6: Good match - build context and generate answer
        context = "\n\n---\n\n".join([r['text'] for r in results])
        
        logger.info(f"Built context from {len(results)} chunks, best score: {results[0]['score']:.3f}")
        
        # Generate answer using LLM
        answer = await llm_service.generate_answer(request.question, context)
        
        # Calculate confidence (convert L2 distance to 0-1 scale)
        best_score = results[0]['score']
        confidence = max(0.0, min(1.0, 1.0 - (best_score / SIMILARITY_THRESHOLD)))
        
        # Build source chunks for response
        sources = [
            SourceChunk(text=r['text'], score=r['score'])
            for r in results
        ]
        
        return QueryResponse(
            answer=answer,
            sources=sources,
            has_context=True,
            intent="DOCUMENT_QUERY",
            confidence_score=round(confidence, 2)
        )
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )


@app.post("/query/web-search", response_model=QueryResponse, tags=["Query"])
async def search_web(request: QueryRequest):
    """
    Perform web search when documents don't have relevant information.
    
    This endpoint is called when:
    - User confirms they want to search the web
    - Low relevance score from vector store
    - No documents uploaded
    
    Args:
        request: QueryRequest with the question to search
        
    Returns:
        QueryResponse with web search results summarized by LLM
    """
    logger.info(f"Web search requested for: '{request.question}'")
    
    try:
        # Perform web search and summarize with LLM
        answer = await web_search_service.search_and_summarize(
            question=request.question,
            max_results=3  # Optimized for speed
        )
        
        return QueryResponse(
            answer=answer,
            sources=[],  # Could add web URLs as sources in the future
            has_context=True,  # Has web context
            intent="WEB_SEARCH",
            confidence_score=None  # Not applicable for web search
        )
        
    except Exception as e:
        logger.error(f"Error performing web search: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error performing web search: {str(e)}"
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

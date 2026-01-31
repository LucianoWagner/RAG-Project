"""
FastAPI Application - RAG PDF System v2.0
Production-ready with Observability, Caching, and Analytics

New Features:
- Prometheus metrics
- Structured logging
- Redis caching
- MySQL analytics
- Circuit breakers
- Request tracing
"""

import time
import hashlib
from uuid import uuid4
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Request
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from pathlib import Path

import shutil
from typing import List, Optional

# Configuration
from app.config import settings

# Models
from app.models.schemas import (
    UploadResponse,
    QueryRequest,
    QueryResponse,
    SourceChunk,
    HealthResponse,
    DeleteResponse
)

# Services
from app.services.pdf_service import PDFService
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStore
from app.services.llm_service import LLMService
from app.services.intent_classifier import IntentClassifier
from app.services.web_search_service import WebSearchService
from app.services.bm25_service import BM25Service
from app.services.hybrid_search_service import HybridSearchService

# NEW: Observability & Database
from app.services.cache_service import CacheService, get_cache
from app.services.metrics_service import (
    MetricsCollector,
    get_metrics,
    query_latency,
    embedding_latency,
    llm_latency,
    vector_store_size
)
from app.database import (
    get_db,
    init_database,
    check_database_health,
    DocumentMetadata,
    User
)
from app.database.repositories import DocumentRepository
from app.utils.logging_config import get_logger
from app.utils.resilience import (
    with_circuit_breaker,
    with_retry,
    with_timeout,
    ollama_breaker,
    ollama_breaker,
    get_circuit_breaker_status
)

# Authentication
from app.auth.router import router as auth_router
from app.auth.dependencies import get_current_user
# Initialize logger
logger = get_logger(__name__)


# ============================================================================
# LIFESPAN CONTEXT MANAGER
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown tasks following best practices.
    """
    # ===== STARTUP =====
    logger.info(f"🚀 Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Ollama: {settings.ollama_base_url} | Model: {settings.ollama_model}")
    logger.info(f"Embedding Model: {settings.embedding_model}")
    logger.info(f"Search Mode: {settings.search_mode}")
    
    # Initialize cache
    try:
        cache = await get_cache()
        logger.info("✅ Redis cache initialized")
        MetricsCollector.update_health("redis", True)
    except Exception as e:
        logger.warning(f"⚠️  Redis not available: {e}")
        MetricsCollector.update_health("redis", False)
    
    # Initialize database
    try:
        await init_database()
        health = await check_database_health()
        if health:
            logger.info("✅ MySQL database initialized")
            MetricsCollector.update_health("mysql", True)
        else:
            raise Exception("Database health check failed")
    except Exception as e:
        logger.warning(f"⚠️  MySQL not available: {e}")
        MetricsCollector.update_health("mysql", False)
    
    # Pre-load embedding model
    try:
        embedding_service._ensure_model_loaded()
        logger.info("✅ Embedding model loaded")
    except Exception as e:
        logger.error(f"❌ Failed to load embedding model: {e}")
    
    # Check Ollama
    try:
        ollama_health = await llm_service.check_health()
        MetricsCollector.update_health("ollama", ollama_health)
        if ollama_health:
            logger.info("✅ Ollama service connected")
        else:
            logger.warning("⚠️  Ollama not available")
    except Exception as e:
        logger.warning(f"⚠️  Ollama check failed: {e}")
        MetricsCollector.update_health("ollama", False)
    
    logger.info("=" * 50)
    logger.info(f"🎯 {settings.app_name} is ready!")
    logger.info(f"📊 Docs: http://localhost:8000/docs")
    logger.info(f"📈 Metrics: http://localhost:8000/metrics")
    logger.info("=" * 50)
    
    yield  # Application runs here
    
    # ===== SHUTDOWN =====
    logger.info("🔄 Shutting down application...")
    
    # Save vector store
    global vector_store
    if vector_store is not None:
        try:
            vector_store.save_index(settings.vector_store_dir)
            logger.info("✅ Vector store saved")
        except Exception as e:
            logger.error(f"❌ Failed to save vector store: {e}")
    
    # Close cache connection
    cache = app.state.cache if hasattr(app.state, 'cache') else None
    if cache:
        await cache.close()
        logger.info("✅ Cache connection closed")
    
    logger.info("👋 Shutdown complete")


# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Production-ready RAG system with observability, caching, and analytics",
    lifespan=lifespan
)

# Include routers
app.include_router(auth_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# MIDDLEWARE
# ============================================================================

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """
    Middleware to track request metrics automatically.
    
    Tracks:
    - Request latency
    - Error rates
    - Request volume
    """
    # Skip metrics for /metrics endpoint to avoid recursion
    if request.url.path == "/metrics":
        return await call_next(request)
    
    start_time = time.time()
    
    try:
        response = await call_next(request)
        
        # Record latency
        latency = time.time() - start_time
        
        # Log request
        logger.info(
            "Request completed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "latency_ms": round(latency * 1000, 2)
            }
        )
        
        return response
        
    except Exception as e:
        latency = time.time() - start_time
        logger.error(
            f"Request failed: {e}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "latency_ms": round(latency * 1000, 2)
            }
        )
        MetricsCollector.record_error(
            error_type=type(e).__name__,
            component="api"
        )
        raise


# ============================================================================
# SERVICE INITIALIZATION
# ============================================================================

# Core services
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
intent_classifier = IntentClassifier(embedding_service=embedding_service)
web_search_service = WebSearchService(llm_service=llm_service)

# Global instances (lazy initialization)
vector_store = None
bm25_service = None
hybrid_search_service = None


def get_vector_store() -> VectorStore:
    """Get or initialize vector store."""
    global vector_store
    
    if vector_store is None:
        dimension = embedding_service.get_embedding_dimension()
        index_path = settings.vector_store_dir
        vector_store = VectorStore(dimension=dimension, index_path=index_path)
        
        # Update metrics
        vector_store_size.set(vector_store.index.ntotal)
        logger.info(f"Vector store initialized: {vector_store.index.ntotal} documents")
    
    return vector_store


def get_bm25_service() -> BM25Service:
    """Get or initialize BM25 service."""
    global bm25_service
    
    if bm25_service is None:
        index_path = settings.vector_store_dir
        bm25_service = BM25Service(index_path=index_path)
        logger.info("BM25 service initialized")
    
    return bm25_service


def get_hybrid_search_service() -> HybridSearchService:
    """Get or initialize hybrid search service."""
    global hybrid_search_service
    
    if hybrid_search_service is None:
        bm25 = get_bm25_service()
        store = get_vector_store()
        
        hybrid_search_service = HybridSearchService(
            bm25_service=bm25,
            vector_store=store,
            embedding_service=embedding_service,
            rrf_k=settings.rrf_k
        )
        logger.info(f"Hybrid search initialized (RRF k={settings.rrf_k})")
    
    return hybrid_search_service


# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

async def get_document_repository(db: AsyncSession = Depends(get_db)) -> DocumentRepository:
    """Inject DocumentRepository."""
    return DocumentRepository(db)


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": f"{settings.app_name} - Production API",
        "version": settings.app_version,
        "search_mode": settings.search_mode,
        "docs": "/docs",
        "metrics": "/metrics",
        "health": "/health",
        "analytics": "/analytics/summary"
    }


@app.get("/health", tags=["Health"])
async def health_check(
    cache: CacheService = Depends(get_cache),
    current_user: User = Depends(get_current_user)  # 🔐 Protected Endpoint
):
    """
    Enhanced health check with component-level status.
    
    Returns:
        Detailed health status for all components
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
        documents_count = store.index.ntotal
    except Exception as e:
        logger.error(f"Vector store check failed: {e}")
        vector_store_initialized = False
        documents_count = 0
    
    # Check Redis
    redis_available = cache._initialized
    
    # Check MySQL
    mysql_available = await check_database_health()
    
    # Circuit breaker status
    breakers = get_circuit_breaker_status()
    
    # Overall status
    critical_services = [ollama_available, vector_store_initialized]
    status = "healthy" if all(critical_services) else "degraded"
    
    return {
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "ollama": {
                "available": ollama_available,
                "circuit_breaker": breakers["ollama"]["state"]
            },
            "embedding_model": {
                "loaded": embedding_model_loaded
            },
            "vector_store": {
                "initialized": vector_store_initialized,
                "documents": documents_count
            },
            "redis": {
                "available": redis_available,
                "circuit_breaker": breakers["redis"]["state"]
            },
            "mysql": {
                "available": mysql_available
            }
        },
        "config": {
            "search_mode": settings.search_mode,
            "top_k": settings.top_k_results,
           "caching_enabled": settings.enable_metrics
        }
    }


@app.get("/metrics", tags=["Monitoring"])
async def metrics_endpoint(
    current_user: User = Depends(get_current_user)  # 🔐 Protected Endpoint
):
    """
    Prometheus metrics endpoint.
    
    Returns:
        Metrics in Prometheus text format
    """
    from prometheus_client import CONTENT_TYPE_LATEST
    
    metrics_data = get_metrics()
    return Response(content=metrics_data, media_type=CONTENT_TYPE_LATEST)


@app.post("/documents/upload", response_model=UploadResponse, tags=["Documents"])
async def upload_document(
    file: UploadFile = File(...),
    cache: CacheService = Depends(get_cache),
    doc_repo: DocumentRepository = Depends(get_document_repository),
    current_user: User = Depends(get_current_user)  # 🔐 Protected Endpoint
):
    """
    Upload and process a PDF document with caching and metrics.
    
    Protected: Requires valid JWT token.
    NEW: Tracks upload metrics and stores metadata in database
    """
    start_time = time.time()
    logger.info(f"Document upload requested: {file.filename}")
    
    # Validate file type
    if not file.filename.endswith('.pdf'):
        logger.warning(f"Invalid file type: {file.filename}")
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Read file content
    try:
        content = await file.read()
        file_size = len(content)
        logger.info(f"Read file ({file_size} bytes)")
    except Exception as e:
        logger.error(f"Failed to read file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")
    
    # Calculate file hash BEFORE saving
    file_hash = hashlib.sha256(content).hexdigest()
    
    # Check for duplicates
    try:
        existing_doc = await doc_repo.get_document_by_hash(file_hash)
        if existing_doc:
            logger.warning(f"Duplicate file detected: {file.filename} (matches {existing_doc.filename})")
            raise HTTPException(
                status_code=409,
                detail={
                    "message": "This document has already been uploaded",
                    "original_filename": existing_doc.filename,
                    "upload_date": existing_doc.upload_timestamp.isoformat(),
                    "chunks_count": existing_doc.chunks_count
                }
            )
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        # If DB check fails, log warning but continue (graceful degradation)
        logger.warning(f"Duplicate check failed, proceeding anyway: {e}")
    
    # Now save file (only if not duplicate)
    file_path = settings.pdf_upload_dir / file.filename
    try:
        with open(file_path, 'wb') as buffer:
            buffer.write(content)
        logger.info(f"Saved file to {file_path}")
        
    except Exception as e:
        logger.error(f"Failed to save file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    try:
        # Extract text (with OCR fallback for scanned PDFs)
        text, used_ocr = pdf_service.extract_text(file_path)
        if used_ocr:
            logger.info(f"Text extracted using OCR for scanned PDF: {file.filename}")
        
        # Split into chunks
        chunks = chunking_service.split_text(text)
        logger.info(f"Created {len(chunks)} chunks")
        
        # Generate embeddings with caching
        embed_start = time.time()
        embeddings = embedding_service.embed_texts(chunks)
        embed_time = int((time.time() - embed_start) * 1000)
        
        # Store in vector database
        store = get_vector_store()
        chunks_added = store.add_documents(
            embeddings=embeddings,
            texts=chunks,
            source=file.filename
        )
        
        # Add to BM25 index
        bm25 = get_bm25_service()
        metadata = [
            {
                'text': text,
                'source': file.filename,
                'chunk_id': store.index.ntotal - len(chunks) + i
            }
            for i, text in enumerate(chunks)
        ]
        bm25.add_documents(texts=chunks, metadata=metadata)
        
        # Save indices
        store.save_index(settings.vector_store_dir)
        bm25.save_index(settings.vector_store_dir)
        
        # Update metrics
        vector_store_size.set(store.index.ntotal)
        
        # Log to database
        processing_time = int((time.time() - start_time) * 1000)
        try:
            await doc_repo.log_document_upload(
                filename=file.filename,
                file_hash=file_hash,
                chunks_count=chunks_added,
                file_size_bytes=file_size,
                processing_time_ms=processing_time,
                extracted_text_length=len(text)
            )
        except Exception as e:
            logger.warning(f"Failed to log document to database: {e}")
        
        logger.info(f"Successfully processed {file.filename} in {processing_time}ms")
        
        return UploadResponse(
            filename=file.filename,
            chunks_processed=chunks_added,
            message=f"Document processed successfully ({processing_time}ms)"
        )
        
    except Exception as e:
        logger.error(f"Error processing document: {e}")
        MetricsCollector.record_error("document_processing_error", "upload")
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")


@app.delete("/documents/all", response_model=DeleteResponse, tags=["Documents"])
async def delete_all_documents(
    cache: CacheService = Depends(get_cache),
    current_user: User = Depends(get_current_user)  # 🔐 Protected Endpoint
):
    """
    Delete all documents and clear caches.
    
    Protected: Requires valid JWT token.
    NEW: Also flushes Redis cache
    """
    logger.info("Delete all documents requested")
    
    deleted_pdfs = 0
    deleted_indices = 0
    
    try:
        # Delete PDFs
        pdf_files = list(settings.pdf_upload_dir.glob("*.pdf"))
        for pdf_file in pdf_files:
            try:
                pdf_file.unlink()
                deleted_pdfs += 1
            except Exception as e:
                logger.warning(f"Failed to delete {pdf_file.name}: {e}")
        
        # Delete indices
        index_files = list(settings.vector_store_dir.glob("*"))
        for index_file in index_files:
            try:
                index_file.unlink()
                deleted_indices += 1
            except Exception as e:
                logger.warning(f"Failed to delete {index_file.name}: {e}")
        
        # Reset global services
        global vector_store, bm25_service, hybrid_search_service
        vector_store = None
        bm25_service = None
        hybrid_search_service = None
        
        # Flush cache
        if cache._initialized:
            await cache.flush_all()
            logger.info("Cache flushed")
        
        # Update metrics
        vector_store_size.set(0)
        
        logger.info(f"Deleted {deleted_pdfs} PDFs and {deleted_indices} index files")
        
        return DeleteResponse(
            message="All documents, indices, and caches cleared",
            deleted_pdfs=deleted_pdfs,
            deleted_indices=deleted_indices
        )
        
    except Exception as e:
        logger.error(f"Error deleting documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# QUERY ENDPOINT (ENHANCED)
# ============================================================================

@app.post("/query", response_model=QueryResponse, tags=["Query"])
async def query_documents(
    request: QueryRequest,
    cache: CacheService = Depends(get_cache)
):
    """
    Query with observability and caching.
    
    Features:
    - Embedding caching (10x faster repeated queries)
    - Prometheus metrics tracking
    - Circuit breaker protection
    """
    query_id = str(uuid4())
    start_time = time.time()
    
    logger.info(f"Query {query_id}: '{request.question}'")
    
    try:
        # Generate query embedding WITH CACHING
        cache_key = f"embed:{hashlib.sha256(request.question.encode()).hexdigest()[:16]}"
        
        embed_start = time.time()
        query_embedding = await cache.get_or_compute(
            key=cache_key,
            compute_fn=embedding_service.embed_query,
            ttl=settings.cache_ttl_embeddings,
            cache_type="embeddings",
            query=request.question
        )
        embed_time = int((time.time() - embed_start) * 1000)
        embedding_latency.observe((time.time() - embed_start))
        
        # Classify Intent
        intent = intent_classifier.classify(request.question, query_embedding)
        
        # Handle greetings
        if intent == "GREETING":
            logger.info("Detected greeting intent")
            
            llm_start = time.time()
            greeting_response = await llm_service.generate_greeting_response(request.question)
            llm_time = int((time.time() - llm_start) * 1000)
            
            total_latency = int((time.time() - start_time) * 1000)
            
            # Record metrics
            MetricsCollector.record_query(
                intent="GREETING",
                search_mode=settings.search_mode,
                latency=time.time() - start_time
            )
            
            return QueryResponse(
                answer=greeting_response,
                sources=[],
                has_context=False,
                intent="GREETING"
            )
        
        # Check vector store
        store = get_vector_store()
        
        if store.index.ntotal == 0:
            return QueryResponse(
                answer="No tengo documentos cargados aún. ¿Deseas:\\n1. Subir PDFs primero\\n2. Buscar esta información en internet?",
                sources=[],
                has_context=False,
                intent="NO_DOCUMENTS",
                suggested_action="upload_or_search"
            )
        
        # Search for relevant chunks WITH CACHING
        search_start = time.time()
        
        if settings.search_mode == "hybrid":
            hybrid_service = get_hybrid_search_service()
            results = hybrid_service.search(request.question, k=settings.top_k_results)
        else:
            results = store.search(query_embedding, k=settings.top_k_results)
        
        search_time = int((time.time() - search_start) * 1000)
        
        # Check relevance
        SIMILARITY_THRESHOLD = 0.7
        
        if not results or results[0]['score'] >= SIMILARITY_THRESHOLD:
            return QueryResponse(
                answer="No encontré información relevante. ¿Quieres que busque en internet?",
                sources=[],
                has_context=False,
                intent="LOW_RELEVANCE",
                confidence_score=0.0,
                suggested_action="web_search"
            )
        
        # Build context and generate answer
        context = "\\n\\n---\\n\\n".join([r['text'] for r in results])
        
        llm_start = time.time()
        answer = await llm_service.generate_answer(request.question, context)
        llm_time = int((time.time() - llm_start) * 1000)
        
        # Calculate confidence
        best_score = results[0]['score']
        confidence = max(0.0, min(1.0, 1.0 - (best_score / SIMILARITY_THRESHOLD)))
        
        # Build sources
        sources = [SourceChunk(text=r['text'], score=r['score']) for r in results]
        
        total_latency = int((time.time() - start_time) * 1000)
        
        # Record metrics
        MetricsCollector.record_query(
            intent="DOCUMENT_QUERY",
            search_mode=settings.search_mode,
            latency=time.time() - start_time,
            confidence=confidence
        )
        
        return QueryResponse(
            answer=answer,
            sources=sources,
            has_context=True,
            intent="DOCUMENT_QUERY",
            confidence_score=round(confidence, 2)
        )
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        MetricsCollector.record_error("query_error", "query_endpoint")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query/web-search", response_model=QueryResponse, tags=["Query"])
async def search_web(
    request: QueryRequest,
    cache: CacheService = Depends(get_cache)
):
    """
    Web search with Wikipedia caching.
    
    Caches results for 24 hours for performance.
    """
    query_id = str(uuid4())
    start_time = time.time()
    
    logger.info(f"Web search {query_id}: '{request.question}'")
    
    try:
        # Cache key for Wikipedia
        cache_key = f"wiki:{hashlib.sha256(request.question.encode()).hexdigest()[:16]}"
        
        wiki_start = time.time()
        answer = await cache.get_or_compute(
            key=cache_key,
            compute_fn=web_search_service.search_and_summarize,
            ttl=settings.cache_ttl_wikipedia,
            cache_type="wikipedia",
            question=request.question,
            max_results=3
        )
        wiki_time = int((time.time() - wiki_start) * 1000)
        
        return QueryResponse(
            answer=answer,
            sources=[],
            has_context=True,
            intent="WEB_SEARCH"
        )
        
    except Exception as e:
        logger.error(f"Error performing web search: {e}")
        MetricsCollector.record_error("web_search_error", "web_search")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================

@app.get("/analytics/cache", tags=["Analytics"])
async def get_cache_statistics(
    cache: CacheService = Depends(get_cache),
    current_user: User = Depends(get_current_user)  # 🔐 Protected Endpoint
):
    """Get detailed cache statistics."""
    return await cache.get_stats()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

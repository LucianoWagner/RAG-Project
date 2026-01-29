"""
Metrics collection service using Prometheus client.

Tracks performance, business, and system health metrics for observability.
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from typing import Dict, Any
import time
from functools import wraps
from app.utils.logging_config import get_logger

logger = get_logger(__name__)


# ============================================================================
# PERFORMANCE METRICS
# ============================================================================

# Query latency histogram (seconds)
query_latency = Histogram(
    'rag_query_latency_seconds',
    'Time spent processing RAG queries',
    ['intent', 'search_mode'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

# Component-level latency
embedding_latency = Histogram(
    'rag_embedding_latency_seconds',
    'Time to generate embeddings',
    buckets=[0.01, 0.05, 0.1, 0.2, 0.5, 1.0]
)

vector_search_latency = Histogram(
    'rag_vector_search_latency_seconds',
    'Time for vector similarity search',
    buckets=[0.01, 0.05, 0.1, 0.2, 0.5]
)

llm_latency = Histogram(
    'rag_llm_latency_seconds',
    'Time for LLM response generation',
    ['model'],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
)

wikipedia_search_latency = Histogram(
    'rag_wikipedia_search_latency_seconds',
    'Time for Wikipedia search',
    buckets=[1.0, 2.0, 5.0, 10.0, 20.0]
)


# ============================================================================
# BUSINESS METRICS
# ============================================================================

# Query counters
queries_total = Counter(
    'rag_queries_total',
    'Total number of queries processed',
    ['intent', 'search_mode', 'cache_hit']
)

queries_by_intent = Counter(
    'rag_queries_by_intent',
    'Queries grouped by intent classification',
    ['intent']
)

documents_uploaded = Counter(
    'rag_documents_uploaded_total',
    'Total documents uploaded'
)

# Token usage tracking
tokens_used = Counter(
    'rag_tokens_used_total',
    'Total tokens used by LLM',
    ['model', 'operation']
)


# ============================================================================
# QUALITY METRICS
# ============================================================================

# Confidence score distribution
confidence_score = Histogram(
    'rag_confidence_score',
    'Distribution of confidence scores',
    buckets=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
)

# Relevance score distribution
relevance_score = Histogram(
    'rag_relevance_score',
    'Distribution of relevance scores (lower is better for L2)',
    buckets=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.5, 2.0]
)


# ============================================================================
# CACHE METRICS
# ============================================================================

cache_operations = Counter(
    'rag_cache_operations_total',
    'Cache operations (hit/miss)',
    ['operation', 'cache_type']  # operation: hit/miss, cache_type: embedding/wikipedia/search
)

cache_hit_ratio = Gauge(
    'rag_cache_hit_ratio',
    'Current cache hit ratio',
    ['cache_type']
)


# ============================================================================
# SYSTEM HEALTH METRICS
# ============================================================================

ollama_health = Gauge(
    'rag_ollama_health',
    'Ollama service health (1=up, 0=down)'
)

redis_health = Gauge(
    'rag_redis_health',
    'Redis service health (1=up, 0=down)'
)

mysql_health = Gauge(
    'rag_mysql_health',
    'MySQL service health (1=up, 0=down)'
)

vector_store_size = Gauge(
    'rag_vector_store_documents',
    'Number of documents in vector store'
)


# ============================================================================
# ERROR TRACKING
# ============================================================================

errors_total = Counter(
    'rag_errors_total',
    'Total errors encountered',
    ['error_type', 'component']
)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

class MetricsCollector:
    """Centralized metrics collection with helper methods."""
    
    @staticmethod
    def record_query(
        intent: str,
        search_mode: str,
        latency: float,
        cache_hit: bool = False,
        confidence: float = None
    ):
        """Record a complete query execution."""
        queries_total.labels(
            intent=intent,
            search_mode=search_mode,
            cache_hit=str(cache_hit)
        ).inc()
        
        queries_by_intent.labels(intent=intent).inc()
        
        query_latency.labels(
            intent=intent,
            search_mode=search_mode
        ).observe(latency)
        
        if confidence is not None:
            confidence_score.observe(confidence)
    
    @staticmethod
    def record_cache_operation(cache_type: str, is_hit: bool):
        """Record cache hit or miss."""
        operation = "hit" if is_hit else "miss"
        cache_operations.labels(
            operation=operation,
            cache_type=cache_type
        ).inc()
    
    @staticmethod
    def update_cache_hit_ratio(cache_type: str, ratio: float):
        """Update cache hit ratio gauge."""
        cache_hit_ratio.labels(cache_type=cache_type).set(ratio)
    
    @staticmethod
    def record_error(error_type: str, component: str):
        """Record an error occurrence."""
        errors_total.labels(
            error_type=error_type,
            component=component
        ).inc()
        logger.error(f"Error recorded: {error_type} in {component}")
    
    @staticmethod
    def update_health(service: str, is_healthy: bool):
        """Update service health status."""
        value = 1.0 if is_healthy else 0.0
        
        if service == "ollama":
            ollama_health.set(value)
        elif service == "redis":
            redis_health.set(value)
        elif service == "mysql":
            mysql_health.set(value)


def track_time(metric: Histogram, **labels):
    """
    Decorator to track execution time of a function.
    
    Example:
        @track_time(embedding_latency)
        async def embed_query(query: str):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                if labels:
                    metric.labels(**labels).observe(duration)
                else:
                    metric.observe(duration)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                if labels:
                    metric.labels(**labels).observe(duration)
                else:
                    metric.observe(duration)
        
        # Return appropriate wrapper based on function type
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def get_metrics() -> bytes:
    """
    Generate Prometheus metrics in text format.
    
    Returns:
        Metrics in Prometheus exposition format
    """
    return generate_latest()


# Initialize logger
logger.info("Metrics service initialized")

"""
Resilience patterns for robust error handling.

Implements circuit breaker and retry logic with exponential backoff.
"""

import asyncio
from functools import wraps
from typing import Callable, Any, TypeVar, Optional
from pybreaker import CircuitBreaker, CircuitBreakerError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)
from app.config import settings
from app.utils.logging_config import get_logger
from app.services.metrics_service import MetricsCollector

logger = get_logger(__name__)

T = TypeVar('T')


# ============================================================================
# CIRCUIT BREAKERS
# ============================================================================

# Circuit breaker for Ollama LLM service
ollama_breaker = CircuitBreaker(
    fail_max=settings.circuit_breaker_threshold,  # Open after N failures
    reset_timeout=settings.circuit_breaker_timeout,  # Try again after N seconds
    name="ollama_circuit_breaker"
)


# Circuit breaker for Redis cache
redis_breaker = CircuitBreaker(
    fail_max=5,
    reset_timeout=30,
    name="redis_circuit_breaker"
)


# ============================================================================
# DECORATORS
# ============================================================================

def with_circuit_breaker(breaker: CircuitBreaker):
    """
    Decorator to apply circuit breaker pattern.
    
    Usage:
        @with_circuit_breaker(ollama_breaker)
        async def call_ollama(...):
            ...
    
    Args:
        breaker: CircuitBreaker instance
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                result = await breaker.call_async(func, *args, **kwargs)
                return result
            except CircuitBreakerError as e:
                logger.error(f"Circuit breaker {breaker.name} is OPEN: {e}")
                MetricsCollector.record_error("circuit_breaker_open", breaker.name)
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                result = breaker.call(func, *args, **kwargs)
                return result
            except CircuitBreakerError as e:
                logger.error(f"Circuit breaker {breaker.name} is OPEN: {e}")
                MetricsCollector.record_error("circuit_breaker_open", breaker.name)
                raise
        
        # Return appropriate wrapper
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def with_retry(
    max_attempts: int = 3,
    min_wait: int = 1,
    max_wait: int = 10,
    exceptions: tuple = (Exception,)
):
    """
    Decorator to add retry logic with exponential backoff.
    
    Usage:
        @with_retry(max_attempts=3, min_wait=2, max_wait=10)
        async def unstable_function():
            ...
    
    Args:
        max_attempts: Maximum retry attempts
        min_wait: Minimum wait time (seconds)
        max_wait: Maximum wait time (seconds)
        exceptions: Tuple of exceptions to retry on
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        retry_decorator = retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
            retry=retry_if_exception_type(exceptions),
            before_sleep=before_sleep_log(logger, "WARNING"),
            reraise=True
        )
        
        return retry_decorator(func)
    
    return decorator


# ============================================================================
# TIMEOUT DECORATOR
# ============================================================================

def with_timeout(seconds: int):
    """
    Decorator to add timeout to async functions.
    
    Usage:
        @with_timeout(30)
        async def slow_function():
            ...
    
    Args:
        seconds: Timeout in seconds
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
            except asyncio.TimeoutError:
                logger.error(f"Function {func.__name__} timed out after {seconds}s")
                MetricsCollector.record_error("timeout", func.__name__)
                raise TimeoutError(f"{func.__name__} exceeded timeout of {seconds}s")
        
        return wrapper
    
    return decorator


# ============================================================================
# GRACEFUL DEGRADATION
# ============================================================================

async def with_fallback(
    primary_fn: Callable,
    fallback_fn: Callable,
    fallback_on: tuple = (Exception,)
) -> Any:
    """
    Execute primary function with fallback on failure.
    
    Example:
        result = await with_fallback(
            lambda: expensive_llm_call(),
            lambda: simple_template_response()
        )
    
    Args:
        primary_fn: Primary function to execute
        fallback_fn: Fallback function if primary fails
        fallback_on: Exceptions to trigger fallback
        
    Returns:
        Result from primary or fallback
    """
    try:
        if hasattr(primary_fn, '__await__'):
            result = await primary_fn()
        else:
            result = primary_fn()
        
        return result
        
    except fallback_on as e:
        logger.warning(f"Primary function failed, using fallback: {e}")
        
        if hasattr(fallback_fn, '__await__'):
            result = await fallback_fn()
        else:
            result = fallback_fn()
        
        return result


# ============================================================================
# RATE LIMITING
# ============================================================================

class TokenBucket:
    """
    Token bucket rate limiter.
    
    Usage:
        limiter = TokenBucket(capacity=10, refill_rate=1.0)
        
        async def endpoint():
            await limiter.acquire()
            # Process request
    """
    
    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize token bucket.
        
        Args:
            capacity: Maximum tokens
            refill_rate: Tokens per second
        """
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate
        self.last_refill = asyncio.get_event_loop().time()
        self._lock = asyncio.Lock()
    
    async def acquire(self, tokens: int = 1) -> bool:
        """
        Acquire tokens from bucket.
        
        Args:
            tokens: Number of tokens to acquire
            
        Returns:
            True if acquired, False otherwise
        """
        async with self._lock:
            await self._refill()
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            else:
                logger.warning("Rate limit exceeded")
                MetricsCollector.record_error("rate_limit_exceeded", "token_bucket")
                return False
    
    async def _refill(self):
        """Refill tokens based on elapsed time."""
        now = asyncio.get_event_loop().time()
        elapsed = now - self.last_refill
        
        new_tokens = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + new_tokens)
        self.last_refill = now


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_circuit_breaker_status() -> dict:
    """
    Get status of all circuit breakers.
    
    Returns:
        Dictionary with breaker states
    """
    return {
        "ollama": {
            "state": str(ollama_breaker.current_state),
            "fail_counter": ollama_breaker.fail_counter
        },
        "redis": {
            "state": str(redis_breaker.current_state),
            "fail_counter": redis_breaker.fail_counter
        }
    }


logger.info("Resilience patterns initialized")

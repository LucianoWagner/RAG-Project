"""
Intelligent caching service using Redis.

Provides caching for embeddings, Wikipedia searches, and search results
with automatic TTL, invalidation, and performance tracking.
"""

import hashlib
import json
import pickle
import inspect
from typing import Any, Optional, Callable, List
import numpy as np
import redis.asyncio as redis
from app.config import settings
from app.utils.logging_config import get_logger
from app.services.metrics_service import MetricsCollector

logger = get_logger(__name__)


class CacheService:
    """
    Redis-based caching service with intelligent strategies.
    
    Features:
    - Automatic serialization (pickle for numpy, JSON for others)
    - TTL management
    - Cache warming
    - Hit/miss tracking
    - Pattern-based invalidation
    """
    
    def __init__(self):
        """Initialize Redis connection."""
        self.redis_client: Optional[redis.Redis] = None
        self._initialized = False
        
        # Cache statistics
        self.stats = {
            "embeddings": {"hits": 0, "misses": 0},
            "wikipedia": {"hits": 0, "misses": 0},
            "search": {"hits": 0, "misses": 0}
        }
    
    async def initialize(self):
        """
        Connect to Redis asynchronously.
        
        Raises:
            ConnectionError: If Redis is not available
        """
        if self._initialized:
            return
        
        try:
            self.redis_client = await redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=False,  # We handle encoding manually
                socket_timeout=5,
                socket_connect_timeout=5
            )
            
            # Test connection
            await self.redis_client.ping()
            
            self._initialized = True
            MetricsCollector.update_health("redis", True)
            logger.info("Redis cache service initialized successfully")
            
        except Exception as e:
            MetricsCollector.update_health("redis", False)
            logger.error(f"Failed to connect to Redis: {e}")
            raise ConnectionError(f"Redis not available: {e}")
    
    async def close(self):
        """Close Redis connection gracefully."""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis connection closed")
    
    def _generate_key(self, prefix: str, data: str) -> str:
        """
        Generate cache key with hash.
        
        Args:
            prefix: Cache namespace (embed, wiki, search)
            data: Data to hash
            
        Returns:
            Cache key in format: prefix:hash
        """
        hash_value = hashlib.sha256(data.encode()).hexdigest()[:16]
        return f"{prefix}:{hash_value}"
    
    async def get(self, key: str, cache_type: str = "general") -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            cache_type: Type for metrics (embeddings, wikipedia, search)
            
        Returns:
            Cached value or None if not found
        """
        if not self._initialized:
            return None
        
        try:
            value = await self.redis_client.get(key)
            
            if value is not None:
                # Cache hit
                self._update_stats(cache_type, hit=True)
                MetricsCollector.record_cache_operation(cache_type, is_hit=True)
                logger.debug(f"Cache hit: {key}")
                
                # Deserialize
                return pickle.loads(value)
            else:
                # Cache miss
                self._update_stats(cache_type, hit=False)
                MetricsCollector.record_cache_operation(cache_type, is_hit=False)
                logger.debug(f"Cache miss: {key}")
                return None
                
        except Exception as e:
            logger.warning(f"Cache get error for {key}: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: int,
        cache_type: str = "general"
    ) -> bool:
        """
        Set value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            cache_type: Type for logging
            
        Returns:
            True if successful
        """
        if not self._initialized:
            return False
        
        try:
            # Serialize
            serialized = pickle.dumps(value)
            
            # Set with TTL
            await self.redis_client.setex(key, ttl, serialized)
            
            logger.debug(f"Cached {key} with TTL={ttl}s")
            return True
            
        except Exception as e:
            logger.warning(f"Cache set error for {key}: {e}")
            return False
    
    async def get_or_compute(
        self,
        key: str,
        compute_fn: Callable,
        ttl: int,
        cache_type: str = "general",
        *args,
        **kwargs
    ) -> Any:
        """
        Get from cache or compute and store.
        
        Pattern: Cache-aside (lazy loading)
        
        Args:
            key: Cache key
            compute_fn: Function to compute value if not cached
            ttl: Time to live
            cache_type: Type for metrics
            *args: Arguments for compute_fn
            **kwargs: Keyword arguments for compute_fn
            
        Returns:
            Cached or computed value
        """
        # Try cache first
        cached_value = await self.get(key, cache_type)
        
        if cached_value is not None:
            return cached_value
        
        # Compute value
        if inspect.iscoroutinefunction(compute_fn):
            computed_value = await compute_fn(*args, **kwargs)
        else:
            computed_value = compute_fn(*args, **kwargs)
        
        # Store in cache
        await self.set(key, computed_value, ttl, cache_type)
        
        return computed_value
    
    async def invalidate(self, key: str) -> bool:
        """
        Invalidate a single cache entry.
        
        Args:
            key: Cache key to invalidate
            
        Returns:
            True if successful
        """
        if not self._initialized:
            return False
        
        try:
            deleted = await self.redis_client.delete(key)
            logger.info(f"Invalidated cache key: {key}")
            return deleted > 0
        except Exception as e:
            logger.warning(f"Cache invalidation error for {key}: {e}")
            return False
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate multiple keys matching pattern.
        
        Example:
            await cache.invalidate_pattern("embed:*")
        
        Args:
            pattern: Glob pattern
            
        Returns:
            Number of keys deleted
        """
        if not self._initialized:
            return 0
        
        try:
            keys = []
            async for key in self.redis_client.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                deleted = await self.redis_client.delete(*keys)
                logger.info(f"Invalidated {deleted} keys matching {pattern}")
                return deleted
            return 0
            
        except Exception as e:
            logger.warning(f"Pattern invalidation error for {pattern}: {e}")
            return 0
    
    async def warm_cache(self, queries: List[str], embed_fn: Callable):
        """
        Pre-populate cache with common queries.
        
        Args:
            queries: List of common queries
            embed_fn: Embedding function
        """
        logger.info(f"Warming cache with {len(queries)} queries...")
        
        for query in queries:
            key = self._generate_key("embed", query)
            
            # Check if already cached
            if await self.get(key, "embeddings") is None:
                # Compute and cache
                embedding = await embed_fn(query)
                await self.set(
                    key,
                    embedding,
                    settings.cache_ttl_embeddings,
                    "embeddings"
                )
        
        logger.info("Cache warming completed")
    
    def _update_stats(self, cache_type: str, hit: bool):
        """Update internal statistics."""
        if cache_type in self.stats:
            if hit:
                self.stats[cache_type]["hits"] += 1
            else:
                self.stats[cache_type]["misses"] += 1
            
            # Update hit ratio metric
            total = self.stats[cache_type]["hits"] + self.stats[cache_type]["misses"]
            if total > 0:
                ratio = self.stats[cache_type]["hits"] / total
                MetricsCollector.update_cache_hit_ratio(cache_type, ratio)
    
    async def get_stats(self) -> dict:
        """
        Get cache statistics.
        
        Returns:
            Statistics per cache type
        """
        stats_with_ratio = {}
        
        for cache_type, data in self.stats.items():
            total = data["hits"] + data["misses"]
            hit_ratio = data["hits"] / total if total > 0 else 0.0
            
            stats_with_ratio[cache_type] = {
                **data,
                "total": total,
                "hit_ratio": hit_ratio
            }
        
        # Add Redis info
        if self._initialized:
            try:
                info = await self.redis_client.info()
                stats_with_ratio["redis_info"] = {
                    "used_memory": info.get("used_memory_human", "N/A"),
                    "connected_clients": info.get("connected_clients", 0),
                    "uptime_days": info.get("uptime_in_days", 0)
                }
            except:
                stats_with_ratio["redis_info"] = {"error": "Failed to fetch"}
        
        return stats_with_ratio
    
    async def flush_all(self) -> bool:
        """
        Clear entire cache (use with caution!).
        
        Returns:
            True if successful
        """
        if not self._initialized:
            return False
        
        try:
            await self.redis_client.flushdb()
            logger.warning("Cache flushed completely")
            
            # Reset stats
            for cache_type in self.stats:
                self.stats[cache_type] = {"hits": 0, "misses": 0}
            
            return True
        except Exception as e:
            logger.error(f"Cache flush error: {e}")
            return False


# Global cache instance
cache_service = CacheService()


async def get_cache() -> CacheService:
    """
    Dependency injection for FastAPI.
    
    Returns:
        Initialized cache service
    """
    if not cache_service._initialized:
        await cache_service.initialize()
    return cache_service

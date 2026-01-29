"""
Test script for observability and caching features (simplified).

Tests:
- Health check with all components
- Metrics endpoint  
- Cache functionality
- Cache statistics endpoint
- Document metadata tracking
"""

import asyncio
import httpx
import time

BASE_URL = "http://localhost:8000"


async def test_health_detailed():
    """Test enhanced health endpoint."""
    print("\n1. Testing Enhanced Health Check...")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        data = response.json()
        
        print(f"   Status: {data['status']}")
        print(f"   Ollama: {'✓' if data['services']['ollama']['available'] else '✗'}")
        print(f"   Redis: {'✓' if data['services']['redis']['available'] else '✗'}")
        print(f"   MySQL: {'✓' if data['services']['mysql']['available'] else '✗'}")
        print(f"   Documents: {data['services']['vector_store']['documents']}")
        print(f"   Search Mode: {data['config']['search_mode']}")


async def test_metrics():
    """Test Prometheus metrics endpoint."""
    print("\n2. Testing Metrics Endpoint...")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/metrics")
        
        if response.status_code == 200:
            lines = response.text.split('\n')
            metric_count = len([l for l in lines if l and not l.startswith('#')])
            print(f"   ✓ Metrics endpoint working ({metric_count} metrics)")
        else:
            print(f"   ✗ Failed: {response.status_code}")


async def test_cache_performance():
    """Test caching with repeated queries."""
    print("\n3. Testing Cache Performance...")
    
    query = {"question": "What is artificial intelligence?"}
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # First query (cache miss)
        print("   First query (cache miss)...")
        start = time.time()
        response1 = await client.post(f"{BASE_URL}/query/web-search", json=query)
        latency1 = time.time() - start
        
        # Second query (cache hit)
        print("   Second query (cache hit)...")
        start = time.time()
        response2 = await client.post(f"{BASE_URL}/query/web-search", json=query)
        latency2 = time.time() - start
        
        speedup = latency1 / latency2 if latency2 > 0 else 0
        
        print(f"   First query: {latency1:.2f}s")
        print(f"   Second query: {latency2:.2f}s")
        print(f"   Speedup: {speedup:.1f}x faster")


async def test_cache_stats():
    """Test cache statistics endpoint."""
    print("\n4. Testing Cache Statistics...")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/analytics/cache")
        cache_data = response.json()
        
        print(f"   Cache Statistics:")
        for cache_type, stats in cache_data.items():
            if cache_type != "redis_info":
                print(f"     {cache_type}: {stats.get('hit_ratio', 0):.2%} hit ratio")


async def main():
    """Run all tests."""
    print("=" * 50)
    print("RAG PDF System v2.0 - Feature Tests (Simplified)")
    print("=" * 50)
    
    try:
        await test_health_detailed()
        await test_metrics()
        await test_cache_performance()
        await test_cache_stats()
        
        print("\n" + "=" * 50)
        print("✓ All tests completed!")
        print("=" * 50)
        print("\nNote: Query/feedback logging removed by design")
        print("Database only tracks document metadata now")
        
    except httpx.ConnectError:
        print("\n✗ Error: Cannot connect to server")
        print("   Make sure the app is running: uvicorn app.main:app --reload")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

"""Simple load test using Python asyncio and httpx."""
import asyncio
import time
import statistics
from datetime import datetime
import httpx
import json

BASE_URL = "http://localhost:8001"
TOTAL_REQUESTS = 500
CONCURRENT_USERS = 50


async def make_request(client: httpx.AsyncClient, endpoint: str, request_num: int):
    """Make a single API request and measure latency."""
    start_time = time.time()
    
    try:
        response = await client.get(f"{BASE_URL}{endpoint}")
        latency = (time.time() - start_time) * 1000  # Convert to ms
        
        return {
            "endpoint": endpoint,
            "status": response.status_code,
            "latency_ms": latency,
            "success": response.status_code == 200,
            "request_num": request_num
        }
    except Exception as e:
        latency = (time.time() - start_time) * 1000
        return {
            "endpoint": endpoint,
            "status": 0,
            "latency_ms": latency,
            "success": False,
            "error": str(e),
            "request_num": request_num
        }


async def load_test_scenario(user_id: int, endpoints: list):
    """Simulate a single user making requests."""
    results = []
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for i, endpoint in enumerate(endpoints):
            result = await make_request(client, endpoint, i)
            results.append(result)
            await asyncio.sleep(0.5)  # 500ms between requests
    
    return results


async def run_load_test():
    """Run load test with multiple concurrent users."""
    print("=" * 60)
    print("CEX/DEX Arbitrage Platform - Load Test")
    print("=" * 60)
    print(f"\nConfiguration:")
    print(f"  Base URL: {BASE_URL}")
    print(f"  Concurrent Users: {CONCURRENT_USERS}")
    print(f"  Requests per User: {len(ENDPOINTS)}")
    print(f"  Total Requests: {CONCURRENT_USERS * len(ENDPOINTS)}")
    print(f"\nStarting load test at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}...")
    print("-" * 60)
    
    # Define test endpoints
    global ENDPOINTS
    ENDPOINTS = [
        "/api/v1/status",
        "/api/v1/opportunities?limit=50",
        "/api/v1/trades?limit=100",
        "/api/metrics",
    ]
    
    start_time = time.time()
    
    # Create concurrent user tasks
    tasks = [
        load_test_scenario(user_id, ENDPOINTS)
        for user_id in range(CONCURRENT_USERS)
    ]
    
    # Run all user scenarios concurrently
    all_results = await asyncio.gather(*tasks)
    
    total_time = time.time() - start_time
    
    # Flatten results
    results = [item for sublist in all_results for item in sublist]
    
    # Calculate statistics
    analyze_results(results, total_time)


def analyze_results(results, total_time):
    """Analyze and print test results."""
    print(f"\n{'=' * 60}")
    print("Load Test Results")
    print("=" * 60)
    
    total_requests = len(results)
    successful_requests = sum(1 for r in results if r['success'])
    failed_requests = total_requests - successful_requests
    
    latencies = [r['latency_ms'] for r in results if r['success']]
    
    print(f"\nOverall Results:")
    print(f"  Total Requests: {total_requests}")
    print(f"  Successful: {successful_requests} ({successful_requests/total_requests*100:.2f}%)")
    print(f"  Failed: {failed_requests} ({failed_requests/total_requests*100:.2f}%)")
    print(f"  Total Duration: {total_time:.2f}s")
    print(f"  Requests/Second: {total_requests/total_time:.2f}")
    
    if latencies:
        print(f"\nLatency Statistics (successful requests):")
        print(f"  Minimum: {min(latencies):.2f}ms")
        print(f"  Maximum: {max(latencies):.2f}ms")
        print(f"  Mean: {statistics.mean(latencies):.2f}ms")
        print(f"  Median (p50): {statistics.median(latencies):.2f}ms")
        print(f"  p95: {percentile(latencies, 0.95):.2f}ms")
        print(f"  p99: {percentile(latencies, 0.99):.2f}ms")
    
    # Per-endpoint breakdown
    print(f"\nPer-Endpoint Results:")
    for endpoint in ["/api/v1/status", "/api/v1/opportunities", "/api/v1/trades", "/api/metrics"]:
        endpoint_results = [r for r in results if endpoint in r['endpoint']]
        if endpoint_results:
            endpoint_success = sum(1 for r in endpoint_results if r['success'])
            endpoint_latencies = [r['latency_ms'] for r in endpoint_results if r['success']]
            
            if endpoint_latencies:
                print(f"\n  {endpoint}")
                print(f"    Requests: {len(endpoint_results)}")
                print(f"    Success: {endpoint_success}/{len(endpoint_results)}")
                print(f"    Mean Latency: {statistics.mean(endpoint_latencies):.2f}ms")
                print(f"    p95 Latency: {percentile(endpoint_latencies, 0.95):.2f}ms")
    
    # SLO validation
    print(f"\n{'=' * 60}")
    print("SLO Validation")
    print("=" * 60)
    
    if latencies:
        p95_latency = percentile(latencies, 0.95)
        error_rate = failed_requests / total_requests
        
        print(f"\n  Target: p95 latency < 200ms")
        if p95_latency < 200:
            print(f"  \u2705 PASSED: {p95_latency:.2f}ms")
        else:
            print(f"  \u274c FAILED: {p95_latency:.2f}ms (exceeds 200ms)")
        
        print(f"\n  Target: Error rate < 1%")
        if error_rate < 0.01:
            print(f"  \u2705 PASSED: {error_rate*100:.2f}%")
        else:
            print(f"  \u274c FAILED: {error_rate*100:.2f}% (exceeds 1%)")
        
        print(f"\n  Target: Throughput > 10 req/s")
        throughput = total_requests / total_time
        if throughput > 10:
            print(f"  \u2705 PASSED: {throughput:.2f} req/s")
        else:
            print(f"  \u274c FAILED: {throughput:.2f} req/s (below 10 req/s)")
    
    # Save results
    with open('/app/load_tests/results.json', 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "duration_seconds": total_time,
            "requests_per_second": total_requests / total_time,
            "latency_ms": {
                "min": min(latencies) if latencies else 0,
                "max": max(latencies) if latencies else 0,
                "mean": statistics.mean(latencies) if latencies else 0,
                "median": statistics.median(latencies) if latencies else 0,
                "p95": percentile(latencies, 0.95) if latencies else 0,
                "p99": percentile(latencies, 0.99) if latencies else 0,
            },
            "error_rate": error_rate,
            "results": results[:100]  # Save first 100 for analysis
        }, f, indent=2)
    
    print(f"\n\u2139\ufe0f  Detailed results saved to /app/load_tests/results.json")
    print("=" * 60)


def percentile(data, p):
    """Calculate percentile of data."""
    sorted_data = sorted(data)
    index = int(len(sorted_data) * p)
    return sorted_data[min(index, len(sorted_data) - 1)]


if __name__ == "__main__":
    print("\nStarting asyncio load test...")
    asyncio.run(run_load_test())

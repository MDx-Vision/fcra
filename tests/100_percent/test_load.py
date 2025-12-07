#!/usr/bin/env python3
"""Load testing - simulate concurrent users"""

import asyncio
import aiohttp
import time
import json
from datetime import datetime

BASE_URL = "http://localhost:5001"

async def load_test():
    """Simulate 100 concurrent requests"""

    urls = [
        "/",
        "/dashboard",
        "/dashboard/clients",
        "/dashboard/cases",
        "/api/clients",
        "/api/settlements",
    ]

    results = {
        "timestamp": datetime.now().isoformat(),
        "requests": [],
        "total_requests": 0,
        "successful": 0,
        "failed": 0,
        "avg_time": 0,
        "max_time": 0,
        "min_time": float('inf')
    }

    async def fetch(session, url):
        start = time.time()
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                await response.text()
                elapsed = time.time() - start
                return {
                    "url": url,
                    "status": response.status,
                    "time": elapsed,
                    "success": response.status == 200
                }
        except Exception as e:
            return {
                "url": url,
                "status": 0,
                "time": time.time() - start,
                "success": False,
                "error": str(e)[:50]
            }

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting load test...")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Testing {len(urls)} URLs with ~100 concurrent requests")

    connector = aiohttp.TCPConnector(limit=50)
    async with aiohttp.ClientSession(connector=connector) as session:
        # Create 100 requests spread across URLs
        tasks = []
        for _ in range(17):  # 17 * 6 = 102 requests
            for url in urls:
                tasks.append(fetch(session, f"{BASE_URL}{url}"))

        # Execute all concurrently
        start_time = time.time()
        request_results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time

    # Analyze results
    times = []
    for r in request_results:
        results["total_requests"] += 1
        if r["success"]:
            results["successful"] += 1
        else:
            results["failed"] += 1
        times.append(r["time"])
        results["requests"].append(r)

    results["avg_time"] = sum(times) / len(times) if times else 0
    results["max_time"] = max(times) if times else 0
    results["min_time"] = min(times) if times else 0
    results["total_time"] = total_time
    results["requests_per_second"] = results["total_requests"] / total_time if total_time > 0 else 0

    # Save results
    with open("tests/100_percent/load_results.json", "w") as f:
        # Don't save all individual requests to keep file small
        save_results = {k: v for k, v in results.items() if k != "requests"}
        save_results["sample_requests"] = results["requests"][:10]
        json.dump(save_results, f, indent=2)

    print("\n" + "=" * 40)
    print("LOAD TEST RESULTS")
    print("=" * 40)
    print(f"Total Requests: {results['total_requests']}")
    print(f"Successful: {results['successful']}")
    print(f"Failed: {results['failed']}")
    print(f"Total Time: {total_time:.2f}s")
    print(f"Requests/Second: {results['requests_per_second']:.1f}")
    print(f"Avg Response Time: {results['avg_time']*1000:.1f}ms")
    print(f"Max Response Time: {results['max_time']*1000:.1f}ms")
    print(f"Min Response Time: {results['min_time']*1000:.1f}ms")

    if results["failed"] > 0:
        print(f"\nFailed requests: {results['failed']}")

    return results

if __name__ == "__main__":
    asyncio.run(load_test())

#!/usr/bin/env python3
"""Test ALL routes for basic availability"""

import requests
import time
import re
from collections import defaultdict

BASE_URL = "http://localhost:5001"

# Extract routes from the routes file
def extract_routes():
    routes = []
    with open('tests/exhaustive/all_routes.txt', 'r') as f:
        for line in f:
            # Extract route pattern from @app.route('/path')
            match = re.search(r"@app\.route\('([^']+)'", line)
            if match:
                route = match.group(1)
                # Skip routes with parameters for now (test separately)
                if '<' not in route:
                    routes.append(route)
    return routes

def test_all_routes():
    routes = extract_routes()
    print(f"Testing {len(routes)} static routes...")

    session = requests.Session()
    results = {
        "total": len(routes),
        "passed": 0,
        "failed": 0,
        "errors": []
    }

    start_time = time.time()

    for route in routes:
        try:
            resp = session.get(f"{BASE_URL}{route}", timeout=5)
            if resp.status_code == 200:
                results["passed"] += 1
                print(f"  [PASS] {route}")
            else:
                results["failed"] += 1
                results["errors"].append({"route": route, "status": resp.status_code})
                print(f"  [FAIL] {route} - Status {resp.status_code}")
        except Exception as e:
            results["failed"] += 1
            results["errors"].append({"route": route, "error": str(e)})
            print(f"  [ERROR] {route} - {e}")

    elapsed = time.time() - start_time

    print("\n" + "=" * 60)
    print("ROUTE TESTING SUMMARY")
    print("=" * 60)
    print(f"Total Routes: {results['total']}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    print(f"Pass Rate: {results['passed']/results['total']*100:.1f}%")
    print(f"Time: {elapsed:.1f}s")

    if results["errors"]:
        print("\nFailed Routes:")
        for err in results["errors"][:20]:
            print(f"  - {err}")

    return results

if __name__ == "__main__":
    test_all_routes()

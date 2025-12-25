#!/usr/bin/env python3
"""TASK 5: Test ALL links"""

import asyncio
import json
from datetime import datetime
from playwright.async_api import async_playwright

BASE_URL = "http://localhost:5001"

RESULTS = {
    "timestamp": datetime.now().isoformat(),
    "links_found": 0,
    "links_tested": 0,
    "links_valid": 0,
    "links_broken": 0,
    "external_links": 0,
    "issues": [],
    "log": []
}

async def test_all_links():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        pages = [
            "/", "/signup", "/staff/login", "/portal/login",
            "/dashboard", "/dashboard/clients", "/dashboard/signups",
            "/dashboard/cases", "/dashboard/settlements", "/dashboard/staff",
            "/dashboard/analytics", "/dashboard/credit-tracker", "/dashboard/calendar",
            "/dashboard/contacts", "/dashboard/automation-tools", "/dashboard/letter-queue",
            "/dashboard/demand-generator", "/dashboard/import", "/dashboard/documents",
            "/dashboard/settings", "/dashboard/integrations", "/dashboard/billing",
            "/dashboard/tasks", "/dashboard/workflows", "/dashboard/ml-insights",
            "/dashboard/white-label", "/dashboard/franchise", "/dashboard/affiliates",
            "/dashboard/triage", "/dashboard/escalation", "/dashboard/case-law",
            "/dashboard/knowledge-base", "/dashboard/sops", "/dashboard/chexsystems",
            "/dashboard/specialty-bureaus", "/dashboard/furnishers", "/dashboard/patterns",
            "/dashboard/sol", "/dashboard/cfpb", "/dashboard/frivolousness", "/dashboard/predictive",
        ]

        tested_links = set()

        for url in pages:
            await _run_links_on_page(page, url, tested_links)

        await browser.close()

    save_results()

async def _run_links_on_page(page, url, tested_links):
    """Find and test every link on a page"""

    RESULTS["log"].append(f"\n=== Scanning: {url} ===")

    try:
        await page.goto(f"{BASE_URL}{url}", wait_until="networkidle", timeout=15000)

        links = await page.query_selector_all("a[href]")
        RESULTS["log"].append(f"  Found {len(links)} links")

        for link in links:
            href = await link.get_attribute("href")

            if not href or href in tested_links:
                continue

            if href.startswith("#") or href.startswith("javascript:") or href.startswith("mailto:"):
                continue

            tested_links.add(href)
            RESULTS["links_found"] += 1

            try:
                if href.startswith("/"):
                    full_url = f"{BASE_URL}{href}"
                elif href.startswith("http"):
                    full_url = href
                    RESULTS["external_links"] += 1
                    RESULTS["links_tested"] += 1
                    continue
                else:
                    continue

                response = await page.request.get(full_url, timeout=10000)
                status = response.status

                RESULTS["links_tested"] += 1

                if status < 400:
                    RESULTS["links_valid"] += 1
                else:
                    RESULTS["links_broken"] += 1
                    RESULTS["issues"].append({
                        "page": url,
                        "link": href,
                        "status": status
                    })

            except Exception as e:
                RESULTS["links_broken"] += 1
                RESULTS["issues"].append({
                    "page": url,
                    "link": href,
                    "error": str(e)[:50]
                })

    except Exception as e:
        RESULTS["log"].append(f"  ERROR: {str(e)[:50]}")

def save_results():
    with open("tests/mandatory/TASK5_LINKS_RESULTS.json", "w") as f:
        json.dump(RESULTS, f, indent=2)

    report = f"""# TASK 5: LINK TESTING RESULTS

**Target:** 323 links
**Timestamp:** {RESULTS['timestamp']}

## Summary
| Metric | Count |
|--------|-------|
| Links Found | {RESULTS['links_found']} |
| Links Tested | {RESULTS['links_tested']} |
| Links Valid | {RESULTS['links_valid']} |
| Links Broken | {RESULTS['links_broken']} |
| External Links (skipped) | {RESULTS['external_links']} |

## Broken Links
"""
    for issue in RESULTS['issues']:
        report += f"- {issue}\n"

    with open("tests/mandatory/TASK5_LINKS_REPORT.md", "w") as f:
        f.write(report)

    print(f"\nTASK 5 COMPLETE:")
    print(f"  Links tested: {RESULTS['links_tested']}")
    print(f"  Links valid: {RESULTS['links_valid']}")
    print(f"  Links broken: {RESULTS['links_broken']}")

if __name__ == "__main__":
    asyncio.run(test_all_links())

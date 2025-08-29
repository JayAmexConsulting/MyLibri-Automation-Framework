# full_crawl_broken_links.py

import pytest
from playwright.sync_api import sync_playwright
import csv, json
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse
from collections import deque

# --- Configuration ---
URL = "https://mylibribooks.com"
EMAIL = "cpot.tea@gmail.com"
PASSWORD = "Moniwyse!400"
TIMEOUT = 15000  # Default timeout in milliseconds

def crawl(page, start_url, visited):
    """
    Crawls a website from a starting URL, staying within the same domain.
    Returns a list of {"url": ..., "status": ...}.
    """
    to_visit = deque([start_url])  # Using a deque for efficient queue operations
    results = []
    base_url = f"{urlparse(start_url).scheme}://{urlparse(start_url).netloc}"

    print(f"Starting crawl from: {start_url}")

    while to_visit:
        current_url = to_visit.popleft() # Use popleft() for a breadth-first search (queue behavior)

        # Skip if already visited to prevent infinite loops and redundant checks.
        if current_url in visited:
            continue
        visited.add(current_url)

        try:
            # Navigate to the page and wait for the DOM to be ready
            print(f"🔎 Visiting {current_url}")
            response = page.goto(current_url, wait_until="domcontentloaded", timeout=TIMEOUT)
            status = response.status if response else "No response"

            print(f"✅ {current_url} -> Status: {status}")
            results.append({"url": current_url, "status": status})

            # Find all links on the current page
            anchors = page.locator("a")
            count = anchors.count()
            
            for i in range(count):
                try:
                    href = anchors.nth(i).get_attribute("href")
                    if not href:
                        continue

                    abs_url = urljoin(current_url, href)

                    # Normalize the URL to remove fragments and query parameters for better comparison
                    normalized_url = urljoin(base_url, urlparse(abs_url).path)

                    # Add to the queue only if it's within the same domain and not yet visited.
                    if normalized_url.startswith(base_url) and normalized_url not in visited:
                        to_visit.append(normalized_url)
                except Exception as e:
                    print(f"⚠️ Error processing link {href}: {e}")
                    continue

        except Exception as e:
            print(f"❌ Error visiting {current_url}: {e}")
            results.append({"url": current_url, "status": f"Error: {e}"})
            continue

    return results

@pytest.mark.fast
def test_full_crawl_broken_links():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    Path("test_reports").mkdir(exist_ok=True)

    all_results = []
    visited_urls = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_default_timeout(TIMEOUT)

        # --- Phase 1: Before Login ---
        print("\n=== PHASE 1: Crawling before login ===\n")
        
        # Crawl from the root and the public blog page
        public_results = crawl(page, URL, visited_urls)
        all_results.extend([{"phase": "before_login", **r} for r in public_results])
        
        blog_results_public = crawl(page, f"{URL}/blog", visited_urls)
        all_results.extend([{"phase": "before_login", **r} for r in blog_results_public])

        # --- Phase 2: After Login ---
        print("\n=== PHASE 2: Logging in and crawling ===\n")
        page.goto(URL)
        page.click("text=Sign In")
        page.wait_for_url("**/signin")
        page.fill("input[type='email']", EMAIL)
        page.fill("input[type='password']", PASSWORD)
        page.click("button:has-text('Login')")
        page.wait_for_url("**/home/dashboard**", timeout=20000)

        # Crawl from the dashboard
        private_results_dashboard = crawl(page, f"{URL}/home/dashboard", visited_urls)
        all_results.extend([{"phase": "after_login", **r} for r in private_results_dashboard])
        
        # Explicitly crawl the other specified pages
        private_results_genre = crawl(page, f"{URL}/home/genre", visited_urls)
        all_results.extend([{"phase": "after_login", **r} for r in private_results_genre])
        
        private_results_discover = crawl(page, f"{URL}/home/discover", visited_urls)
        all_results.extend([{"phase": "after_login", **r} for r in private_results_discover])
        
        private_results_library = crawl(page, f"{URL}/home/library", visited_urls)
        all_results.extend([{"phase": "after_login", **r} for r in private_results_library])
        
        # Crawl the blog page again after login
        blog_results_private = crawl(page, f"{URL}/blog", visited_urls)
        all_results.extend([{"phase": "after_login", **r} for r in blog_results_private])
        
        # --- Phase 3: After Logout ---
        print("\n=== PHASE 3: Logging out and crawling ===\n")
        try:
            # Assuming a "Logout" button or link exists.
            page.click("text=Logout")
            page.wait_for_url("**", timeout=10000)
        except Exception as e:
            print(f"⚠️ Could not log out automatically: {e}")
        
        post_logout_results = crawl(page, URL, visited_urls)
        all_results.extend([{"phase": "after_logout", **r} for r in post_logout_results])

        # --- Export Results ---
        print("\n--- Exporting Results ---\n")
        csv_path = f"test_reports/full_broken_links_{timestamp}.csv"
        json_path = f"test_reports/full_broken_links_{timestamp}.json"
        html_path = f"test_reports/full_broken_links_{timestamp}.html"

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["phase", "url", "status"])
            writer.writeheader()
            writer.writerows(all_results)

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(all_results, f, indent=2)

        with open(html_path, "w", encoding="utf-8") as f:
            f.write("<html><head><title>Full Broken Links Report</title></head><body>")
            f.write("<h1>🔗 Full Broken Link Check</h1><ul>")
            for item in all_results:
                # Assuming status codes >= 400 are failures
                color = "red" if isinstance(item['status'], int) and item['status'] >= 400 else "green"
                f.write(f"<li style='color:{color}'>[{item['phase']}] {item['url']} → {item['status']}</li>")
            f.write("</ul></body></html>")

        print("✅ Export complete:")
        print(f" - CSV: {csv_path}")
        print(f" - JSON: {json_path}")
        print(f" - HTML: {html_path}")
        
        browser.close()

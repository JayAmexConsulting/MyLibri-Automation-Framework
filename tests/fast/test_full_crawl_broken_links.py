import pytest
from playwright.sync_api import sync_playwright
import csv, json
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

URL = "https://mylibribooks.com"
EMAIL = "cpot.tea@gmail.com"
PASSWORD = "Moniwyse!400"

def crawl(page, start_url, base_url, visited):
    """
    Crawl from start_url, staying within base_url domain.
    Returns a list of {"url": ..., "status": ...}.
    """
    to_visit = [start_url]
    results = []

    while to_visit:
        current_url = to_visit.pop()
        if current_url in visited:
            continue
        visited.add(current_url)

        try:
            response = page.goto(current_url, wait_until="domcontentloaded")
            status = response.status if response else "No response"

            print(f"🔎 {current_url} → {status}")
            results.append({"url": current_url, "status": status})

            # Collect new links
            anchors = page.locator("a")
            count = anchors.count()
            for i in range(count):
                href = anchors.nth(i).get_attribute("href")
                if not href:
                    continue

                abs_url = urljoin(current_url, href)
                # Stay inside same site
                if abs_url.startswith(base_url) and abs_url not in visited:
                    to_visit.append(abs_url)

        except Exception as e:
            print(f"⚠️ Error visiting {current_url}: {e}")
            results.append({"url": current_url, "status": f"Error: {e}"})
            continue

    return results

@pytest.mark.fast
def test_full_crawl_broken_links():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    Path("test_reports").mkdir(exist_ok=True)

    all_results = []
    visited = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.set_default_timeout(15000)

        # --- Phase 1: Before Login ---
        print("\n🌍 Crawling before login...")
        public_results = crawl(page, URL, URL, visited)
        all_results.extend([{"phase": "before_login", **r} for r in public_results])

        # --- Phase 2: After Login ---
        print("\n🔑 Logging in...")
        page.goto(URL)
        page.click("text=Sign In")
        page.wait_for_url("**/signin")
        page.fill("input[type='email']", EMAIL)
        page.fill("input[type='password']", PASSWORD)
        page.click("button:has-text('Login')")
        page.wait_for_url("**/home/dashboard**", timeout=20000)

        print("\n🔒 Crawling after login...")
        private_results = crawl(page, f"{URL}/home/dashboard", URL, visited)
        all_results.extend([{"phase": "after_login", **r} for r in private_results])

        # --- Phase 3: After Logout ---
        print("\n🚪 Logging out...")
        try:
            # Adjust selector to your app's logout button/link
            page.click("text=Logout")
            page.wait_for_url("**", timeout=10000)
        except Exception as e:
            print(f"⚠️ Could not log out automatically: {e}")

        print("\n🌍 Crawling after logout...")
        post_logout_results = crawl(page, URL, URL, visited)
        all_results.extend([{"phase": "after_logout", **r} for r in post_logout_results])

        # --- Export Results ---
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
                color = "red" if isinstance(item['status'], int) and item['status'] >= 400 else "green"
                f.write(f"<li style='color:{color}'>[{item['phase']}] {item['url']} → {item['status']}</li>")
            f.write("</ul></body></html>")

        print("\n✅ Crawl complete:")
        print(f" - CSV:  {csv_path}")
        print(f" - JSON: {json_path}")
        print(f" - HTML: {html_path}")

        browser.close()

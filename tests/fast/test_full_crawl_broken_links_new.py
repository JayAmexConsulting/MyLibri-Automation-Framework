import pytest
from playwright.sync_api import sync_playwright
import csv, json
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse


URL = "https://mylibribooks.com"
EMAIL = "cpot.tea@gmail.com"
PASSWORD = "Moniwyse!400"


def check_link_status(link):
    """Return HTTP status code for a link."""
    try:
        response = requests.head(link, allow_redirects=True, timeout=10)
        return response.status_code
    except Exception:
        try:
            response = requests.get(link, allow_redirects=True, timeout=10)
            return response.status_code
        except Exception:
            return None


def crawl(page, start_url, base_url, visited, depth=1):
    """
    Crawl <a href> links within the same domain.
    depth = how many levels to crawl (1 = only this page, >1 = recursive).
    """
    results = []
    domain = urlparse(base_url).netloc

    if start_url in visited:
        return results
    visited.add(start_url)

    try:
        page.goto(start_url, timeout=20000)
    except Exception as e:
        results.append({"url": start_url, "status": None, "error": str(e)})
        return results

    status = check_link_status(start_url)
    results.append({"url": start_url, "status": status})

    # stop if not recursive
    if depth <= 0:
        return results

    links = page.eval_on_selector_all("a", "elements => elements.map(e => e.href)")
    for link in links:
        if not link or link.startswith(("mailto:", "tel:", "javascript:")):
            continue

        parsed = urlparse(link)
        if parsed.netloc and parsed.netloc != domain:
            continue
        absolute = urljoin(base_url, parsed.path or "/")
        if absolute not in visited:
            results.extend(crawl(page, absolute, base_url, visited, depth - 1))
    return results


@pytest.mark.fast
def test_broken_links():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    Path("test_reports").mkdir(exist_ok=True)

    all_results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, slow_mo=100)
        page = browser.new_page()
        page.set_default_timeout(10000)

        # -------- BEFORE LOGIN --------
        print("\n🌍 Crawling before login...")
        visited = set()
        public_results = crawl(page, URL, URL, visited, depth=1)
        all_results.extend([{"phase": "before_login", **r} for r in public_results])

        # -------- LOGIN --------
        print("\n🔑 Logging in...")
        page.goto(URL)
        page.click("text=Sign In")
        page.wait_for_url("**/signin")
        page.fill("input[type='email']", EMAIL)
        page.fill("input[type='password']", PASSWORD)
        page.click("button:has-text('Login')")
        page.wait_for_url("**/home/dashboard")

        # -------- AFTER LOGIN --------
        print("\n🔐 Crawling after login...")
        visited = set()
        after_login_seeds = [
            f"{URL}/home/dashboard",
            f"{URL}/home/library",
            f"{URL}/home/discover",
            f"{URL}/home/profile",
            f"{URL}/home/wallet",
            f"{URL}/home/books",
            f"{URL}/termsOfUse"
        ]
        for seed in after_login_seeds:
            private_results = crawl(page, seed, URL, visited, depth=1)
            all_results.extend([{"phase": "after_login", **r} for r in private_results])

        # -------- LOGOUT --------
        print("\n🚪 Logging out...")
        try:
            page.click("text=Logout")
            page.wait_for_url(URL)
        except Exception:
            print("⚠️ Logout button not found, skipping logout check.")

        # -------- AFTER LOGOUT --------
        print("\n🌍 Crawling after logout...")
        visited = set()
        logout_results = crawl(page, URL, URL, visited, depth=1)
        all_results.extend([{"phase": "after_logout", **r} for r in logout_results])

        browser.close()

    # -------- SAVE REPORTS --------
    csv_path = f"test_reports/broken_links_{timestamp}.csv"
    json_path = f"test_reports/broken_links_{timestamp}.json"
    html_path = f"test_reports/broken_links_{timestamp}.html"

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["phase", "url", "status", "error"])
        writer.writeheader()
        writer.writerows(all_results)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)

    # -------- HTML REPORT WITH SUMMARY --------
    total_links = len(all_results)
    broken_links = [r for r in all_results if r.get("status") != 200]
    total_broken = len(broken_links)
    percent_broken = round((total_broken / total_links * 100), 2) if total_links else 0

    with open(html_path, "w", encoding="utf-8") as f:
        f.write("<html><head><title>Full Broken Link Check</title></head><body>")
        f.write("<h1>🔗 Full Broken Link Check</h1>")

        # Summary Table
        f.write("<h2>📊 Summary</h2>")
        f.write("<table border='1' cellpadding='5' cellspacing='0'>")
        f.write("<tr><th>Total Links</th><th>Broken Links</th><th>% Broken</th></tr>")
        f.write(f"<tr><td>{total_links}</td><td>{total_broken}</td><td>{percent_broken}%</td></tr>")
        f.write("</table>")

        # Detailed Results
        f.write("<h2>🔍 Detailed Results</h2><ul>")
        for item in all_results:
            status_display = (
                f"<span style='color:green'>{item['status']}</span>"
                if item.get("status") == 200
                else f"<span style='color:red'>{item.get('status') or 'Error'}</span>"
            )
            f.write(f"<li>[{item['phase']}] {item['url']} → {status_display}</li>")
        f.write("</ul></body></html>")

    print("✅ Export complete:")
    print(f" - CSV:  {csv_path}")
    print(f" - JSON: {json_path}")
    print(f" - HTML: {html_path}")

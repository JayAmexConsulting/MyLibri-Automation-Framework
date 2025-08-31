import pytest
from playwright.sync_api import sync_playwright
import csv, json
from datetime import datetime
from pathlib import Path

# --- Configuration ---
URL = "https://mylibribooks.com"
BOOK_URL_BASE = f"{URL}/home/books"
EMAIL = "cpot.tea@gmail.com"
PASSWORD = "Moniwyse!400"

START_ID = 1501
MAX_ID = 2831
STOP_AFTER_CONSECUTIVE_FAILS = 30

@pytest.mark.slow
def test_long_running_broken_link_check():
    """
    Checks for broken book detail pages and outputs a report
    containing only the broken links.
    """
    print("--- Starting broken link check ---")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = Path("test_reports")
    report_dir.mkdir(exist_ok=True)
    print(f"✅ Created report directory: {report_dir}")

    with sync_playwright() as p:
        # Removed slow_mo for faster execution
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_default_timeout(15000)

        # --- Login ---
        print("🔐 Logging in...")
        page.goto(URL)
        page.click("text=Sign In")
        page.wait_for_url("**/signin", timeout=10000)
        page.fill("input[type='email']", EMAIL)
        page.fill("input[type='password']", PASSWORD)
        page.click("button:has-text('Login')")
        page.wait_for_timeout(3000)
        print("✅ Login successful.")

        broken_links = []
        failures_in_a_row = 0

        # --- Check Each Book ID ---
        print("➡️ Scanning for broken links...")
        for book_id in range(START_ID, MAX_ID + 1):
            book_url = f"{BOOK_URL_BASE}/{book_id}"
            
            try:
                page.goto(book_url, timeout=8000)
                page.wait_for_timeout(500)

                # Check for the main content to determine if the page loaded correctly
                book_title = page.locator("div.book-details h1.book-name").first.text_content().strip()
                
                # If a title is found, the link is working.
                failures_in_a_row = 0
                
            except Exception as e:
                # This block runs if an element is not found or a timeout occurs.
                failures_in_a_row += 1
                error_message = f"Failed to load page or find title: {str(e)}"
                
                broken_link_data = {
                    "id": book_id,
                    "url": book_url,
                    "status": "Broken",
                    "error": error_message
                }
                broken_links.append(broken_link_data)
                print(f"❌ Broken link found: ID {book_id} at {book_url}")
                
            if failures_in_a_row >= STOP_AFTER_CONSECUTIVE_FAILS:
                print(f"\n🛑 Stopping after {STOP_AFTER_CONSECUTIVE_FAILS} consecutive broken links.")
                break

        # --- Generate Report (Only for broken links) ---
        print("\n--- Generating reports for broken links only ---")
        csv_path = report_dir / f"broken_links_{timestamp}.csv"
        json_path = report_dir / f"broken_links_{timestamp}.json"
        html_path = report_dir / f"broken_links_{timestamp}.html"

        # CSV Report
        with open(csv_path, "w", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["id", "url", "status", "error"])
            writer.writeheader()
            writer.writerows(broken_links)

        # JSON Report
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(broken_links, f, indent=2)
            
        # HTML Report
        print("➡️ Generating HTML report...")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write("<html><head><title>Broken Link Report</title>")
            f.write("<style>")
            f.write("body { font-family: sans-serif; line-height: 1.6; padding: 20px; }")
            f.write("h1 { color: #d9534f; }")
            f.write(".broken-link { border: 1px solid #d9534f; border-radius: 8px; padding: 15px; margin-bottom: 20px; background-color: #f2dede; }")
            f.write(".url { font-weight: bold; color: #337ab7; }")
            f.write(".reason { color: #843534; font-size: 0.9em; margin-top: 10px; }")
            f.write("</style></head><body>")
            f.write("<h1><span style='color: #6c6c6c;'>🔗</span> Broken Link Report</h1>")
            f.write(f"<p>Found {len(broken_links)} broken links.</p>")
            
            if not broken_links:
                f.write("<p>✅ No broken links found.</p>")
            else:
                for link in broken_links:
                    f.write("<div class='broken-link'>")
                    f.write(f"<p><strong>ID:</strong> {link['id']}</p>")
                    f.write(f"<p><strong>URL:</strong> <a class='url' href='{link['url']}'>{link['url']}</a></p>")
                    f.write(f"<p class='reason'><strong>Reason:</strong> {link['error']}</p>")
                    f.write("</div>")
            f.write("</body></html>")
            
        print(f"✅ Report complete. View at: {html_path}")
        print("--- Test run finished ---")
        browser.close()

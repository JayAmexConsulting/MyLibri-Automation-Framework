import pytest
from playwright.sync_api import sync_playwright
import csv, json
from datetime import datetime
from pathlib import Path

URL = "https://mylibribooks.com"
EMAIL = "cpot.tea@gmail.com"
PASSWORD = "Moniwyse!400"

@pytest.mark.fast
def test_quick_check():
    """
    Test that navigates to the genre page and scrapes book counts.
    This script is self-contained and does not require a separate fixture file.
    """
    print("--- Starting test_quick_check ---")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    Path("test_reports").mkdir(exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, slow_mo=200)
        page = browser.new_page()
        page.set_default_timeout(15000)

        # --- Login ---
        print("➡️ Navigating to the login page...")
        page.goto(URL)
        page.click("text=Sign In")
        page.wait_for_url("**/signin")
        
        print("⏳ Logging in...")
        page.fill("input[type='email']", EMAIL)
        page.fill("input[type='password']", PASSWORD)
        page.click("button:has-text('Login')")
        page.wait_for_url("**/home/dashboard", timeout=20000)
        print("✅ Login successful.")

        # --- Genre Page ---
        print(f"➡️ Navigating to the genre page: {URL}/home/genre")
        page.goto(f"{URL}/home/genre")
        page.wait_for_selector("div.genre-wrapper ul li", timeout=15000)
        
        genre_elements = page.locator("div.genre-wrapper ul li")
        genre_count = genre_elements.count()
        print(f"📚 Total genre elements found: {genre_count}")

        genre_results = []
        
        for i in range(genre_count):
            # re-locate inside loop to avoid stale handles
            element = page.locator("div.genre-wrapper ul li").nth(i)
            try:
                element.wait_for(state="visible", timeout=10000)
                genre_name = element.inner_text().strip()
                
                print(f"📚 Navigating to genre: {genre_name}")
                element.click()
                
                # Count books
                book_count = 0
                book_locator = page.locator("div.book-card, div.book-item, .book")
                if book_locator.count() > 0:
                    book_locator.first.wait_for(state="visible", timeout=15000)
                    book_count = book_locator.count()
                
                print(f"📚 {genre_name}: {book_count} book(s)")
                genre_results.append({"genre": genre_name, "count": book_count})

                # Back to genre list
                print("⬅️ Going back to the genre list...")
                page.go_back(wait_until="domcontentloaded")
                page.wait_for_selector("div.genre-wrapper ul li", timeout=15000)

            except Exception as e:
                print(f"⚠️ Skipping genre index {i}: {e}")
                continue

        # --- Export ---
        print("➡️ Saving test results to files...")
        csv_path = f"test_reports/genre_book_counts_{timestamp}.csv"
        json_path = f"test_reports/genre_book_counts_{timestamp}.json"
        html_path = f"test_reports/genre_book_counts_{timestamp}.html"

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["genre", "count"])
            writer.writeheader()
            writer.writerows(genre_results)

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(genre_results, f, indent=2)

        with open(html_path, "w", encoding="utf-8") as f:
            f.write("<html><head><title>Genre Report</title></head><body>")
            f.write("<h1>📊 Genre Book Count</h1><ul>")
            for item in genre_results:
                f.write(f"<li>{item['genre']}: {item['count']} book(s)</li>")
            f.write("</ul></body></html>")

        print("✅ Export complete:")
        print(f" - CSV: {csv_path}")
        print(f" - JSON: {json_path}")
        print(f" - HTML: {html_path}")
        print("--- Test run finished ---")

        browser.close()

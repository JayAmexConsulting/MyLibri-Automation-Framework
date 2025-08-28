import pytest
from playwright.sync_api import sync_playwright
import csv, json
from datetime import datetime
from pathlib import Path

URL = "https://mylibribooks.com"
EMAIL = "cpot.tea@gmail.com"
PASSWORD = "Moniwyse!400"

@pytest.mark.fast
def test_quick_check_multi_pages():
    """
    Scrapes book counts for all genres by opening each genre in a new page (faster).
    """
    print("--- Starting test_quick_check_multi_pages ---")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    Path("test_reports").mkdir(exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, slow_mo=200)
        context = browser.new_context()
        page = context.new_page()
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

        # Collect all genre names first
        genre_names = [genre_elements.nth(i).inner_text().strip() for i in range(genre_count)]
        
        genre_results = []

        # --- Open each genre in a new page ---
        for genre_name in genre_names:
            print(f"📚 Opening genre: {genre_name}")
            genre_page = context.new_page()
            genre_page.goto(f"{URL}/home/genre")
            genre_page.wait_for_selector("div.genre-wrapper ul li", timeout=15000)

            try:
                # Click the genre
                genre_page.click(f"text={genre_name}")
                genre_page.wait_for_timeout(2000)

                # Count books
                book_locator = genre_page.locator("div.book-card, div.book-item, .book")
                book_count = book_locator.count() if book_locator.count() > 0 else 0

                print(f"   ➡️ {genre_name}: {book_count} book(s)")
                genre_results.append({"genre": genre_name, "count": book_count})

            except Exception as e:
                print(f"⚠️ Failed for {genre_name}: {e}")
                genre_results.append({"genre": genre_name, "count": 0})

            finally:
                genre_page.close()

        # --- Export ---
        print("➡️ Saving test results to files...")
        csv_path = f"test_reports/genre_book_counts_multi_{timestamp}.csv"
        json_path = f"test_reports/genre_book_counts_multi_{timestamp}.json"
        html_path = f"test_reports/genre_book_counts_multi_{timestamp}.html"

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

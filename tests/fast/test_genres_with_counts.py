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
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    Path("test_reports").mkdir(exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, slow_mo=200)
        page = browser.new_page()
        page.set_default_timeout(15000)

        # --- Login ---
        page.goto(URL)
        page.click("text=Sign In")
        page.wait_for_url("**/signin")
        page.fill("input[type='email']", EMAIL)
        page.fill("input[type='password']", PASSWORD)
        page.click("button:has-text('Login')")
        page.wait_for_url("**/home/dashboard", timeout=20000)

        # --- Genre Page ---
        page.goto(f"{URL}/home/genre")
        page.wait_for_selector("div.genre-wrapper ul li")

        genre_elements = page.locator("div.genre-wrapper ul li")
        genre_count = genre_elements.count()
        genre_results = []

        print(f"📚 Total genre elements found: {genre_count}")

        for i in range(genre_count):
            element = genre_elements.nth(i)
            try:
                genre_name = element.inner_text().strip()
                # Click into genre
                element.click()
                page.wait_for_load_state("networkidle")

                # Wait for books to appear (adjust selector to actual DOM)
                book_elements = page.locator("div.book-card, div.book-item, .book")  
                book_count = book_elements.count()

                print(f"📚 {genre_name}: {book_count} book(s)")
                genre_results.append({
                    "genre": genre_name,
                    "count": book_count
                })

                # Go back to genre page
                page.goto(f"{URL}/home/genre")
                page.wait_for_selector("div.genre-wrapper ul li")

                # Refresh locator after navigation
                genre_elements = page.locator("div.genre-wrapper ul li")

            except Exception as e:
                print(f"⚠️ Skipping genre index {i}: {e}")
                continue

        # --- Export ---
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
        print(f" - CSV:  {csv_path}")
        print(f" - JSON: {json_path}")
        print(f" - HTML: {html_path}")

        browser.close()

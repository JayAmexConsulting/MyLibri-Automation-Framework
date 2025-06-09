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
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=300)
        page = browser.new_page()
        page.goto(URL)

        # Login
        page.click("text=Sign In")
        page.wait_for_url("**/signin")
        page.fill("input[type='email']", EMAIL)
        page.fill("input[type='password']", PASSWORD)
        page.click("button:has-text('Login')")
        page.wait_for_timeout(2000)

        # Go to genre page
        page.goto(f"{URL}/home/genre")
        page.wait_for_timeout(1500)

        # Collect genres
        genre_elements = page.locator("div.genre-wrapper ul li")
        genre_count = genre_elements.count()
        genre_results = []

        for i in range(genre_count):
            genre_name = genre_elements.nth(i).inner_text().strip()
            if not genre_name:
                continue

            # Click the genre to load books
            genre_elements.nth(i).click()
            page.wait_for_timeout(2000)

            # Get current URL to identify genre ID
            genre_url = page.url

            # Count books in this genre
            try:
                book_locator = page.locator("div.book-and-author")
                book_count = book_locator.count()
            except Exception:
                book_count = 0

            genre_results.append({
                "genre": genre_name,
                "url": genre_url,
                "book_count": book_count
            })

            print(f"📚 {genre_name}: {book_count} book(s)")

            # Go back to genre list page to repeat
            page.goto(f"{URL}/home/genre")
            page.wait_for_timeout(1000)
            genre_elements = page.locator("div.genre-wrapper ul li")  # refresh locator

        # Export results
        Path("test_reports").mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_path = f"test_reports/genre_book_counts_{timestamp}.csv"
        json_path = f"test_reports/genre_book_counts_{timestamp}.json"
        html_path = f"test_reports/genre_book_counts_{timestamp}.html"

        # CSV
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["genre", "book_count", "url"])
            writer.writeheader()
            writer.writerows(genre_results)

        # JSON
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(genre_results, f, indent=2)

        # HTML
        with open(html_path, "w", encoding="utf-8") as f:
            f.write("<html><head><title>Genre Book Count</title></head><body>")
            f.write("<h1>📚 Genre Book Count Report</h1><table border='1'><tr><th>Genre</th><th>Book Count</th><th>Link</th></tr>")
            for g in genre_results:
                f.write(f"<tr><td>{g['genre']}</td><td>{g['book_count']}</td><td><a href='{g['url']}'>{g['url']}</a></td></tr>")
            f.write("</table></body></html>")

        print("\n✅ Export complete:")
        print(f" - CSV:  {csv_path}")
        print(f" - JSON: {json_path}")
        print(f" - HTML: {html_path}")

        browser.close()

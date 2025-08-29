import pytest
from playwright.sync_api import sync_playwright
import csv, json
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

# --- Configuration ---
URL = "https://mylibribooks.com"
EMAIL = "cpot.tea@gmail.com"
PASSWORD = "Moniwyse!400"


@pytest.mark.fast
def test_count_books_by_genre():
    """
    Test that navigates to the genre page, collects all genre links,
    and then counts the number of books on each genre page.
    This version is fixed and stable.
    """
    print("--- Starting book count by genre test ---")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = Path("test_reports")
    report_dir.mkdir(exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True) #set to False to debug locally
        page = browser.new_page()
        page.set_default_timeout(30000)

        # 🔐 Login
        page.goto(URL)
        page.click("text=Sign In")
        page.wait_for_url("**/signin")
        page.fill("input[type='email']", EMAIL)
        page.fill("input[type='password']", PASSWORD)
        page.click("button:has-text('Login')")
        page.wait_for_timeout(3000)

        # 🚀 Go to Genre Page
        page.goto(f"{URL}/home/genre")
        page.wait_for_selector("div.genre-wrapper ul li", timeout=8000)

        # ✅ Collect genre names and optional URLs
        genre_elements = page.locator("div.genre-wrapper ul li")
        genre_count = genre_elements.count()
        genre_list = []

        for i in range(genre_count):
            try:
                element = genre_elements.nth(i)
                name = element.inner_text().strip()

                # Try to extract href if inside an <a>
                href = None
                link = element.locator("a")
                if link.count() > 0:
                    href = link.get_attribute("href")

                if name:
                    genre_list.append({
                        "name": name,
                        "url": urljoin(URL, href) if href else f"{URL}/home/genre/{name.replace(' ', '-')}"
                    })
            except Exception as e:
                print(f"⚠️ Skipping index {i} due to error: {e}")
                continue

        print(f"🎯 Total genres found: {len(genre_list)}")

        # --- Iterate and Test Each Genre ---
        genre_results = []
        for genre in genre_list:
            genre_name = genre["name"]
            genre_url = genre["url"]

            try:
                print(f"➡️ Navigating to genre: {genre_name} ({genre_url})")
                page.goto(genre_url, timeout=30000)

                # Detect books
                book_locator = page.locator("div.book-card, div.book-item, .book")
                book_count = 0

                if page.locator("text=No books found for this genre.").count() > 0:
                    book_count = 0
                elif book_locator.count() > 0:
                    book_locator.first.wait_for(state="visible", timeout=15000)
                    book_count = book_locator.count()

                print(f"📖 {genre_name}: {book_count} book(s)")
                genre_results.append({"genre": genre_name, "count": book_count})

            except Exception as e:
                print(f"⚠️ Error on genre '{genre_name}': {e}")
                genre_results.append({"genre": genre_name, "count": 0, "error": str(e)})
                continue

        # --- Export Results ---
        print("➡️ Saving test results...")
        csv_path = report_dir / f"genre_book_counts_{timestamp}.csv"
        json_path = report_dir / f"genre_book_counts_{timestamp}.json"
        html_path = report_dir / f"genre_book_counts_{timestamp}.html"

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

import pytest
from playwright.sync_api import sync_playwright
import csv, json
from datetime import datetime
from pathlib import Path

URL = "https://mylibribooks.com"
EMAIL = "cpot.tea@gmail.com"
PASSWORD = "Moniwyse!400"

@pytest.mark.slow
def test_long_running():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=300)  # headless=False for debugging
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

        # Capture genre names (list items inside wrapper)
        genre_items = page.locator("div.genre-wrapper li")
        genre_count = genre_items.count()
        print(f"🔎 Found {genre_count} genres")

        genre_texts = []
        for i in range(genre_count):
            txt = genre_items.nth(i).inner_text().strip()
            if txt:
                genre_texts.append(txt)

        all_books = []

        for genre_name in genre_texts:
            print(f"➡️ Visiting genre: {genre_name}")
            try:
                page.locator(f"text={genre_name}").first.click()
                page.wait_for_timeout(2500)
                genre_url = page.url

                # Try different book selectors
                book_cards = page.locator("div.book-and-author, div.book-card, div.book-item")
                book_count = book_cards.count()
                print(f"📚 Found {book_count} book(s) in {genre_name}")

                for i in range(book_count):
                    book = book_cards.nth(i)
                    try:
                        title = book.locator("h2, h3, .book-title").first.inner_text().strip()
                    except:
                        title = "N/A"

                    try:
                        author = book.locator("p, .author-name").first.inner_text().strip()
                    except:
                        author = "N/A"

                    try:
                        rating = book.locator("text=Rating").first.inner_text().strip()
                    except:
                        rating = "N/A"

                    all_books.append({
                        "genre": genre_name,
                        "title": title,
                        "author": author,
                        "rating": rating,
                        "genre_url": genre_url
                    })

                print(f"✅ Extracted {book_count} book(s) from {genre_name}")

            except Exception as e:
                print(f"⚠️ Skipping genre '{genre_name}': {e}")

            # Return to genre list
            page.goto(f"{URL}/home/genre")
            page.wait_for_timeout(1000)

        # Export results
        Path("test_reports").mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_path = f"test_reports/books_metadata_{timestamp}.csv"
        json_path = f"test_reports/books_metadata_{timestamp}.json"
        html_path = f"test_reports/books_metadata_{timestamp}.html"

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["genre", "title", "author", "rating", "genre_url"])
            writer.writeheader()
            writer.writerows(all_books)

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(all_books, f, indent=2)

        with open(html_path, "w", encoding="utf-8") as f:
            f.write("<html><head><title>Books Metadata</title></head><body>")
            f.write("<h1>📚 MyLibriBooks Metadata Report</h1><table border='1'><tr><th>Genre</th><th>Title</th><th>Author</th><th>Rating</th></tr>")
            for b in all_books:
                f.write(f"<tr><td>{b['genre']}</td><td>{b['title']}</td><td>{b['author']}</td><td>{b['rating']}</td></tr>")
            f.write("</table></body></html>")

        print(f"\n📦 Exported: {len(all_books)} books")
        print(f"CSV:  {csv_path}")
        print(f"JSON: {json_path}")
        print(f"HTML: {html_path}")
        browser.close()

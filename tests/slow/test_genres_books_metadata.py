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
        browser = p.chromium.launch(headless=True, slow_mo=300)
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

        # Get all genre names safely
        genre_texts = page.locator("div.genre-wrapper ul li").all_inner_texts()
        genre_texts = [g.strip() for g in genre_texts if g.strip()]
        all_books = []

        for genre_name in genre_texts:
            print(f"➡️  Visiting genre: {genre_name}")
            try:
                page.locator(f"text={genre_name}").first.click()
                page.wait_for_timeout(2500)
                genre_url = page.url

                book_cards = page.locator("div.book-and-author")
                book_count = book_cards.count()

                for i in range(book_count):
                    book = book_cards.nth(i)
                    try:
                        title = book.locator("h2").inner_text().strip()
                    except:
                        title = "N/A"

                    try:
                        author = book.locator("p").nth(0).inner_text().strip()
                    except:
                        author = "N/A"

                    try:
                        rating = book.locator("span:has-text('Rating')").inner_text().strip()
                    except:
                        rating = "N/A"

                    all_books.append({
                        "genre": genre_name,
                        "title": title,
                        "author": author,
                        "rating": rating,
                        "genre_url": genre_url
                    })

                print(f"✅ {genre_name}: {book_count} book(s) extracted")

            except Exception as e:
                print(f"⚠️ Skipping genre '{genre_name}': {e}")

            # Return to genre list
            page.goto(f"{URL}/home/genre")
            page.wait_for_timeout(1000)

        # Export
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

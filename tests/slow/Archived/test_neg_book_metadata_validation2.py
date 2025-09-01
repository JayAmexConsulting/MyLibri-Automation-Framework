import pytest
from playwright.sync_api import sync_playwright
from datetime import datetime
import csv, json
from pathlib import Path

# --- Config ---
URL = "https://mylibribooks.com"
BOOK_URL_BASE = f"{URL}/home/books"
EMAIL = "cpot.tea@gmail.com"
PASSWORD = "Moniwyse!400"

START_ID = 1501
MAX_ID = 3000
STOP_AFTER_CONSECUTIVE_FAILS = 30


@pytest.mark.slow
def test_failed_books_only():
    """
    Iterates through book IDs and records ONLY failed metadata results.
    Exports results to CSV, JSON, and HTML.
    """
    print("🚀 Starting failed metadata validation test...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_default_timeout(10000)

        # 🔐 Login
        print("🔐 Logging in...")
        page.goto(URL)
        page.click("text=Sign In")
        page.wait_for_url("**/signin", timeout=10000)
        page.fill("input[type='email']", EMAIL)
        page.fill("input[type='password']", PASSWORD)
        page.click("button:has-text('Login')")
        page.wait_for_timeout(2000)

        failed_results = []
        failures_in_a_row = 0

        # --- Loop through books ---
        for book_id in range(START_ID, MAX_ID + 1):
            book_url = f"{BOOK_URL_BASE}/{book_id}"
            print(f"📘 Checking ID {book_id}... ", end="")

            try:
                page.goto(book_url, timeout=8000)
                page.wait_for_timeout(500)

                # Defaults
                title, author, rating, cover = "N/A", "N/A", "No Rating", "No Cover"
                errors = []

                # Extract title
                if page.locator("div.book-details h1.book-name").count() > 0:
                    title = page.locator("div.book-details h1.book-name").first.text_content().strip()
                else:
                    errors.append("Missing title")

                # Extract author
                if page.locator("div.book-details p.author-name").count() > 0:
                    author = page.locator("div.book-details p.author-name").first.text_content().strip()
                else:
                    errors.append("Missing author")

                # Extract rating
                if page.locator("div.book-details p:text('Rating')").count() > 0:
                    rating_raw = page.locator("div.book-details p:text('Rating')").first.text_content()
                    rating = rating_raw.strip() if rating_raw else "No Rating"

                # Extract cover
                if page.locator("div.book-details img").count() > 0:
                    cover_url = page.locator("div.book-details img").first.get_attribute("src")
                    cover = cover_url if cover_url else "No Cover"
                else:
                    errors.append("Missing cover")

                if errors:
                    print(f"❌ Failed — {', '.join(errors)}")
                    failed_results.append({
                        "id": book_id,
                        "url": book_url,
                        "title": title,
                        "author": author,
                        "rating": rating,
                        "cover": cover,
                        "errors": ", ".join(errors),
                        "timestamp": datetime.now().isoformat()
                    })
                    failures_in_a_row += 1
                else:
                    print(f"✅ Passed")

                if failures_in_a_row >= STOP_AFTER_CONSECUTIVE_FAILS:
                    print(f"\n🛑 Stopped after {STOP_AFTER_CONSECUTIVE_FAILS} consecutive failures.")
                    break

            except Exception as e:
                print(f"❌ Error: {str(e)}")
                failed_results.append({
                    "id": book_id,
                    "url": book_url,
                    "title": "N/A",
                    "author": "N/A",
                    "rating": "N/A",
                    "cover": "N/A",
                    "errors": str(e),
                    "timestamp": datetime.now().isoformat()
                })
                failures_in_a_row += 1

        # --- Save failed outputs ---
        report_dir = Path("test_reports")
        report_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        csv_path = report_dir / f"failed_metadata_{timestamp}.csv"
        json_path = report_dir / f"failed_metadata_{timestamp}.json"
        html_path = report_dir / f"failed_metadata_{timestamp}.html"

        # CSV
        with open(csv_path, "w", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["id", "url", "title", "author", "rating", "cover", "errors", "timestamp"])
            writer.writeheader()
            writer.writerows(failed_results)

        # JSON
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(failed_results, f, indent=2)

        # HTML
        with open(html_path, "w", encoding="utf-8") as f:
            f.write("<html><head><title>Failed Book Metadata Report</title></head><body>")
            f.write("<h1>❌ Failed Book Metadata Report</h1>")
            f.write("<table border='1' cellpadding='5' cellspacing='0'>")
            f.write("<tr><th>ID</th><th>Title</th><th>Author</th><th>Rating</th><th>Cover</th><th>URL</th><th>Errors</th></tr>")
            for item in failed_results:
                f.write("<tr>")
                f.write(f"<td>{item['id']}</td>")
                f.write(f"<td>{item['title']}</td>")
                f.write(f"<td>{item['author']}</td>")
                f.write(f"<td>{item['rating']}</td>")
                f.write(f"<td><img src='{item['cover']}' width='50'></td>")
                f.write(f"<td><a href='{item['url']}' target='_blank'>Link</a></td>")
                f.write(f"<td>{item['errors']}</td>")
                f.write("</tr>")
            f.write("</table></body></html>")

        print(f"\n✅ Done: {len(failed_results)} failed books recorded.")
        print(f"📄 CSV: {csv_path}")
        print(f"📄 JSON: {json_path}")
        print(f"📄 HTML: {html_path}")
        browser.close()

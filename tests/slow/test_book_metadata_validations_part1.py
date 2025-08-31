import pytest
from playwright.sync_api import sync_playwright
from datetime import datetime
import csv, json
from pathlib import Path

# --- Configuration ---
URL = "https://mylibribooks.com"
BOOK_URL_BASE = f"{URL}/home/books"
EMAIL = "cpot.tea@gmail.com"
PASSWORD = "Moniwyse!400"

START_ID = 1
MAX_ID = 1500
STOP_AFTER_CONSECUTIVE_FAILS = 30


@pytest.mark.slow
def test_long_running_part1():
    print("🚀 Starting metadata validation test...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # Headless set to True
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
        page.wait_for_timeout(3000)  # Added a delay after login
        print("✅ Login successful.")

        metadata_results = []
        failures_in_a_row = 0

        # --- Loop through book IDs ---
        for book_id in range(START_ID, MAX_ID + 1):
            book_url = f"{BOOK_URL_BASE}/{book_id}"
            print(f"📘 Validating Book ID {book_id}... ", end="")

            try:
                # Go to the book page and wait for the main content container to appear
                page.goto(book_url, timeout=10000, wait_until='domcontentloaded')
                page.wait_for_selector("div.book-details", timeout=8000)
                page.wait_for_timeout(500)  # Small delay after page load

                # Initialize defaults
                title, author, rating, pages_count = "N/A", "N/A", "N/A", "N/A"
                comment = ""

                # --- Safely extract metadata ---
                title_locator = page.locator("div.book-details h1.book-name")
                if title_locator.count() > 0:
                    title = title_locator.first.text_content().strip()

                author_locator = page.locator("div.book-details p.author-name")
                if author_locator.count() > 0:
                    author = author_locator.first.text_content().strip()
                
                # Extract Rating
                rating_locator = page.locator("div.book-details p:has-text('Rating')")
                if rating_locator.count() > 0:
                    rating = rating_locator.first.text_content().strip()

                # Extract Number of Pages
                pages_locator = page.locator("div.book-details p.no-of-page-text")
                if pages_locator.count() > 0:
                    pages_count = pages_locator.first.text_content().strip()
                
                # --- Validation and Reporting ---
                if title == "N/A":
                    comment = "Book ID Broken, no valid book metadata found"
                    print(f"❌ {comment}")
                    failures_in_a_row += 1
                else:
                    comment = "Valid"
                    print(f"✅ Book Data Found: '{title}' by '{author}' | Rating: {rating} | Pages: {pages_count}")
                    failures_in_a_row = 0

                # Always append the result
                metadata_results.append({
                    "id": book_id,
                    "url": book_url,
                    "title": title,
                    "author": author,
                    "rating": rating,
                    "pages": pages_count,
                    "comment": comment,
                    "timestamp": datetime.now().isoformat()
                })

                if failures_in_a_row >= STOP_AFTER_CONSECUTIVE_FAILS:
                    print(f"\n🛑 Stopped after {STOP_AFTER_CONSECUTIVE_FAILS} consecutive failures.")
                    break

            except Exception:
                comment = "Book ID Broken, no valid book metadata found"
                print(f"❌ {comment}")
                failures_in_a_row += 1
                metadata_results.append({
                    "id": book_id,
                    "url": book_url,
                    "title": "N/A",
                    "author": "N/A",
                    "rating": "N/A",
                    "pages": "N/A",
                    "comment": comment,
                    "timestamp": datetime.now().isoformat()
                })

        # --- Export results ---
        report_dir = Path("test_reports")
        report_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        csv_path = report_dir / f"metadata_validation_{timestamp}.csv"
        json_path = report_dir / f"metadata_validation_{timestamp}.json"
        html_path = report_dir / f"metadata_validation_{timestamp}.html"

        # CSV Report
        with open(csv_path, "w", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["id", "url", "title", "author", "rating", "pages", "comment", "timestamp"])
            writer.writeheader()
            writer.writerows(metadata_results)

        # JSON Report
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(metadata_results, f, indent=2)

        # HTML Report
        print("➡️ Generating HTML report...")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write("<html><head><title>Book Metadata Report</title>")
            f.write("<style>")
            f.write("body { font-family: sans-serif; line-height: 1.6; padding: 20px; }")
            f.write("h1 { color: #4CAF50; }")
            f.write("table { width: 100%; border-collapse: collapse; margin-top: 20px; }")
            f.write("th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }")
            f.write("th { background-color: #4CAF50; color: white; }")
            f.write("</style></head><body>")
            f.write("<h1>📊 Book Metadata Report</h1>")
            f.write(f"<p>Processed {len(metadata_results)} books.</p>")
            f.write("<table>")
            f.write("<tr><th>ID</th><th>Title</th><th>Author</th><th>Rating</th><th>Pages</th><th>URL</th><th>Comment</th></tr>")
            for item in metadata_results:
                f.write("<tr>")
                f.write(f"<td>{item['id']}</td>")
                f.write(f"<td>{item['title']}</td>")
                f.write(f"<td>{item['author']}</td>")
                f.write(f"<td>{item['rating']}</td>")
                f.write(f"<td>{item['pages']}</td>")
                f.write(f"<td><a href='{item['url']}' target='_blank'>Link</a></td>")
                f.write(f"<td>{item['comment']}</td>")
                f.write("</tr>")
            f.write("</table></body></html>")

        total_books_checked = len(metadata_results)
        valid_books_found = sum(1 for x in metadata_results if x["comment"] == "Valid")
        no_valid_metadata = total_books_checked - valid_books_found

        print("\n--- Test Summary ---")
        print(f"Total books checked: {total_books_checked}")
        print(f"Valid book metadata found: {valid_books_found}")
        print(f"No valid book metadata found: {no_valid_metadata}")
        print("\n--- Reports ---")
        print(f"📄 CSV: {csv_path}")
        print(f"📄 JSON: {json_path}")
        print(f"📄 HTML: {html_path}")
        browser.close()

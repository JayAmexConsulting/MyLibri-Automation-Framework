import pytest
from playwright.sync_api import sync_playwright
import csv, json
from datetime import datetime
from pathlib import Path

URL = "https://mylibribooks.com"
BOOK_URL_BASE = f"{URL}/home/books"
EMAIL = "cpot.tea@gmail.com"
PASSWORD = "Moniwyse!400"
START_ID = 1
MAX_ID = 20
STOP_AFTER_CONSECUTIVE_FAILS = 50

@pytest.mark.slow
def test_long_running():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, slow_mo=200)
        page = browser.new_page()

        print("🔐 Logging in...")
        page.goto(URL)
        page.click("text=Sign In")
        page.wait_for_url("**/signin", timeout=10000)
        page.fill("input[type='email']", EMAIL)
        page.fill("input[type='password']", PASSWORD)
        page.click("button:has-text('Login')")
        page.wait_for_timeout(3000)

        if "dashboard" not in page.url:
            print(f"❌ Login failed, landed on {page.url}")
            browser.close()
            return

        found_books = []
        failures_in_a_row = 0

        for book_id in range(START_ID, MAX_ID + 1):
            book_url = f"{BOOK_URL_BASE}/{book_id}"
            print(f"🔎 Checking ID {book_id} ... ", end="")

            try:
                page.goto(book_url, timeout=8000)
                page.wait_for_timeout(500)

                book_title = ""
                author_name = ""

                try:
                    page.wait_for_selector("div.book-details h1.book-name", timeout=3000)
                    book_title = page.locator("div.book-details h1.book-name").first.text_content().strip()
                except Exception as e:
                    print(f"\n⚠️ Title not found for ID {book_id}: {e}")

                try:
                    author_name = page.locator("div.book-details p.author-name").first.text_content().strip()
                except Exception as e:
                    print(f"\n⚠️ Author not found for ID {book_id}: {e}")

                if not book_title:
                    print("❌ No valid title found")
                    failures_in_a_row += 1
                else:
                    print(f"✅ Found: {book_title} by {author_name}")
                    found_books.append({
                        "id": book_id,
                        "url": book_url,
                        "title": book_title,
                        "author": author_name,
                        "timestamp": datetime.now().isoformat()
                    })
                    failures_in_a_row = 0

                if failures_in_a_row >= STOP_AFTER_CONSECUTIVE_FAILS:
                    print(f"\n🛑 Stopping after {STOP_AFTER_CONSECUTIVE_FAILS} consecutive missing pages.")
                    break

            except Exception as e:
                print(f"❌ Error loading book page {book_url}: {str(e)}")
                failures_in_a_row += 1

        Path("test_reports").mkdir(exist_ok=True)
        Path("docs").mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_path = f"test_reports/book_id_sweep_{timestamp}.csv"
        json_path = f"test_reports/book_id_sweep_{timestamp}.json"
        latest_json_path = "docs/latest.json"

        with open(csv_path, "w", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["id", "url", "title", "author", "timestamp"])
            writer.writeheader()
            writer.writerows(found_books)

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(found_books, f, indent=2)

        with open(latest_json_path, "w", encoding="utf-8") as f:
            json.dump(found_books, f, indent=2)

        print(f"\n📦 Done: {len(found_books)} books found and saved.")
        if not found_books:
            print("⚠️ No books were found or extracted — check platform availability.")

        browser.close()

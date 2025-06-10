from playwright.sync_api import sync_playwright
import csv, json
from datetime import datetime
from pathlib import Path

URL = "https://mylibribooks.com"
BOOK_URL_BASE = f"{URL}/home/books"
EMAIL = "cpot.tea@gmail.com"
PASSWORD = "Moniwyse!400"
START_ID = 1
MAX_ID = 3000
STOP_AFTER_CONSECUTIVE_FAILS = 30

def test_books_validity():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True), slow_mo=200)
        page = browser.new_page()

        # ✅ Step 1: Login
        print("🔐 Logging in to platform...")
        page.goto(URL)
        page.click("text=Sign In")
        page.wait_for_url("**/signin", timeout=10000)
        page.fill("input[type='email']", EMAIL)
        page.fill("input[type='password']", PASSWORD)
        page.click("button:has-text('Login')")
        page.wait_for_timeout(3000)

        # ✅ Step 2: Loop through book IDs
        valid_books = []
        failures_in_a_row = 0

        for book_id in range(START_ID, MAX_ID + 1):
            book_url = f"{BOOK_URL_BASE}/{book_id}"
            print(f"🔎 Checking {book_url} ... ", end="")

            try:
                page.goto(book_url, timeout=8000)
                page.wait_for_timeout(500)

                # Try to grab book title
                try:
                    title = page.locator("div.book-details h1.book-name").first.text_content().strip()
                except:
                    title = ""

                if not title:
                    print("❌ No valid title")
                    failures_in_a_row += 1
                else:
                    print(f"✅ Title: {title}")
                    valid_books.append({
                        "id": book_id,
                        "url": book_url,
                        "title": title
                    })
                    failures_in_a_row = 0  # reset

                if failures_in_a_row >= STOP_AFTER_CONSECUTIVE_FAILS:
                    print(f"\n🛑 Stopped after {STOP_AFTER_CONSECUTIVE_FAILS} consecutive failures.")
                    break

            except Exception as e:
                print(f"❌ Error: {str(e)}")
                failures_in_a_row += 1

        # ✅ Save results
        Path("test_reports").mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_path = f"test_reports/test_books_validity_{timestamp}.csv"
        json_path = f"test_reports/test_books_validity_{timestamp}.json"

        with open(csv_path, "w", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["id", "url", "title"])
            writer.writeheader()
            writer.writerows(valid_books)

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(valid_books, f, indent=2)

        print(f"\n✅ Done: {len(valid_books)} valid books found")
        print(f"📄 CSV: {csv_path}")
        print(f"📄 JSON: {json_path}")
        browser.close()

from playwright.sync_api import sync_playwright
import csv, json
from datetime import datetime
from pathlib import Path

URL = "https://mylibribooks.com"
BOOK_URL_BASE = f"{URL}/home/books"
EMAIL = "cpot.tea@gmail.com"
PASSWORD = "Moniwyse!400"

START_ID = 1
MAX_ID = 100  # Update this as needed
STOP_AFTER_CONSECUTIVE_FAILS = 50

def test_check_book_ids():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=200)
        page = browser.new_page()

        # ✅ Step 1: Log in
        print("🔐 Logging in...")
        page.goto(URL)
        page.click("text=Sign In")
        page.wait_for_url("**/signin", timeout=10000)
        page.fill("input[type='email']", EMAIL)
        page.fill("input[type='password']", PASSWORD)
        page.click("button:has-text('Login')")
        page.wait_for_timeout(3000)

        # ✅ Step 2: Start checking books
        found_books = []
        failures_in_a_row = 0

        for book_id in range(START_ID, MAX_ID + 1):
            book_url = f"{BOOK_URL_BASE}/{book_id}"
            print(f"🔎 Checking ID {book_id} ... ", end="")

            try:
                page.goto(book_url, timeout=8000)
                page.wait_for_timeout(500)

                # Try to extract book title and author
                try:
                    book_title = page.locator("div.book-details h1.book-name").first.text_content().strip()
                except:
                    book_title = ""

                try:
                    author_name = page.locator("div.book-details p.author-name").first.text_content().strip()
                except:
                    author_name = ""

                if not book_title:
                    print("❌ No valid title found")
                    failures_in_a_row += 1
                    found_books.append({
                        "id": book_id,
                        "url": book_url,
                        "title": "N/A",
                        "author": "N/A",
                        "timestamp": datetime.now().isoformat(),
                        "status": "Missing"
                    })
                else:
                    print(f"✅ Found: {book_title} by {author_name}")
                    found_books.append({
                        "id": book_id,
                        "url": book_url,
                        "title": book_title,
                        "author": author_name,
                        "timestamp": datetime.now().isoformat(),
                        "status": "Found"
                    })
                    failures_in_a_row = 0

                if failures_in_a_row >= STOP_AFTER_CONSECUTIVE_FAILS:
                    print(f"\n🛑 Stopping after {STOP_AFTER_CONSECUTIVE_FAILS} consecutive missing pages.")
                    break

            except Exception as e:
                print(f"❌ Error: {str(e)}")
                failures_in_a_row += 1
                found_books.append({
                    "id": book_id,
                    "url": book_url,
                    "title": "N/A",
                    "author": "N/A",
                    "timestamp": datetime.now().isoformat(),
                    "status": f"Error: {str(e)}"
                })

        # ✅ Step 3: Save to CSV + JSON
        Path("test_reports").mkdir(exist_ok=True)
        Path("docs").mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_path = f"test_reports/book_id_sweep_{timestamp}.csv"
        json_path = f"test_reports/book_id_sweep_{timestamp}.json"
        latest_json_path = "docs/latest.json"

        # 📄 Write CSV
        with open(csv_path, "w", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["id", "url", "title", "author", "timestamp", "status"])
            writer.writeheader()
            writer.writerows(found_books)

        # 📄 Write JSON (full)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(found_books, f, indent=2)

        # 🧭 Write JSON for Dashboard
        with open(latest_json_path, "w", encoding="utf-8") as f:
            json.dump(found_books, f, indent=2)

        print(f"\n📦 Done: {len(found_books)} books scanned")
        print(f"📄 CSV: {csv_path}")
        print(f"📄 JSON: {json_path}")

        browser.close()

import pytest
from playwright.sync_api import sync_playwright
import requests
import json
import csv
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
    found_books = []
    failures_in_a_row = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, slow_mo=200)
        page = browser.new_page()

        # ✅ Login first
        print("🔐 Logging in...")
        page.goto(URL)
        page.click("text=Sign In")
        page.wait_for_url("**/signin", timeout=10000)
        page.fill("input[type='email']", EMAIL)
        page.fill("input[type='password']", PASSWORD)
        page.click("button:has-text('Login')")
        page.wait_for_timeout(3000)
        print("✅ Logged in successfully\n")

        for book_id in range(START_ID, MAX_ID + 1):
            book_url = f"{BOOK_URL_BASE}/{book_id}"
            print(f"📘 Book ID {book_id} ... ", end="")

            try:
                page.goto(book_url, timeout=8000)
                page.wait_for_timeout(500)

                title = ""
                author = ""
                rating = "N/A"
                cover_url = ""
                valid_image = False
                page_status = 0

                # Title
                try:
                    title = page.locator("div.book-details h1.book-name").first.text_content().strip()
                except:
                    title = ""

                # Author
                try:
                    author = page.locator("div.book-details p.author-name").first.text_content().strip()
                except:
                    author = ""

                # Rating (optional)
                try:
                    rating_el = page.locator("div.book-details").locator("p", has_text="Rating")
                    rating_text = rating_el.first.text_content().strip()
                    rating = rating_text if rating_text else "N/A"
                except:
                    rating = "N/A"

                # Cover image
                try:
                    img = page.locator("div.book-details img").first
                    cover_url = img.get_attribute("src")
                    if cover_url and cover_url.startswith("http"):
                        resp = requests.get(cover_url)
                        valid_image = resp.status_code == 200
                except:
                    cover_url = ""
                    valid_image = False

                # Link accessible
                try:
                    resp = requests.get(book_url)
                    page_status = resp.status_code
                except:
                    page_status = 0

                if not title:
                    print("❌ No title")
                    failures_in_a_row += 1
                else:
                    print(f"✅ '{title}' by {author}")
                    found_books.append({
                        "id": book_id,
                        "url": book_url,
                        "title": title,
                        "author": author,
                        "rating": rating,
                        "cover_url": cover_url,
                        "image_ok": valid_image,
                        "page_status": page_status,
                        "timestamp": datetime.now().isoformat()
                    })
                    failures_in_a_row = 0

                if failures_in_a_row >= STOP_AFTER_CONSECUTIVE_FAILS:
                    print(f"\n🛑 Stopping after {STOP_AFTER_CONSECUTIVE_FAILS} consecutive failures.")
                    break

            except Exception as e:
                print(f"❌ Error: {str(e)}")
                failures_in_a_row += 1

        browser.close()

    # ✅ Save results
    Path("test_reports").mkdir(exist_ok=True)
    Path("docs").mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = f"test_reports/book_metadata_{timestamp}.csv"
    json_path = f"test_reports/book_metadata_{timestamp}.json"
    latest_path = "docs/latest.json"

    with open(csv_path, "w", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=found_books[0].keys())
        writer.writeheader()
        writer.writerows(found_books)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(found_books, f, indent=2)

    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(found_books, f, indent=2)

    print(f"\n📦 Saved {len(found_books)} books")
    print(f"📄 CSV: {csv_path}")
    print(f"📄 JSON: {json_path}")

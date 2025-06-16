import pytest
from playwright.sync_api import sync_playwright
from datetime import datetime
import csv, json
from pathlib import Path

URL = "https://mylibribooks.com"
BOOK_URL_BASE = f"{URL}/home/books"
EMAIL = "cpot.tea@gmail.com"
PASSWORD = "Moniwyse!400"

START_ID = 1
MAX_ID = 1500
STOP_AFTER_CONSECUTIVE_FAILS = 30

@pytest.mark.slow
def test_long_running_part1():
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

        metadata_results = []
        failures_in_a_row = 0

        for book_id in range(START_ID, MAX_ID + 1):
            book_url = f"{BOOK_URL_BASE}/{book_id}"
            print(f"📘 Checking ID {book_id}... ", end="")

            try:
                page.goto(book_url, timeout=8000)
                page.wait_for_timeout(500)

                title = author = rating = cover = "N/A"

                # Safely extract metadata
                try:
                    title = page.locator("div.book-details h1.book-name").first.text_content().strip()
                except:
                    pass

                try:
                    author = page.locator("div.book-details p.author-name").first.text_content().strip()
                except:
                    pass

                try:
                    rating_raw = page.locator("div.book-details p:text('Rating')").first.text_content()
                    rating = rating_raw.strip() if rating_raw else "No Rating"
                except:
                    rating = "No Rating"

                try:
                    cover_url = page.locator("div.book-details img").first.get_attribute("src")
                    cover = cover_url if cover_url else "No Cover"
                except:
                    cover = "No Cover"

                if title == "N/A":
                    print("❌ No valid title")
                    failures_in_a_row += 1
                else:
                    print(f"✅ {title} by {author} — Rating: {rating}")
                    metadata_results.append({
                        "id": book_id,
                        "url": book_url,
                        "title": title,
                        "author": author,
                        "rating": rating,
                        "cover": cover,
                        "timestamp": datetime.now().isoformat()
                    })
                    failures_in_a_row = 0

                if failures_in_a_row >= STOP_AFTER_CONSECUTIVE_FAILS:
                    print(f"\n🛑 Stopped after {STOP_AFTER_CONSECUTIVE_FAILS} consecutive failures.")
                    break

            except Exception as e:
                print(f"❌ Error: {str(e)}")
                failures_in_a_row += 1

        # Save outputs
        Path("test_reports").mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_path = f"test_reports/metadata_validation_{timestamp}.csv"
        json_path = f"test_reports/metadata_validation_{timestamp}.json"

        with open(csv_path, "w", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["id", "url", "title", "author", "rating", "cover", "timestamp"])
            writer.writeheader()
            writer.writerows(metadata_results)

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(metadata_results, f, indent=2)

        print(f"\n✅ Done: {len(metadata_results)} books validated.")
        print(f"📄 CSV: {csv_path}")
        print(f"📄 JSON: {json_path}")
        browser.close()

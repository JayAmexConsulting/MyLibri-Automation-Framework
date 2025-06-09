import pytest
from playwright.sync_api import sync_playwright
import time, csv, json
from datetime import datetime
from pathlib import Path

EMAIL = "cpot.tea@gmail.com"
PASSWORD = "Moniwyse!400"
BASE_URL = "https://mylibribooks.com"
DISCOVER_URL = f"{BASE_URL}/home/discover"

@pytest.mark.fast
def test_discover_books():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=200)
        page = browser.new_page()

        # Step 1: Login
        page.goto(BASE_URL)
        page.click("text=Sign In")
        page.wait_for_url("**/signin")
        page.fill("input[type='email']", EMAIL)
        page.fill("input[type='password']", PASSWORD)
        page.click("button:has-text('Login')")
        page.wait_for_timeout(3000)

        # Step 2: Visit Discover page
        page.goto(DISCOVER_URL)
        page.wait_for_timeout(2000)

        found_sections = []
        section_blocks = page.locator("div.section").all()

        for idx, block in enumerate(section_blocks):
            try:
                heading = block.locator("h1, h2, h3").first.text_content().strip()
                book_titles = [el.text_content().strip() for el in block.locator("div.book-details h1.book-name").all()]
                found_sections.append({
                    "section": heading,
                    "books": book_titles
                })
                print(f"✅ {heading}: {len(book_titles)} books")

            except Exception as e:
                print(f"⚠️ Block {idx} failed: {e}")

        # Export results
        Path("test_reports").mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_path = f"test_reports/discover_books_{timestamp}.json"

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(found_sections, f, indent=2)

        print(f"\n📄 Saved to {json_path}")
        browser.close()

import pytest
from playwright.sync_api import sync_playwright
import csv, json
from datetime import datetime
from pathlib import Path

URL = "https://mylibribooks.com"
EMAIL = "cpot.tea@gmail.com"
PASSWORD = "Moniwyse!400"

@pytest.mark.fast
def test_discover_sections_books():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, slow_mo=500)
        page = browser.new_page()
        page.goto(URL)

        # Login
        page.click("text=Sign In")
        page.wait_for_url("**/signin", timeout=8000)
        page.fill("input[type='email']", EMAIL)
        page.fill("input[type='password']", PASSWORD)
        page.click("button:has-text('Login')")
        page.wait_for_timeout(3000)

        # Go to Discover page
        page.goto(f"{URL}/home/discover")
        page.wait_for_timeout(2000)

        all_books = []

        # Find all "See All" buttons
        see_all_buttons = page.locator("p.see-all-text")
        section_count = see_all_buttons.count()

        print(f"🔍 Found {section_count} discover sections")

        for i in range(section_count):
            try:
                section_heading = page.locator("h1").nth(i).inner_text().strip()
                see_all = see_all_buttons.nth(i)

                if not see_all.is_visible():
                    print(f"⚠️ Skipping {section_heading} — no See All button visible")
                    continue

                print(f"➡️  Section {i+1}: {section_heading}")
                see_all.scroll_into_view_if_needed()
                see_all.click()
                page.wait_for_timeout(3000)

                # Book cover images
                book_imgs = page.locator("img[src*='libriapp/images']")
                img_count = book_imgs.count()

                for j in range(img_count):
                    img_src = book_imgs.nth(j).get_attribute("src")
                    if img_src:
                        all_books.append({
                            "category": section_heading,
                            "image": img_src
                        })

                print(f"✅ {section_heading}: {img_count} books found")

                # Navigate back to discover page
                page.goto(f"{URL}/home/discover")
                page.wait_for_timeout(1500)

            except Exception as e:
                print(f"❌ Error in section {i+1}: {e}")
                continue

        # Save results
        Path("test_reports").mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_path = f"test_reports/discover_books_covers_{timestamp}.csv"
        json_path = f"test_reports/discover_books_covers_{timestamp}.json"

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["category", "image"])
            writer.writeheader()
            writer.writerows(all_books)

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(all_books, f, indent=2)

        print(f"\n📦 Done: {len(all_books)} book covers exported")
        print(f"📄 CSV:  {csv_path}")
        print(f"📄 JSON: {json_path}")

        # Assert we found at least one book
        assert all_books, "❌ No book covers found in discover sections."

        browser.close()

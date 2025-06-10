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
        browser = p.chromium.launch(headless=True, slow_mo=3000)
        page = browser.new_page()
        page.goto(URL)

        # Login
        page.click("text=Sign In")
        page.wait_for_url("**/signin")
        page.fill("input[type='email']", EMAIL)
        page.fill("input[type='password']", PASSWORD)
        page.click("button:has-text('Login')")
        page.wait_for_timeout(2000)

        # Go to Discover page
        page.goto(f"{URL}/home/discover")
        page.wait_for_timeout(2000)

        all_books = []

        # Get all discover sections (each section container)
        section_blocks = page.locator("div:has(h1) >> ..")  # move to the parent of h1 and see-all
        section_count = section_blocks.count()

        print(f"🔍 Found {section_count} discover section blocks")

        for i in range(section_count):
            try:
                section = section_blocks.nth(i)
                heading = section.locator("h1").inner_text().strip()
                see_all = section.locator("p.see-all-text")

                if not see_all.is_visible():
                    print(f"⚠️ Skipping {heading} — no See All button visible")
                    continue

                print(f"➡️  Section {i+1}: {heading}")
                see_all.scroll_into_view_if_needed()
                see_all.click()
                page.wait_for_timeout(3000)

                # Extract book images
                book_imgs = page.locator("img[src*='libriapp/images']")
                img_count = book_imgs.count()

                for j in range(img_count):
                    img_src = book_imgs.nth(j).get_attribute("src")
                    if img_src:
                        all_books.append({
                            "category": heading,
                            "image": img_src
                        })

                print(f"✅ {heading}: {img_count} books found")

                # Return to Discover and regrab sections
                page.goto(f"{URL}/home/discover")
                page.wait_for_timeout(1500)
                section_blocks = page.locator("div:has(h1) >> ..")

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
        browser.close()

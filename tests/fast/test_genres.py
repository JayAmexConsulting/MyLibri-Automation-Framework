import pytest
from playwright.sync_api import sync_playwright
from pathlib import Path
from datetime import datetime
import csv
import json

URL = "https://mylibribooks.com"
EMAIL = "cpot.tea@gmail.com"
PASSWORD = "Moniwyse!400"

@pytest.mark.fast
def test_quick_check():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = Path("test_reports")
    report_dir.mkdir(exist_ok=True)

    genres = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, slow_mo=200)
        page = browser.new_page()
        page.set_default_timeout(10000)

        # 🔐 Login
        page.goto(URL)
        page.click("text=Sign In")
        page.wait_for_url("**/signin")
        page.fill("input[type='email']", EMAIL)
        page.fill("input[type='password']", PASSWORD)
        page.click("button:has-text('Login')")
        page.wait_for_timeout(3000)

        # 🚀 Go to Genre Page
        page.goto(f"{URL}/home/genre")
        page.wait_for_timeout(2000)

        try:
            page.wait_for_selector("div.genre-wrapper ul li", timeout=8000)
        except:
            print("❌ Genre list not found")
            browser.close()
            return

        genre_elements = page.locator("div.genre-wrapper ul li")
        count = genre_elements.count()

        for i in range(count):
            text = genre_elements.nth(i).text_content()
            if text:
                genres.append({"genre": text.strip()})

        print(f"🎯 Total genres found: {len(genres)}")

        # 📤 Write outputs
        csv_path = report_dir / f"genre_list_{timestamp}.csv"
        json_path = report_dir / f"genre_list_{timestamp}.json"
        html_path = report_dir / f"genre_report_{timestamp}.html"

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["genre"])
            writer.writeheader()
            writer.writerows(genres)

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(genres, f, indent=2)

        with open(html_path, "w", encoding="utf-8") as f:
            f.write("<html><head><title>Genres</title></head><body>")
            f.write("<h1>📚 Extracted Genres</h1><ul>")
            for g in genres:
                f.write(f"<li>{g['genre']}</li>")
            f.write("</ul></body></html>")

        print(f"✅ Exported:")
        print(f" - CSV:  {csv_path}")
        print(f" - JSON: {json_path}")
        print(f" - HTML: {html_path}")

        browser.close()

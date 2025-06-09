import pytest
from playwright.sync_api import sync_playwright
import csv, json
from datetime import datetime
from pathlib import Path

URL = "https://mylibribooks.com"
EMAIL = "cpot.tea@gmail.com"
PASSWORD = "Moniwyse!400"

@pytest.mark.fast
def test_quick_check():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=300)
        page = browser.new_page()
        page.goto(URL)

        # Login
        page.click("text=Sign In")
        page.wait_for_url("**/signin")
        page.fill("input[type='email']", EMAIL)
        page.fill("input[type='password']", PASSWORD)
        page.click("button:has-text('Login')")
        page.wait_for_timeout(2000)

        # Navigate to Genre Page
        page.goto(f"{URL}/home/discover")
        page.wait_for_timeout(1000)
        page.goto(f"{URL}/home/genre")
        page.wait_for_timeout(1000)

        # Extract genres
        genre_elements = page.locator("div.genre-wrapper ul li")
        genre_count = genre_elements.count()
        genres = []

        for i in range(genre_count):
            genre = genre_elements.nth(i).inner_text().strip()
            if genre:
                genres.append({"genre": genre})

        print(f"🎯 Total genres found: {len(genres)}")

        # Create reports folder
        Path("test_reports").mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_path = f"test_reports/genre_list_{timestamp}.csv"
        json_path = f"test_reports/genre_list_{timestamp}.json"
        html_path = f"test_reports/genre_report_{timestamp}.html"

        # Write CSV
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["genre"])
            writer.writeheader()
            writer.writerows(genres)

        # Write JSON
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(genres, f, indent=2)

        # Write simple HTML
        with open(html_path, "w", encoding="utf-8") as f:
            f.write("<html><head><title>Genre Report</title></head><body>")
            f.write("<h1>📚 MyLibriBooks Genre List</h1>")
            f.write("<ul>")
            for item in genres:
                f.write(f"<li>{item['genre']}</li>")
            f.write("</ul>")
            f.write("</body></html>")

        print("✅ Exported:")
        print(f" - CSV:  {csv_path}")
        print(f" - JSON: {json_path}")
        print(f" - HTML: {html_path}")

        browser.close()

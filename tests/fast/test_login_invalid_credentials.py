import pytest
from playwright.sync_api import sync_playwright
from pathlib import Path
from datetime import datetime

URL = "https://mylibribooks.com"
INVALID_EMAIL = "wrong.user@example.com"
INVALID_PASSWORD = "incorrectPassword123"

@pytest.mark.fast
def test_quick_check():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_dir = Path(f"test_reports/screenshots_invalid_login_{timestamp}")
    screenshot_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=200)
        page = browser.new_page()

        # Attempt login with wrong credentials
        page.goto(URL)
        page.click("text=Sign In")
        page.wait_for_url("**/signin", timeout=5000)
        page.fill("input[type='email']", INVALID_EMAIL)
        page.fill("input[type='password']", INVALID_PASSWORD)
        page.screenshot(path=screenshot_dir / "01_wrong_credentials.png")
        page.click("button:has-text('Login')")
        page.wait_for_timeout(3000)
        page.screenshot(path=screenshot_dir / "02_after_submit.png")

        # Assert error appears (if any) or still on signin
        assert "/signin" in page.url, "Expected to remain on sign-in page with invalid credentials"
        print("❌ Login failed as expected — test passed.")
        browser.close()

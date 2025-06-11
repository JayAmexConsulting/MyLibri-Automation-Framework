import pytest
from playwright.sync_api import sync_playwright
from pathlib import Path
from datetime import datetime

URL = "https://mylibribooks.com"
EMAIL = "cpot.tea@gmail.com"
PASSWORD = "Moniwyse!400"

@pytest.mark.fast
def test_quick_check():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_dir = Path(f"test_reports/screenshots_login_logout_{timestamp}")
    screenshot_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, slow_mo=200)
        page = browser.new_page()
        page.set_default_timeout(10000)

        try:
            # Step 1: Login
            page.goto(URL)
            page.screenshot(path=screenshot_dir / "01_home.png")
            page.click("text=Sign In")
            page.wait_for_url("**/signin", timeout=5000)
            page.screenshot(path=screenshot_dir / "02_signin_page.png")

            page.fill("input[type='email']", EMAIL)
            page.fill("input[type='password']", PASSWORD)
            page.screenshot(path=screenshot_dir / "03_filled_credentials.png")
            page.click("button:has-text('Login')")
            page.wait_for_timeout(3000)
            page.screenshot(path=screenshot_dir / "04_logged_in.png")

            # Step 2: Navigate to profile
            try:
                page.wait_for_selector("img.profile_pic", timeout=10000)
                page.click("img.profile_pic")
                page.wait_for_timeout(500)
                page.click("text=Tea Pot")
                page.wait_for_url("**/home/profile", timeout=5000)
                page.screenshot(path=screenshot_dir / "05_profile_page.png")
            except Exception as e:
                page.screenshot(path=screenshot_dir / "05_profile_page_failed.png")
                raise AssertionError(f"❌ Failed to access profile: {e}")

            # Step 3: Log out
            try:
                page.click("img.profile_pic")
                page.wait_for_timeout(500)
                page.click("text=Log Out")
                page.wait_for_url(URL, timeout=5000)
                page.screenshot(path=screenshot_dir / "06_logged_out.png")
            except Exception as e:
                page.screenshot(path=screenshot_dir / "06_logout_failed.png")
                raise AssertionError(f"❌ Failed to log out: {e}")

        finally:
            browser.close()

        print(f"✅ Test complete. Screenshots saved to {screenshot_dir}")

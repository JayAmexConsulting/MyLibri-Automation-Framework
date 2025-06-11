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
    screenshot_dir = Path(f"test_reports/screenshots_ui_{timestamp}")
    screenshot_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, slow_mo=200)
        page = browser.new_page()
        page.set_default_timeout(10000)

        try:
            # Step 1: Login
            page.goto(URL)
            page.click("text=Sign In")
            page.wait_for_url("**/signin")
            page.fill("input[type='email']", EMAIL)
            page.fill("input[type='password']", PASSWORD)
            page.click("button:has-text('Login')")
            page.wait_for_timeout(3000)
            page.screenshot(path=screenshot_dir / "01_after_login.png")

            # Step 2: Navigate to Profile
            try:
                page.wait_for_selector("img.profile_pic")
                page.click("img.profile_pic")
                page.wait_for_timeout(500)
                page.click("text=Tea Pot")
                page.wait_for_url("**/home/profile")
                page.wait_for_timeout(1000)
                page.screenshot(path=screenshot_dir / "02_biodata.png")
            except Exception as e:
                page.screenshot(path=screenshot_dir / "02_biodata_error.png")
                raise AssertionError(f"❌ Failed to load profile: {e}")

            # Step 3: Check UI Sections
            try:
                page.click("text=Wallet")
                page.wait_for_timeout(1000)
                page.screenshot(path=screenshot_dir / "03_wallet.png")

                page.click("text=Subscription")
                page.wait_for_timeout(1000)
                page.screenshot(path=screenshot_dir / "04_subscription.png")

                page.click("text=Change Password")
                page.wait_for_timeout(1000)
                page.screenshot(path=screenshot_dir / "05_change_password.png")
            except Exception as e:
                page.screenshot(path=screenshot_dir / "05_section_error.png")
                raise AssertionError(f"❌ Failed while navigating UI sections: {e}")

            # Step 4: Log Out
            try:
                page.click("img.profile_pic")
                page.wait_for_timeout(500)
                logout_btn = page.locator("li.list", has_text="Log Out")
                logout_btn.wait_for(state="visible", timeout=5000)
                logout_btn.click()
                page.wait_for_url(URL, timeout=5000)
                page.screenshot(path=screenshot_dir / "06_logged_out.png")
            except Exception as e:
                page.screenshot(path=screenshot_dir / "06_logout_error.png")
                raise AssertionError(f"❌ Logout failed: {e}")

        finally:
            browser.close()

        print(f"✅ UI test complete. Screenshots saved in {screenshot_dir}")

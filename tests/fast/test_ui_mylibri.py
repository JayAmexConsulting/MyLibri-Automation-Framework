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
        browser = p.chromium.launch(headless=True, slow_mo=300)
        context = browser.new_context(viewport={"width": 1280, "height": 1024})
        page = context.new_page()
        page.set_default_timeout(20000)

        try:
            # Login
            page.goto(URL)
            page.click("text=Sign In")
            page.wait_for_url("**/signin")
            page.fill("input[type='email']", EMAIL)
            page.fill("input[type='password']", PASSWORD)
            page.click("button:has-text('Login')")
            page.wait_for_timeout(3000)
            page.screenshot(path=screenshot_dir / "01_logged_in.png")

            assert "home" in page.url, "❌ Login failed"

            # Navigate to Profile
            page.locator("img.profile_pic").scroll_into_view_if_needed()
            page.click("img.profile_pic")
            page.click("text=Tea Pot")
            page.wait_for_url("**/home/profile", timeout=10000)
            page.screenshot(path=screenshot_dir / "02_profile_biodata.png")

            # Wallet
            page.click("text=Wallet")
            page.wait_for_timeout(1000)
            page.screenshot(path=screenshot_dir / "03_wallet.png")

            # Subscription
            page.click("text=Subscription")
            page.wait_for_timeout(1000)
            page.screenshot(path=screenshot_dir / "04_subscription.png")

            # Change Password
            page.click("text=Change Password")
            page.wait_for_timeout(1000)
            page.screenshot(path=screenshot_dir / "05_change_password.png")

            # Logout
            page.click("img.profile_pic")
            logout_btn = page.locator("li.list", has_text="Log Out")
            logout_btn.wait_for(state="visible", timeout=5000)
            logout_btn.click()
            page.wait_for_timeout(1000)
            page.screenshot(path=screenshot_dir / "06_logged_out.png")

        except Exception as e:
            page.screenshot(path=screenshot_dir / "error.png")
            raise AssertionError(f"❌ Failed to load profile: {e}")

        print(f"✅ UI test complete. Screenshots saved in {screenshot_dir}")
        browser.close()

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
        browser = p.chromium.launch(headless=True, slow_mo=300)
        context = browser.new_context(viewport={"width": 1280, "height": 1024})
        page = context.new_page()
        page.set_default_timeout(20000)

        try:
            # Step 1: Login
            page.goto(URL)
            page.screenshot(path=screenshot_dir / "01_home.png")
            page.click("text=Sign In")
            page.wait_for_url("**/signin")
            page.fill("input[type='email']", EMAIL)
            page.fill("input[type='password']", PASSWORD)
            page.click("button:has-text('Login')")
            page.wait_for_timeout(3000)
            page.screenshot(path=screenshot_dir / "02_dashboard.png")

            assert "home" in page.url or "dashboard" in page.url, "❌ Login failed — dashboard not reached"

            # Step 2: Profile
            page.locator("img.profile_pic").scroll_into_view_if_needed()
            page.click("img.profile_pic")
            page.click("text=Tea Pot")
            page.wait_for_url("**/home/profile", timeout=10000)
            page.screenshot(path=screenshot_dir / "03_profile.png")

            # Step 3: Log out
            page.click("img.profile_pic")
            page.click("text=Log Out")
            page.wait_for_url(URL, timeout=8000)
            page.screenshot(path=screenshot_dir / "04_logged_out.png")

        except Exception as e:
            page.screenshot(path=screenshot_dir / "error.png")
            raise AssertionError(f"❌ Test failed: {e}")

        print(f"✅ Test complete. Screenshots saved to {screenshot_dir}")
        browser.close()

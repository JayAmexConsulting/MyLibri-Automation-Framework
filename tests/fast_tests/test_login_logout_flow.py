from playwright.sync_api import sync_playwright
from pathlib import Path
from datetime import datetime

URL = "https://mylibribooks.com"
EMAIL = "cpot.tea@gmail.com"
PASSWORD = "Moniwyse!400"

def test_login_and_logout():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_dir = Path(f"test_reports/screenshots_login_logout_{timestamp}")
    screenshot_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=200)
        page = browser.new_page()

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
        page.click("img.profile_pic")
        page.wait_for_timeout(500)
        page.click("text=Tea Pot")
        page.wait_for_url("**/home/profile", timeout=5000)
        page.screenshot(path=screenshot_dir / "05_profile_page.png")

        # Step 3: Log out
        page.click("img.profile_pic")
        page.wait_for_timeout(500)
        page.click("text=Log Out")
        page.wait_for_url(URL, timeout=5000)
        page.screenshot(path=screenshot_dir / "06_logged_out.png")

        print(f"✅ Test complete. Screenshots saved to {screenshot_dir}")
        browser.close()

import pytest
from playwright.sync_api import sync_playwright

URL = "https://mylibribooks.com"
EMAIL = "cpot.tea@gmail.com"
PASSWORD = "Moniwyse!400"

@pytest.mark.fast
def test_quick_check():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, slow_mo=200)
        page = browser.new_page()
        page.goto(URL)

        # Login
        page.click("text=Sign In")
        page.wait_for_url("**/signin", timeout=5000)
        page.fill("input[type='email']", EMAIL)
        page.fill("input[type='password']", PASSWORD)
        page.click("button:has-text('Login')")
        page.wait_for_timeout(3000)
        page.screenshot(path="test_reports/after_login.png")

        # Navigate to profile
        page.click("img.profile_pic")
        page.wait_for_timeout(500)
        page.click("text=Tea Pot")
        page.wait_for_url("**/home/profile", timeout=5000)
        page.wait_for_timeout(1000)
        page.screenshot(path="test_reports/profile_biodata.png")

        # Wallet
        page.click("text=Wallet")
        page.wait_for_timeout(1000)
        page.screenshot(path="test_reports/profile_wallet.png")

        # Subscription
        page.click("text=Subscription")
        page.wait_for_timeout(1000)
        page.screenshot(path="test_reports/profile_subscription.png")

        # Change Password
        page.click("text=Change Password")
        page.wait_for_timeout(1000)
        page.screenshot(path="test_reports/profile_change_password.png")

        # Reopen the avatar menu to expose "Log Out"
        page.click("img.profile_pic")
        page.wait_for_timeout(500)

        # Click the <li> that says Log Out
        page.locator("li.list", has_text="Log Out").click()
        page.wait_for_timeout(1000)

        browser.close()

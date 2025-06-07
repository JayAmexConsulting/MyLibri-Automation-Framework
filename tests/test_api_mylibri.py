from playwright.sync_api import sync_playwright

URL = "https://mylibribooks.com"
EMAIL = "cpot.tea@gmail.com"
PASSWORD = "Moniwyse!400"

def test_homepage_loads():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URL)
        assert "MyLibri" in page.title()
        browser.close()

def test_signin_works():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Go to login page
        page.goto(URL)
        page.click("text=Sign In")
        page.wait_for_url("**/signin")

        # Perform login
        page.fill("input[type='email']", EMAIL)
        page.fill("input[type='password']", PASSWORD)
        page.click("button:has-text('Login')")
        page.wait_for_timeout(3000)

        # Check for avatar/profile to confirm login
        assert page.locator("img.profile_pic").is_visible(), "❌ Avatar not visible after login"

        browser.close()

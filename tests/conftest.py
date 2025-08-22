# conftest.py
import pytest
from playwright.sync_api import expect, Page
from pathlib import Path
from datetime import datetime
import os
import re
import logging

# Set up logging for the fixture file
logging.basicConfig(level=logging.INFO, # Keep INFO for debugging fixtures
                    format='%(asctime)s - %(levelname)s - %(name)s:%(lineno)d - %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = "https://mylibribooks.com/"
SIGNIN_URL = "https://mylibribooks.com/signin"
VALID_USERNAME = os.getenv("VALID_USERNAME")
VALID_PASSWORD = os.getenv("VALID_PASSWORD")

# Removed scroll_to_bottom helper for direct sign-in, as it's not needed here

@pytest.fixture(scope="function")
def mobile_login_setup(page: Page):
    """
    Fixture to handle mobile emulation, direct navigation to sign-in page,
    login, and verification of successful login to 'My Library' page.
    """
    logger.info(f"[Fixture] Navigating directly to sign-in page: {SIGNIN_URL}")
    page.goto(SIGNIN_URL)
    # Use 'domcontentloaded' again, as the form seems to render quickly based on the screenshot
    # We will let Playwright's auto-waiting handle most waits for actionability.
    page.wait_for_load_state("domcontentloaded") 
    page.wait_for_timeout(2000) # Small pause after navigation, adjust if needed

    logger.info("[Fixture] On sign-in page. Proceeding with credentials.")

    try:
        # **DIRECT AND ACCURATE LOCATORS FROM image_a4ef8d.png**
        # Email input: Has type='email' and placeholder='Email address'
        email_input_locator = page.locator("input[type='email'][placeholder='Email address']")
        
        # Password input: Has type='password' and placeholder='Password'
        password_input_locator = page.locator("input[type='password'][placeholder='Password']")
        
        # Login button: Is a button, contains text 'Login' and has class 'btn-login-button'
        # The screenshot shows 'Login' on the button, not 'Sign in'.
        login_button_locator = page.locator("button.btn-login-button:has-text('Login')") 
        
        # Adding an explicit wait for the "Sign In" header, which is very clear in the screenshot.
        # It's an <h5> tag inside a div with class 'lib-login-wrapper'.
        sign_in_header_locator = page.locator("div.lib-login-wrapper h5:has-text('Sign In')")
        
        logger.info("Waiting for 'Sign In' header to be visible...")
        expect(sign_in_header_locator).to_be_visible(timeout=10000) # Increased timeout slightly for initial page load, but not excessive.

        logger.info("Waiting for email input to be visible and fillable...")
        expect(email_input_locator).to_be_visible(timeout=5000) # Reduce specific waits if the form is already loaded
        expect(email_input_locator).to_be_editable(timeout=5000) 
        email_input_locator.fill(VALID_USERNAME)
        logger.info(f"Email field filled with {VALID_USERNAME}.")

        logger.info("Waiting for password input to be visible and fillable...")
        expect(password_input_locator).to_be_visible(timeout=5000)
        expect(password_input_locator).to_be_editable(timeout=5000)
        password_input_locator.fill(VALID_PASSWORD)
        logger.info("Password field filled.")

        logger.info("Waiting for login button to be visible and enabled, then clicking...")
        expect(login_button_locator).to_be_visible(timeout=5000)
        expect(login_button_locator).to_be_enabled(timeout=5000)
        login_button_locator.click()
        logger.info("Login button clicked.")

        # Wait for post-login state
        page.wait_for_load_state("networkidle") 
        page.wait_for_timeout(5000) # Final buffer for page render

        # Assert successful login (e.g., check URL or presence of a post-login element)
        expect(page).to_have_url(re.compile(r".*/library"), timeout=20000) # Keep higher timeout for navigation
        expect(page.locator("li:has-text('My Books')")).to_be_visible(timeout=15000)
        logger.info("[Fixture] Successfully logged in and navigated to My Library.")

    except Exception as e:
        logger.error(f"❌ [Fixture] Login failed during setup: {e}")
        screenshot_path = Path("test_reports") / f"error_login_setup_failed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        page.screenshot(path=screenshot_path, full_page=True)
        logger.info(f"[Fixture] Screenshot taken: {screenshot_path}")
        html_path = Path("test_reports") / f"error_login_setup_failed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(page.content())
        logger.info(f"[Fixture] Page HTML saved: {html_path}")
        pytest.fail(f"Login setup failed: {e}")

    yield page
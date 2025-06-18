import pytest
from playwright.sync_api import sync_playwright, expect
from pathlib import Path
from datetime import datetime
import re
import logging

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(name)s:%(lineno)d - %(message)s')
logger = logging.getLogger(__name__)

# Constants (Using INVALID credentials for this specific test)
URL = "https://mylibribooks.com"
LOGIN_URL = f"{URL}/signin"
# !!! IMPORTANT: Use truly invalid credentials for this test !!!
INVALID_EMAIL = "nobody_noone@gmail.com" # As per your screenshot
INVALID_PASSWORD = "wrongpassword12345" # Ensure this is unique and wrong
TIMEOUT = 45000 # Overall timeout for page operations

# --- Specific Device Configuration ---
TARGET_DEVICE_NAME = 'iPhone 13'

@pytest.mark.mobile
def test_mobile_invalid_login():
    """
    Tests the mobile login flow with invalid credentials (non-existent user),
    expecting an error message and no successful login.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    sanitized_device_name = re.sub(r'[^\w\-_\.]', '', TARGET_DEVICE_NAME)
    test_report_dir = Path(f"test_reports/mobile_invalid_login_{sanitized_device_name}_{timestamp}")
    test_report_dir.mkdir(parents=True, exist_ok=True)

    browser = None
    page = None

    try:
        with sync_playwright() as p:
            device_config = p.devices[TARGET_DEVICE_NAME]
            browser_type = p.chromium

            browser = browser_type.launch(headless=False, slow_mo=100)
            context = browser.new_context(
                **device_config,
                locale='en-US',
                timezone_id='America/Los_Angeles',
                java_script_enabled=True,
                ignore_https_errors=True
            )
            context.set_default_timeout(TIMEOUT)
            page = context.new_page()
            page.set_default_navigation_timeout(TIMEOUT)

            logger.info(f"Starting invalid login test on device: {TARGET_DEVICE_NAME} ({browser_type.name})")

            # --- Step 1: Navigate directly to Login Page ---
            logger.info(f"Navigating directly to login page: {LOGIN_URL}")
            page.goto(LOGIN_URL, wait_until="domcontentloaded")
            page.screenshot(path=test_report_dir / f"01_login_page_initial_{sanitized_device_name}.png")
            expect(page).to_have_url(re.compile("signin|login", re.IGNORECASE))
            logger.info("On sign-in page. Proceeding with invalid credentials.")

            # --- Step 2: Fill Invalid Login Credentials ---
            logger.info("Filling invalid login credentials.")
            page.get_by_label("Email").or_(page.locator("input[type='email']")).fill(INVALID_EMAIL)
            page.get_by_label("Password").or_(page.locator("input[type='password']")).fill(INVALID_PASSWORD)

            # --- Step 3: Click Login Button ---
            login_button = page.get_by_role("button", name=re.compile("login|sign in", re.IGNORECASE))
            login_button.click()
            logger.info("Clicked login button with invalid credentials.")

            # --- Step 4: Verify Error Message and No Redirection ---
            logger.info("Verifying that an error message is displayed and login is unsuccessful.")

            # IMPORTANT DEBUG STEP: Screenshot and page source for further analysis if needed
            # This is still valuable if the new locator fails or for future debugging.
            page.screenshot(path=test_report_dir / f"DEBUG_02_login_failed_before_error_check_{sanitized_device_name}.png", full_page=True)
            logger.info(f"DEBUG: Screenshot taken before error message assertion: {test_report_dir / f'DEBUG_02_login_failed_before_error_check_{sanitized_device_name}.png'}")
            with open(test_report_dir / f"DEBUG_02_login_failed_page_source_{sanitized_device_name}.html", "w", encoding="utf-8") as f:
                f.write(page.content())
            logger.info(f"DEBUG: Page source dumped for inspection: {test_report_dir / f'DEBUG_02_login_failed_page_source_{sanitized_device_name}.html'}")

            # --- REVISED ERROR MESSAGE LOCATOR based on the screenshot and the new understanding ---
            # Targeting the main red banner error message using a regex for flexibility
            # This covers "User does not exist" and the subsequent text, even if split.
            error_message_locator = page.get_by_text(re.compile("User does not exist", re.IGNORECASE))

            # Assert that the error message is visible. The expect.to_be_visible() has its own timeout.
            expect(error_message_locator).to_be_visible(timeout=10000)
            logger.info(f"Main error message displayed: '{error_message_locator.text_content()}'")

            # Additionally, check for the field-level validation for "invalid email"
            # This is a good secondary check for this specific 'non-existent user' scenario.
            field_error_locator = page.get_by_text("Please input a valid email")
            expect(field_error_locator).to_be_visible(timeout=5000)
            logger.info(f"Field-level error message displayed: '{field_error_locator.text_content()}'")


            # Assert that the URL *remains* on the login page (no redirection to dashboard/home)
            expect(page).to_have_url(re.compile("signin|login", re.IGNORECASE))
            logger.info("Verified URL remains on the login page, confirming no successful login.")

            page.screenshot(path=test_report_dir / f"03_login_failed_final_{sanitized_device_name}.png")
            logger.info("Invalid login test completed successfully: error messages displayed and no login.")

    except Exception as e:
        logger.error(f"❌ Test failed unexpectedly for {TARGET_DEVICE_NAME}: {e}")
        if page:
            try:
                page.screenshot(path=test_report_dir / f"error_final_{sanitized_device_name}.png", full_page=True)
                with open(test_report_dir / f"error_page_source_final_{sanitized_device_name}.html", "w", encoding="utf-8") as f:
                    f.write(page.content())
            except Exception as se:
                logger.warning(f"Could not take final error screenshot for {sanitized_device_name}: {se}")
        raise

    finally:
        if browser:
            try:
                browser.close()
                logger.info(f"Browser for {TARGET_DEVICE_NAME} closed successfully.")
            except Exception as ce:
                logger.warning(f"Error closing browser for {TARGET_DEVICE_NAME}: {ce}")
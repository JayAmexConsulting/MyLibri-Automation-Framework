import pytest
import re
import os
import logging
from datetime import datetime
from pathlib import Path
from playwright.sync_api import Page, expect, sync_playwright

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Constants
URL = "https://mylibribooks.com"
LOGIN_URL = f"{URL}/signin"

# --- REQUIRED: Specify the invalid email and invalid password directly in the script ---
INVALID_EMAIL = "nobody_noone@gmail.com" # As per your original script
INVALID_PASSWORD = "wrongpassword12345" # Ensure this is unique and wrong

# TARGET_DEVICE_NAME is typically configured in pytest.ini's [pytest-playwright] section.
TARGET_DEVICE_NAME = 'iPhone 13'

# Define a fixture for mobile context to ensure emulation and headful mode for observation
@pytest.fixture(scope="function")
def mobile_page(playwright, browser_type): # 'browser_type' comes from pytest-playwright
    # Get the Playwright device descriptor for iPhone 13
    try:
        # Access devices from the 'playwright' object directly
        iphone_13 = playwright.devices[TARGET_DEVICE_NAME]
    except KeyError:
        logger.warning(f"Device '{TARGET_DEVICE_NAME}' not found in Playwright's built-in devices. Using default mobile settings.")
        # Fallback to generic mobile settings if specific device is not found
        iphone_13 = {
            # CORRECTED SYNTAX: Changed "13.1.1" to '13.1.1' to fix previous SyntaxError
            "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 13_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version='13.1.1' Mobile/15E148 Safari/604.1",
            "viewport": {"width": 375, "height": 667},
            "is_mobile": True,
            "has_touch": True,
            "device_scale_factor": 2
        }

    # Launch a new browser instance explicitly with headless=False for observation
    # This ensures the browser window is visible for debugging.
    browser_instance = browser_type.launch(headless=False)
    context = browser_instance.new_context(**iphone_13)
    # The original script had a high TIMEOUT. Set default timeout for the context if needed.
    # context.set_default_timeout(45000) # Re-add if 45s timeout is consistently required
    # page.set_default_navigation_timeout(45000) # Re-add if 45s nav timeout is consistently required
    page = context.new_page()
    yield page
    page.close()
    context.close()
    browser_instance.close()


@pytest.mark.mobile
def test_mobile_invalid_login(mobile_page: Page): # Use the custom mobile_page fixture
    """
    Tests the mobile login flow with invalid credentials (non-existent user),
    expecting specific error messages and no successful login.
    """
    page = mobile_page # Assign the page from the fixture

    # The email and password are now directly specified, no need to check os.getenv
    logger.info(f"Using specified invalid email: '{INVALID_EMAIL}' and invalid password.")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    sanitized_device_name = re.sub(r'[^\w\-_\.]', '', TARGET_DEVICE_NAME)
    test_report_dir = Path(f"test_reports/mobile_invalid_login_{sanitized_device_name}_{timestamp}")
    test_report_dir.mkdir(parents=True, exist_ok=True)

    try:
        logger.info(f"Starting invalid login test on device: {TARGET_DEVICE_NAME}")

        # --- Step 1: Navigate directly to Login Page ---
        logger.info(f"Navigating directly to login page: {LOGIN_URL}")
        # Use "domcontentloaded" as it was successful in previous scripts for initial page load.
        page.goto(LOGIN_URL, wait_until="domcontentloaded")
        
        # Taking a screenshot of the initial login page
        page.screenshot(path=test_report_dir / f"01_login_page_initial_{sanitized_device_name}.png")
        # Assert that the URL is indeed the signin/login page
        expect(page).to_have_url(re.compile("signin|login", re.IGNORECASE))
        logger.info("On sign-in page. Proceeding with invalid credentials.")

        # --- Step 2: Fill Invalid Login Credentials ---
        logger.info(f"Filling email: '{INVALID_EMAIL}' and password.")
        email_input = page.get_by_label("Email").or_(page.locator("input[type='email']"))
        password_input = page.get_by_label("Password").or_(page.locator("input[type='password']"))
        
        # Directly fill the fields. Playwright's fill method automatically waits for the element to be ready.
        email_input.fill(INVALID_EMAIL)
        password_input.fill(INVALID_PASSWORD)
        logger.info(f"Email and password fields filled.")

        # --- Step 3: Click Login Button ---
        login_button = page.get_by_role("button", name=re.compile("login|sign in", re.IGNORECASE))
        # No explicit pre-click expect().to_be_visible/enabled needed here, Playwright's click also waits.
        login_button.click()
        logger.info("Clicked login button with invalid credentials.")

        # --- Step 4: Verify Error Messages and No Redirection ---
        logger.info("Verifying that error messages are displayed and login is unsuccessful.")

        # IMPORTANT: Based on previous successful test, assert each specific error message.
        # This avoids strict mode violation if both messages appear.
        # The messages "User does not exist" and "Please check your email and password"
        # were observed for valid email/wrong password.
        # Assuming the same messages for invalid email/invalid password based on provided image_b1aeab.png and image_b1b18b.png.

        # Assert the first part of the error message
        expect(page.get_by_text("User does not exist")).to_be_visible(timeout=10000) #
        logger.info("Error message 'User does not exist' is visible.")

        # Assert the second part of the error message
        expect(page.get_by_text("Please check your email and password")).to_be_visible(timeout=10000) #
        logger.info("Error message 'Please check your email and password' is visible.")

        # In your provided image_b1aeab.png, there are also "Please input a valid email" and "Please input a valid password"
        # validation messages under the input fields. We can add assertions for these as well to be thorough.
        expect(page.get_by_text("Please input a valid email")).to_be_visible(timeout=5000)
        logger.info("Field-level error 'Please input a valid email' is visible.")

        expect(page.get_by_text("Please input a valid password")).to_be_visible(timeout=5000)
        logger.info("Field-level error 'Please input a valid password' is visible.")


        # Assert no redirection: URL remains on login page
        expect(page).to_have_url(re.compile(f"^{re.escape(URL)}/(signin|login)/?$", re.IGNORECASE), timeout=5000)
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
        raise # Re-raise the exception to mark the test as failed by pytest
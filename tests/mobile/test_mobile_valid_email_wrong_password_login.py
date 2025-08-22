import pytest
import re
import os
import logging
from datetime import datetime
from pathlib import Path
from playwright.sync_api import Page, expect

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

# --- REQUIRED: Specify the valid email and a wrong password directly in the script ---
VALID_REGISTERED_EMAIL = "cpot.tea@gmail.com" # As per your example
INCORRECT_PASSWORD_FOR_VALID_EMAIL = "ThisIsDefinitelyTheWrongPassword123" # A uniquely wrong password

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
    page = context.new_page()
    yield page
    page.close()
    context.close()
    browser_instance.close()


@pytest.mark.mobile
def test_mobile_valid_email_wrong_password_login(mobile_page: Page): # Use the custom mobile_page fixture
    """
    Tests the mobile login flow with a valid email address but an incorrect password,
    expecting specific error messages and no successful login.
    """
    page = mobile_page # Assign the page from the fixture

    # The email is now directly specified, no need to check os.getenv
    logger.info(f"Using specified valid email: '{VALID_REGISTERED_EMAIL}' and wrong password.")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    sanitized_device_name = re.sub(r'[^\w\-_\.]', '', TARGET_DEVICE_NAME)
    test_report_dir = Path(f"test_reports/mobile_valid_email_wrong_password_login_{sanitized_device_name}_{timestamp}")
    test_report_dir.mkdir(parents=True, exist_ok=True)

    try:
        logger.info(f"Starting valid email/wrong password test on device: {TARGET_DEVICE_NAME}")

        # --- Step 1: Navigate directly to Login Page ---
        logger.info(f"Navigating directly to login page: {LOGIN_URL}")
        page.goto(LOGIN_URL, wait_until="domcontentloaded")
        
        # We assume the page loads correctly and elements are interactive after goto, based on provided screenshots.
        page.screenshot(path=test_report_dir / f"01_login_page_initial_{sanitized_device_name}.png")
        expect(page).to_have_url(re.compile("signin|login", re.IGNORECASE))
        logger.info("On sign-in page. Proceeding with valid email and wrong password.")

        # --- Step 2: Input Valid Email and Wrong Password ---
        logger.info(f"Inputting email: '{VALID_REGISTERED_EMAIL}' and a wrong password.")
        email_input = page.get_by_label("Email").or_(page.locator("input[type='email']"))
        password_input = page.get_by_label("Password").or_(page.locator("input[type='password']"))
        
        # Directly fill the fields. Playwright's fill method waits for the element to be ready.
        email_input.fill(VALID_REGISTERED_EMAIL)
        password_input.fill(INCORRECT_PASSWORD_FOR_VALID_EMAIL)
        logger.info(f"Email and password fields filled.")

        # --- Step 3: Click Login Button ---
        login_button = page.get_by_role("button", name=re.compile("login|sign in", re.IGNORECASE))
        # No explicit pre-click expect().to_be_visible/enabled needed here, Playwright's click also waits.
        login_button.click()
        logger.info("Clicked login button with valid email and wrong password.")

        # --- Step 4: Verify Error Messages and No Redirection ---
        logger.info("Verifying that error messages are displayed and login is unsuccessful.")

        # Assert the first part of the error message
        expect(page.get_by_text("User does not exist")).to_be_visible(timeout=10000)
        logger.info("Error message 'User does not exist' is visible.")

        # Assert the second part of the error message
        expect(page.get_by_text("Please check your email and password")).to_be_visible(timeout=10000)
        logger.info("Error message 'Please check your email and password' is visible.")

        # Assert no redirection: URL remains on login page
        expect(page).to_have_url(re.compile(f"^{re.escape(URL)}/(signin|login)/?$", re.IGNORECASE), timeout=5000)
        logger.info("Verified URL remains on the login page, confirming no successful login.")

        page.screenshot(path=test_report_dir / f"03_login_failed_final_{sanitized_device_name}.png")
        logger.info("Valid email/wrong password login test completed successfully.")

    except Exception as e:
        logger.error(f"❌ Test failed unexpectedly for {TARGET_DEVICE_NAME}: {e}")
        if page:
            try:
                page.screenshot(path=test_report_dir / f"error_final_{sanitized_device_name}.png", full_page=True)
                with open(test_report_dir / f"error_page_source_final_{sanitized_device_name}.html", "w", encoding="utf-8") as f:
                    f.write(page.content())
            except Exception as se:
                logger.warning(f"Could not take final error screenshot/page source for {sanitized_device_name}: {se}")
        raise # Re-raise the exception to mark the test as failed by pytest
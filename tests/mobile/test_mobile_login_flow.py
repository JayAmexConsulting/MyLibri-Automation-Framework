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

# Constants (replace with your actual values or environment variables)
URL = "https://mylibribooks.com"
LOGIN_URL = f"{URL}/signin"  # Direct sign-in URL
EMAIL = "cpot.tea@gmail.com"  # Replace with a valid test email
PASSWORD = "Moniwyse!400"  # Replace with a valid test password
TIMEOUT = 60000  # Default timeout for Playwright operations (60 seconds)

# --- Specific Device Configuration ---
TARGET_DEVICE_NAME = 'iPhone 13'

@pytest.mark.mobile
def test_iphone_login_logout_flow():
    """
    Tests the mobile login and logout flow for mylibribooks.com,
    emulating a specific iPhone device (iPhone 13) using Chromium.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    sanitized_device_name = re.sub(r'[^\w\-_\.]', '', TARGET_DEVICE_NAME)
    test_report_dir = Path(f"test_reports/iphone_login_logout_flow_{sanitized_device_name}_{timestamp}")
    test_report_dir.mkdir(parents=True, exist_ok=True)

    browser = None
    page = None

    try:
        with sync_playwright() as p:
            device_config = p.devices[TARGET_DEVICE_NAME]
            browser_type = p.chromium 

            browser = browser_type.launch(headless=False, slow_mo=100) # slow_mo helps visualize
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

            logger.info(f"Starting test on device: {TARGET_DEVICE_NAME} ({browser_type.name})")

            # --- Step 1: Navigate to Login Page and Log In ---
            logger.info(f"Navigating to login page: {LOGIN_URL}")
            page.goto(LOGIN_URL, wait_until="domcontentloaded")
            page.screenshot(path=test_report_dir / f"01_login_page_{sanitized_device_name}.png")
            expect(page).to_have_url(re.compile("signin|login", re.IGNORECASE))
            logger.info("On sign-in page. Filling credentials.")

            page.get_by_label("Email").or_(page.locator("input[type='email']")).fill(EMAIL)
            page.get_by_label("Password").or_(page.locator("input[type='password']")).fill(PASSWORD)
            
            login_button = page.get_by_role("button", name=re.compile("login|sign in", re.IGNORECASE))
            login_button.click()
            
            expect(page).to_have_url(re.compile("home|dashboard|account|profile", re.IGNORECASE))
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(2000) # Small buffer for initial dashboard rendering
            page.screenshot(path=test_report_dir / f"02_dashboard_after_login_{sanitized_device_name}.png")
            logger.info("Login successful. Navigated to dashboard/home page.")

            # --- Scroll to bottom of the page (Optional, can be removed if not strictly necessary) ---
            logger.info("Scrolling to the bottom of the page.")
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(1000) 
            page.screenshot(path=test_report_dir / f"02a_dashboard_scrolled_{sanitized_device_name}.png")


            # --- Step 2: Navigate to Profile Page ---
            logger.info("Navigating to profile via hamburger menu and profile dropdown.")
            
            # Click Hamburger Menu
            hamburger_menu_locator = page.locator("div.toggle-button")
            hamburger_menu_locator.click()
            logger.info("Clicked hamburger menu icon.")
            page.wait_for_timeout(500) # Small pause for menu to open

            # Click Profile Dropdown Arrow
            profile_arrow_locator = page.locator('div.profile svg')
            profile_arrow_locator.click()
            logger.info("Clicked profile dropdown arrow.")
            page.wait_for_timeout(500) # Small pause for dropdown to reveal "Tea Pot"

            # Click "Tea Pot" (Profile Name) to go to profile page
            profile_name_locator = page.get_by_text("Tea Pot", exact=True)
            profile_name_locator.click()
            logger.info("Clicked 'Tea Pot' to navigate to profile page.")

            # Verify navigation to the profile page
            expect(page).to_have_url(re.compile("home|profile", re.IGNORECASE))
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(2000) # Small buffer for profile page rendering

            # Verify 'Bio Data' section is active (optional, remove if not a strict requirement for flow success)
            bio_data_locator = page.locator("div.profile-page-container div.sidebar-content ul li:has-text('Bio Data')")
            expect(bio_data_locator).to_have_class(re.compile(r".*\bactive\b.*"))
            logger.info("'Bio Data' section is active on profile page.")
            
            page.screenshot(path=test_report_dir / f"03_profile_page_loaded_{sanitized_device_name}.png")
            logger.info("Successfully navigated to and verified profile page.")


            # --- Step 3: Log Out ---
            logger.info("Initiating logout flow.")
            page.screenshot(path=test_report_dir / f"04_before_logout_click_{sanitized_device_name}.png") 

            # Re-click Hamburger Menu (if needed, Playwright will manage)
            hamburger_menu_locator.click()
            logger.info("Re-clicked hamburger menu.")
            page.wait_for_timeout(500)

            # Re-click Profile Dropdown Arrow (if needed, Playwright will manage)
            profile_arrow_locator.click()
            logger.info("Re-clicked profile dropdown arrow.")
            page.wait_for_timeout(500)

            # Click "Log out" link
            log_out_link_locator = page.get_by_text("Log out", exact=True)
            log_out_link_locator.click(timeout=15000) # Increased implicit click timeout for robustness
            logger.info("Clicked 'Log out' link.")

            # --- Post-Logout Action: Wait and End Test ---
            logger.info("Logout click performed. Waiting 5 seconds before ending test.")
            page.wait_for_timeout(5000) # Wait for 5 seconds as requested

            logger.info("Test finished after logging out and waiting.")

    except Exception as e:
        logger.error(f"❌ Test failed for {TARGET_DEVICE_NAME}: {e}")
        if page:
            try:
                page.screenshot(path=test_report_dir / f"error_final_{sanitized_device_name}.png")
                with open(test_report_dir / f"error_page_source_final_{sanitized_device_name}.html", "w", encoding="utf-8") as f:
                    f.write(page.content())
            except Exception as se:
                logger.warning(f"Could not take final error screenshot for {sanitized_device_name}: {se}")
        raise # Re-raise the exception to mark the test as failed by pytest

    finally:
        if browser:
            try:
                browser.close()
                logger.info(f"Browser for {TARGET_DEVICE_NAME} closed successfully.")
            except Exception as ce:
                logger.warning(f"Error closing browser for {TARGET_DEVICE_NAME}: {ce}")
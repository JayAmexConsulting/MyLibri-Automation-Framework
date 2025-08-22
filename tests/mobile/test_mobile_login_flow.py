import pytest
import re
import logging
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright, Page, expect

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# --- HARDCODED CREDENTIALS AND URLS ---
VALID_EMAIL = "cpot.tea@gmail.com"
VALID_PASSWORD = "Moniwyse!400"

URL = "https://mylibribooks.com"
LOGIN_URL = f"{URL}/signin"

TARGET_DEVICE_NAME = 'iPhone 13' # This is for logging and report naming
# --- END HARDCODED VALUES ---

# Define a fixture for mobile context to ensure emulation
# This will also ensure the browser UI is visible for observation.
@pytest.fixture(scope="function")
def mobile_page(playwright, browser_type):
    # Get the Playwright device descriptor for iPhone 13
    try:
        # Access devices from the 'playwright' object directly
        iphone_13 = playwright.devices[TARGET_DEVICE_NAME]
    except KeyError:
        logger.warning(f"Device '{TARGET_DEVICE_NAME}' not found in Playwright's built-in devices. Using default mobile settings.")
        # Fallback to generic mobile settings if specific device is not found
        iphone_13 = {
            "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 13_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.1 Mobile/15E148 Safari/604.1",
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
def test_iphone_login_logout_flow(mobile_page: Page): # Use the custom mobile_page fixture
    """
    Tests the mobile login and logout flow for mylibribooks.com,
    emulating an iPhone 13 using Chromium, with explicit mobile context.
    Credentials are hardcoded within this script.
    """
    page = mobile_page # Assign the page from the fixture
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    sanitized_device_name = re.sub(r'[^\w\-_\.]', '', TARGET_DEVICE_NAME) # Sanitize for directory name
    test_report_dir = Path(f"test_reports/iphone_login_logout_flow_{sanitized_device_name}_{timestamp}")
    test_report_dir.mkdir(parents=True, exist_ok=True)

    try:
        logger.info(f"Starting test on device: {TARGET_DEVICE_NAME}")

        # --- Step 1: Navigate to Login Page and Log In ---
        logger.info(f"Navigating to login page: {LOGIN_URL}")
        page.goto(LOGIN_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(2000) # Small buffer for initial rendering

        page.screenshot(path=test_report_dir / f"01_login_page_{sanitized_device_name}.png")
        expect(page).to_have_url(re.compile("signin|login", re.IGNORECASE))
        logger.info("On sign-in page. Filling credentials.")

        email_field = page.get_by_label("Email").or_(page.locator("input[type='email']"))
        password_field = page.get_by_label("Password").or_(page.locator("input[type='password']"))

        expect(email_field).to_be_visible(timeout=10000)
        expect(email_field).to_be_editable(timeout=10000)
        email_field.fill(VALID_EMAIL)
        logger.info("Email field filled.")

        expect(password_field).to_be_visible(timeout=10000)
        expect(password_field).to_be_editable(timeout=10000)
        password_field.fill(VALID_PASSWORD)
        logger.info("Password field filled.")
        
        login_button = page.get_by_role("button", name=re.compile("login|sign in", re.IGNORECASE))
        expect(login_button).to_be_visible(timeout=10000)
        expect(login_button).to_be_enabled(timeout=10000)
        login_button.click()
        logger.info("Clicked login button.")
        
        expect(page).to_have_url(re.compile("home|dashboard|account|profile|library", re.IGNORECASE), timeout=30000)
        page.wait_for_load_state("networkidle") # Wait for network to be idle after URL change
        page.wait_for_timeout(2000) # Small buffer for visual stability
        page.screenshot(path=test_report_dir / f"02_dashboard_after_login_{sanitized_device_name}.png")
        logger.info("Login successful. Navigated to dashboard/home page.")

        logger.info("Proceeding with test after successful login and page load.")

        # --- Scroll to bottom of the page (Optional) ---
        logger.info("Scrolling to the bottom of the page (optional).")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1000)
        page.screenshot(path=test_report_dir / f"02a_dashboard_scrolled_{sanitized_device_name}.png")

        # --- IMPORTANT: Scroll back to top before interacting with top elements ---
        logger.info("Scrolling back to the top of the page.")
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(500) # Small wait for scroll to complete
        page.screenshot(path=test_report_dir / f"02b_scrolled_to_top_{sanitized_device_name}.png")

        # --- Step 2: Navigate to Profile Page ---
        logger.info("Navigating to profile via hamburger menu and profile dropdown.")
        
        # Hamburger Menu Locator
        hamburger_menu_locator = page.locator("div.toggle-button") 
        
        # Assert that the hamburger menu is visible and enabled, then click it immediately.
        logger.info("Ensuring hamburger menu is visible and enabled, then clicking...")
        expect(hamburger_menu_locator).to_be_visible(timeout=10000) 
        expect(hamburger_menu_locator).to_be_enabled(timeout=10000) 
        
        hamburger_menu_locator.click() 
        logger.info("Clicked hamburger menu icon.")

        # Click Profile Dropdown Arrow
        profile_arrow_locator = page.locator('div.profile svg').or_(
                                page.locator('div.profile button[aria-expanded]')).or_(
                                page.locator('div.profile .arrow-icon'))
        logger.info("Waiting for profile dropdown arrow to be visible and enabled...")
        expect(profile_arrow_locator).to_be_visible(timeout=10000)
        expect(profile_arrow_locator).to_be_enabled(timeout=10000)
        profile_arrow_locator.click()
        logger.info("Clicked profile dropdown arrow.")
        page.wait_for_timeout(1000)

        # Click "Tea Pot" (Profile Name) to go to profile page
        profile_name_locator = page.get_by_text("Tea Pot", exact=True)
        logger.info("Waiting for 'Tea Pot' profile name to be visible and enabled...")
        expect(profile_name_locator).to_be_visible(timeout=10000)
        expect(profile_name_locator).to_be_enabled(timeout=10000)
        profile_name_locator.click()
        logger.info("Clicked 'Tea Pot' to navigate to profile page.")

        # Verify navigation to the profile page
        expect(page).to_have_url(re.compile("home|profile", re.IGNORECASE), timeout=20000)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)

        # Verify 'Bio Data' section is active (optional)
        bio_data_locator = page.locator("div.profile-page-container div.sidebar-content ul li:has-text('Bio Data')")
        expect(bio_data_locator).to_have_class(re.compile(r".*\bactive\b.*"), timeout=10000)
        logger.info("'Bio Data' section is active on profile page.")
        
        page.screenshot(path=test_report_dir / f"03_profile_page_loaded_{sanitized_device_name}.png")
        logger.info("Successfully navigated to and verified profile page.")

        # --- Step 3: Log Out ---
        logger.info("Initiating logout flow.")
        page.screenshot(path=test_report_dir / f"04_before_logout_click_{sanitized_device_name}.png")

        # Re-click Hamburger Menu to reopen the navigation menu if it closed
        logger.info("Ensuring hamburger menu is open for logout...")
        expect(hamburger_menu_locator).to_be_visible(timeout=10000)
        expect(hamburger_menu_locator).to_be_enabled(timeout=10000)
        hamburger_menu_locator.click()
        logger.info("Re-clicked hamburger menu.")

        # Re-click Profile Dropdown Arrow to reveal "Log out" link if it closed
        logger.info("Ensuring profile dropdown is open to reveal logout link...")
        expect(profile_arrow_locator).to_be_visible(timeout=10000)
        expect(profile_arrow_locator).to_be_enabled(timeout=10000)
        profile_arrow_locator.click()
        logger.info("Re-clicked profile dropdown arrow.")
        page.wait_for_timeout(1000)

        # Click "Log out" link
        log_out_link_locator = page.get_by_text("Log out", exact=True)
        logger.info("Waiting for 'Log out' link to be visible and enabled, then clicking...")
        expect(log_out_link_locator).to_be_visible(timeout=10000)
        expect(log_out_link_locator).to_be_enabled(timeout=10000)
        log_out_link_locator.click()
        logger.info("Clicked 'Log out' link.")

        # --- Post-Logout Actions ---
        logger.info("Waiting 5 seconds after logout and capturing screenshot.")
        page.wait_for_timeout(5000) # Wait for 5 seconds
        page.screenshot(path=test_report_dir / f"05_after_logout_{sanitized_device_name}.png", full_page=True)
        logger.info("Screenshot captured after logout.")

        logger.info("Test finished after logging out.")

    except Exception as e:
        logger.error(f"❌ Test failed for {TARGET_DEVICE_NAME}: {e}")
        if page:
            try:
                page.screenshot(path=test_report_dir / f"error_final_{sanitized_device_name}.png", full_page=True)
                with open(test_report_dir / f"error_page_source_final_{sanitized_device_name}.html", "w", encoding="utf-8") as f:
                    f.write(page.content())
            except Exception as se:
                logger.warning(f"Could not take final error screenshot: {se}")
        raise # Re-raise the exception to mark the test as failed by pytest
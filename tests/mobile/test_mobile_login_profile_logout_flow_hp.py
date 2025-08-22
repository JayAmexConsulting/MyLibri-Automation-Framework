import pytest
import re
import os
import logging
from datetime import datetime
from pathlib import Path
from playwright.sync_api import Page, expect # Ensure 'Page' and 'expect' are imported

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

# Retrieve credentials from environment variables for security and flexibility
# REMINDER: Ensure VALID_USERNAME and VALID_PASSWORD are set before running tests
EMAIL = ("cpot.tea@gmail.com")
PASSWORD = ("Moniwyse!400")

# TARGET_DEVICE_NAME is typically configured in pytest.ini's [pytest-playwright] section.
TARGET_DEVICE_NAME = 'iPhone 13'

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
def test_mobile_login_profile_logout_flow_hp(mobile_page: Page): # Use the custom mobile_page fixture
    """
    Tests the mobile login flow by clicking a book, then logging in,
    navigating through profile sections, and finally logging out.
    Includes homepage content verification after logout.
    """
    page = mobile_page # Assign the page from the fixture

    # Check if environment variables are set; skip test if not found.
    if not EMAIL or not PASSWORD:
        pytest.skip("Login credentials (VALID_USERNAME, VALID_PASSWORD) not set as environment variables.")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    sanitized_device_name = re.sub(r'[^\w\-_\.]', '', TARGET_DEVICE_NAME)
    test_report_dir = Path(f"test_reports/mobile_login_profile_logout_flow_hp_{sanitized_device_name}_{timestamp}")
    test_report_dir.mkdir(parents=True, exist_ok=True)

    try:
        logger.info(f"Starting test on device: {TARGET_DEVICE_NAME} (configured via pytest.ini)")

        # --- Step 0: Navigate to Homepage and Ensure Ready State ---
        logger.info(f"Navigating to homepage: {URL}")
        page.goto(URL, wait_until="load")
        
        # Explicit wait for a prominent element on the homepage to ensure rendering
        page_structure_ready_selector = "div#root"
        page.wait_for_selector(page_structure_ready_selector, state="visible")
        logger.info(f"Page structural element '{page_structure_ready_selector}' is visible.")
        page.screenshot(path=test_report_dir / "01_homepage_initial_view.png")
        logger.info("Homepage initial view captured.")

        # --- Step 1: Locate and Click a Book to trigger Login (with controlled scrolling) ---
        logger.info("Attempting to locate and click on a book image to initiate login.")
        book_selector = "img[src*='libriapp/images']"
        book_locator = page.locator(book_selector).first

        # Introduce a controlled scroll to expose elements if not immediately visible
        # Scroll to the middle of the page to reveal books.
        logger.info("Scrolling to the middle of the page to reveal books if necessary.")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)") # Scroll to half the page height
        page.wait_for_timeout(2000) # Give time for content to load after scroll

        # Now, expect the book to be visible and clickable
        expect(book_locator).to_be_visible(timeout=10000) # Auto-waits for visibility up to 10s
        expect(book_locator).to_be_enabled(timeout=10000) # Auto-waits for enabled state up to 10s
        book_locator.click()
        logger.info(f"Clicked on the first visible and enabled book image found using selector: {book_selector}")
        page.screenshot(path=test_report_dir / "02_after_book_click_before_login.png")

        # --- Step 2: Fill Login Credentials and Log In ---
        logger.info("Verifying login screen presence and filling credentials.")
        
        # Expect URL to change to signin/login
        expect(page).to_have_url(re.compile("signin|login", re.IGNORECASE))
        page.screenshot(path=test_report_dir / "03_signin_page.png")
        logger.info("Confirmed sign-in page is displayed.")

        # Fill email and password (get_by_label and fill auto-wait)
        page.get_by_label("Email").or_(page.locator("input[type='email']")).fill(EMAIL)
        page.get_by_label("Password").or_(page.locator("input[type='password']")).fill(PASSWORD)

        login_button = page.get_by_role("button", name=re.compile("login|sign in", re.IGNORECASE))
        expect(login_button).to_be_visible() # Ensure button is visible before clicking
        expect(login_button).to_be_enabled() # Ensure button is enabled
        login_button.click()
        logger.info("Clicked login button.")

        # --- Verify successful login or report failure ---
        error_message_locator = page.locator("text=Invalid credentials").or_(page.locator("text=Login failed")).or_(page.locator("div.error-message"))
        
        if error_message_locator.is_visible(timeout=5000):
            page.screenshot(path=test_report_dir / "error_04_login_failed.png")
            error_text = error_message_locator.text_content()
            logger.error(f"Login failed: Error message detected: '{error_text}'")
            raise AssertionError(f"Login failed: {error_text}")

        expect(page).to_have_url(re.compile("home|dashboard|account|profile", re.IGNORECASE))
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000) # Small buffer for page rendering
        page.screenshot(path=test_report_dir / "04_dashboard_after_login.png")
        logger.info("Login successful. On dashboard/home page.")

        # --- Step 3: Navigate to Profile Page and Sections ---
        logger.info("Navigating to profile via hamburger menu and profile dropdown.")
        
        # Hamburger Menu Locator - Using the confirmed working locator from the previous successful script
        hamburger_menu_locator = page.locator("div.toggle-button") 
        
        # Explicitly wait for the hamburger menu to become visible after login, then click.
        logger.info("Waiting for hamburger menu to become visible, then clicking...")
        hamburger_menu_locator.wait_for(state="visible", timeout=10000) 
        hamburger_menu_locator.click()
        logger.info("Clicked hamburger menu icon.")
        page.wait_for_timeout(1000) # Small buffer for menu animation to complete

        # Click Profile Dropdown Arrow - USING THE CORRECTED LOCATOR (SVG inside div.profile)
        profile_arrow_locator = page.locator("div.profile > svg") 
        logger.info("Clicking profile dropdown arrow (SVG inside div.profile).")
        # Playwright's .click() automatically waits for the element to be visible and enabled.
        profile_arrow_locator.click() 
        logger.info("Clicked profile dropdown arrow.")
        # No page.wait_for_timeout here, as requested, relying on Playwright's auto-waits.

        # Click "Tea Pot" (Profile Name) to go to profile page
        profile_name_locator = page.get_by_text("Tea Pot", exact=True)
        expect(profile_name_locator).to_be_visible()
        expect(profile_name_locator).to_be_enabled()
        profile_name_locator.click()
        logger.info("Clicked 'Tea Pot' to navigate to profile page.")

        # Verify navigation to the profile page URL
        expect(page).to_have_url(re.compile("home|profile", re.IGNORECASE))
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)

        # Verify 'Bio Data' section is active by default
        bio_data_locator = page.locator("div.profile-page-container div.sidebar-content ul li:has-text('Bio Data')")
        expect(bio_data_locator).to_have_class(re.compile(r".*\bactive\b.*"))
        logger.info("'Bio Data' section is active by default on profile page.")
        page.screenshot(path=test_report_dir / "05_profile_page_initial_view.png")
        logger.info("Successfully navigated to and verified profile page.")

        # Navigate and Screenshot each Profile Section
        profile_sections = [
            "Bio Data",
            "Wallet",
            "Subscription",
            "Change Password"
        ]

        for i, section_name in enumerate(profile_sections):
            logger.info(f"Attempting to navigate to '{section_name}' section.")
            section_locator = page.locator(f"div.sidebar-content ul li:has-text('{section_name}')")
            expect(section_locator).to_be_visible()
            expect(section_locator).to_be_enabled()
            section_locator.click()
            logger.info(f"Clicked '{section_name}'.")
            
            # Use networkidle for content changes, then a short timeout
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(1500)

            # Scroll to the bottom and take a full page screenshot
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(3000)
            screenshot_filename = f"0{6+i:02d}_profile_{section_name.lower().replace(' ', '_')}.png"
            page.screenshot(path=test_report_dir / screenshot_filename, full_page=True)
            logger.info(f"Full page screenshot of '{section_name}' section captured.")

            # Scroll back to the top to prepare for the next section click (if any)
            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(1000) # Reduced timeout for simple scroll back
        logger.info("Successfully navigated through all profile sections.")

        # --- Step 4: Log Out ---
        logger.info("Initiating logout flow with homepage content verification (targeting App Store link specifically).")

        # Re-click Hamburger Menu to open the main navigation if it has closed
        logger.info("Ensuring hamburger menu is visible before re-clicking for logout...")
        hamburger_menu_locator.wait_for(state="visible", timeout=10000) 
        hamburger_menu_locator.click()
        logger.info("Re-clicked hamburger menu to ensure it's open for logout.")
        page.wait_for_timeout(1000) # Allow menu animation

        # Re-click Profile Dropdown Arrow to reveal "Log out" link if it has closed
        profile_arrow_locator = page.locator("div.profile > svg") 
        logger.info("Re-clicking profile dropdown arrow (SVG inside div.profile) to show 'Log out' option.")
        profile_arrow_locator.click()
        logger.info("Re-clicked profile dropdown arrow.")
        # No page.wait_for_timeout here, as requested, relying on Playwright's auto-waits.

        # Click the "Log out" link
        log_out_link_locator = page.get_by_text("Log out", exact=True)
        expect(log_out_link_locator).to_be_visible()
        expect(log_out_link_locator).to_be_enabled()
        log_out_link_locator.click()
        logger.info("Clicked 'Log out' link.")

        # --- Verify Logout by checking URL and a prominent element on the logged-out homepage ---
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)

        # Assert that the URL is the base homepage URL after logout
        expect(page).to_have_url(re.compile(f"^{re.escape(URL)}/?$"))
        logger.info("Verified URL is the homepage after logout.")

        # Assert that the "Download on the App Store" link is visible, indicating logged-out state
        # This is the ONLY difference in logic from the previous script.
        app_store_link_locator = page.get_by_role("link", name="Download on the App Store").first
        expect(app_store_link_locator).to_be_visible(timeout=15000) # Ensure it loads within a reasonable time
        logger.info("Verified 'Download on the App Store' link is visible, confirming logged-out state.")

        page.screenshot(path=test_report_dir / "final_07_after_logout_verified_homepage_app_store.png")
        logger.info("Successfully logged out and verified return to the main homepage. Test completed.")

    except Exception as e:
        logger.error(f"❌ Test failed unexpectedly for {TARGET_DEVICE_NAME}: {e}")
        # Always attempt to take a screenshot and save page content on error
        if page:
            try:
                page.screenshot(path=test_report_dir / f"error_final_{sanitized_device_name}.png", full_page=True)
                with open(test_report_dir / f"error_page_source_final_{sanitized_device_name}.html", "w", encoding="utf-8") as f:
                    f.write(page.content())
            except Exception as se:
                logger.warning(f"Could not take final error screenshot/page source for {sanitized_device_name}: {se}")
        raise # Re-raise the exception to mark the test as failed by pytest
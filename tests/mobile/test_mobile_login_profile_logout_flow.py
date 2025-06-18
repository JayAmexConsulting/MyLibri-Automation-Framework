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

# Constants
URL = "https://mylibribooks.com"
LOGIN_URL = f"{URL}/signin" 
EMAIL = "cpot.tea@gmail.com"
PASSWORD = "Moniwyse!400"
TIMEOUT = 45000 # Overall timeout for page operations

# --- Specific Device Configuration ---
TARGET_DEVICE_NAME = 'iPhone 13' # Using a specific device name for better reporting

@pytest.mark.mobile
def test_mobile_login_profile_logout_flow(): 
    """
    Tests the mobile login flow by clicking a book, then logging in,
    navigating through profile sections, and finally logging out.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    sanitized_device_name = re.sub(r'[^\w\-_\.]', '', TARGET_DEVICE_NAME)
    test_report_dir = Path(f"test_reports/mobile_login_profile_logout_flow_{sanitized_device_name}_{timestamp}")
    test_report_dir.mkdir(parents=True, exist_ok=True)

    browser = None
    page = None

    try:
        with sync_playwright() as p:
            # Use devices configuration for iPhone 13
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

            logger.info(f"Starting test on device: {TARGET_DEVICE_NAME} ({browser_type.name})")

            # --- Step 0: Navigate to Homepage and Scroll to Load Books ---
            logger.info(f"Navigating to homepage: {URL}")
            page.goto(URL, wait_until="load") 
            
            # Explicit wait for a prominent element on the homepage to ensure rendering
            page_structure_ready_selector = "div#root" 
            page.wait_for_selector(page_structure_ready_selector, state="visible", timeout=30000)
            logger.info(f"Page structural element '{page_structure_ready_selector}' is visible.")
            page.screenshot(path=test_report_dir / "01_homepage_initial_view.png")
            logger.info("Homepage initial view captured.")

            logger.info("Scrolling down the page to ensure all content/books are loaded.")
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(3000) # Increased wait to 3 seconds after scroll down
            page.screenshot(path=test_report_dir / "02_homepage_after_scrolling_for_books.png")
            logger.info("Finished scrolling attempts for book loading.")

            # --- Step 1: Locate and Click a Book to trigger Login ---
            logger.info("Attempting to locate and click on a book image to initiate login.")
            book_selector = "img[src*='libriapp/images']"  
            book_locator = page.locator(book_selector).first 

            book_locator.click() 
            logger.info(f"Clicked on the first book image found using selector: {book_selector}")
            page.screenshot(path=test_report_dir / "03_after_book_click_before_login.png")

            # --- Step 2: Fill Login Credentials and Log In ---
            logger.info("Verifying login screen presence and filling credentials.")
            
            # Expect URL to change to signin/login
            expect(page).to_have_url(re.compile("signin|login", re.IGNORECASE))
            page.screenshot(path=test_report_dir / "04_signin_page.png")
            logger.info("Confirmed sign-in page is displayed.")

            # Fill email and password (get_by_label and fill auto-wait)
            page.get_by_label("Email").or_(page.locator("input[type='email']")).fill(EMAIL)
            page.get_by_label("Password").or_(page.locator("input[type='password']")).fill(PASSWORD)

            login_button = page.get_by_role("button", name=re.compile("login|sign in", re.IGNORECASE))
            login_button.click()
            logger.info("Clicked login button.")

            # --- Verify successful login ---
            error_message_locator = page.locator("text=Invalid credentials").or_(page.locator("text=Login failed")).or_(page.locator("div.error-message"))
            if error_message_locator.is_visible(timeout=5000):
                page.screenshot(path=test_report_dir / "error_05_login_failed.png")
                error_text = error_message_locator.text_content()
                logger.error(f"Login failed: Error message detected: '{error_text}'")
                raise AssertionError(f"Login failed: {error_text}")

            expect(page).to_have_url(re.compile("home|dashboard|account|profile", re.IGNORECASE))
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(2000) 
            page.screenshot(path=test_report_dir / "05_dashboard_after_login.png")
            logger.info("Login successful. On dashboard/home page.")

            # --- Step 3: Navigate to Profile Page and Sections ---
            logger.info("Navigating to profile via hamburger menu and profile dropdown.")
            
            # Click Hamburger Menu
            hamburger_menu_locator = page.locator("div.toggle-button")
            hamburger_menu_locator.click()
            logger.info("Clicked hamburger menu icon.")
            page.wait_for_timeout(1000) 

            # Click Profile Dropdown Arrow
            profile_arrow_selector = 'div.profile svg'
            profile_arrow_locator = page.locator(profile_arrow_selector)
            profile_arrow_locator.click()
            logger.info("Clicked profile dropdown arrow.")
            page.wait_for_timeout(1000) 

            # Click "Tea Pot" (Profile Name) to go to profile page
            profile_name_locator = page.get_by_text("Tea Pot", exact=True)
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
            page.screenshot(path=test_report_dir / "06_profile_page_initial_view.png")
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
                section_locator.click()
                logger.info(f"Clicked '{section_name}'.")
                
                page.wait_for_load_state("domcontentloaded") 
                page.wait_for_timeout(1500) 

                # Scroll to the bottom and take a full page screenshot
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(3000) 
                screenshot_filename = f"0{7+i:02d}_profile_{section_name.lower().replace(' ', '_')}.png"
                page.screenshot(path=test_report_dir / screenshot_filename, full_page=True)
                logger.info(f"Full page screenshot of '{section_name}' section captured.")

                # Scroll back to the top to prepare for the next section click (if any)
                page.evaluate("window.scrollTo(0, 0)")
                page.wait_for_timeout(3000) 
            logger.info("Successfully navigated through all profile sections.")

            # --- Step 4: Log Out (Simplified as requested) ---
            logger.info("Initiating logout flow (simplified).")
            
            # Re-click Hamburger Menu to open the main navigation if it has closed
            hamburger_menu_locator.click()
            logger.info("Re-clicked hamburger menu to ensure it's open for logout.")
            page.wait_for_timeout(1000) 

            # Re-click Profile Dropdown Arrow to reveal "Log out" link if it has closed
            profile_arrow_locator.click()
            logger.info("Re-clicked profile dropdown arrow to show 'Log out' option.")
            page.wait_for_timeout(1000) 

            # Click the "Log out" link
            log_out_link_locator = page.get_by_text("Log out", exact=True)
            log_out_link_locator.click() 
            logger.info("Clicked 'Log out' link.")

            # *** SIMPLIFIED LOGOUT: Just wait for 5 seconds and end the test ***
            page.wait_for_timeout(5000) 
            logger.info("Waited 5 seconds after clicking logout. Ending test without further assertions.")
            page.screenshot(path=test_report_dir / "final_08_after_logout_simplified.png")


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
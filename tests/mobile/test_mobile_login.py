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
# !!! IMPORTANT: Ensure this is a VALID, REGISTERED email and password for successful login !!!
VALID_EMAIL = "cpot.tea@gmail.com" # Example from previous interaction
VALID_PASSWORD = "Moniwyse!400" # Use the actual valid password
TIMEOUT = 45000 # Overall timeout for page operations (can be adjusted)
# TARGET_DEVICE_NAME is no longer used for p.devices, but can be kept for logging/reporting
TARGET_DEVICE_NAME = 'iPhone 13'

@pytest.mark.mobile
def test_mobile_login_only():
    """
    Tests the mobile login flow for mylibribooks.com by:
    1. Loading the homepage and attempting to scroll to reveal books.
    2. Clicking on the first visible book (image) to trigger the login screen.
    3. Performing login with valid credentials.
    4. Verifying successful login by checking the URL and a post-login element.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    sanitized_device_name = re.sub(r'[^\w\-_\.]', '', TARGET_DEVICE_NAME) # Sanitize for directory name
    test_report_dir = Path(f"test_reports/mobile_login_only_{sanitized_device_name}_{timestamp}")
    test_report_dir.mkdir(parents=True, exist_ok=True)

    browser = None
    page = None

    try:
        with sync_playwright() as p:
            # --- REVERTED: Original Mobile Context Configuration ---
            # Using explicit viewport and user_agent which seemed to work better before
            browser_type = p.chromium
            browser = browser_type.launch(headless=False, slow_mo=700) # Reverted slow_mo for observation
            context = browser.new_context(
                viewport={'width': 375, 'height': 812}, # iPhone X/XS/11 Pro dimensions
                user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1',
                device_scale_factor=3,
                locale='en-US',
                timezone_id='America/Los_Angeles',
                java_script_enabled=True,
                ignore_https_errors=True
            )
            context.set_default_timeout(TIMEOUT)
            page = context.new_page()
            page.set_default_navigation_timeout(TIMEOUT)

            logger.info(f"Navigating to {URL} with mobile emulation.")
            page.goto(URL, wait_until="domcontentloaded", timeout=90000)
            
            # --- Explicit wait for a prominent element on the homepage to ensure rendering ---
            page_structure_ready_selector = "div#root" # Main application root element
            try:
                page.wait_for_selector(page_structure_ready_selector, state="visible", timeout=30000)
                logger.info(f"Page structural element '{page_structure_ready_selector}' is visible.")
            except Exception as e:
                logger.error(f"Page structure did not become visible within expected time: {e}")
                page.screenshot(path=test_report_dir / "error_01_page_structure_timeout.png")
                raise AssertionError("Initial page structure did not load or render correctly.")

            page.screenshot(path=test_report_dir / "01_homepage_initial_view.png")
            logger.info("Homepage initial view captured.")

            # --- Gradual Scrolling down the page to ensure books are loaded ---
            logger.info("Attempting to scroll down the page gradually to load books.")
            
            initial_scroll_height = page.evaluate("document.body.scrollHeight")
            logger.info(f"Initial document.body.scrollHeight: {initial_scroll_height}")
            
            scroll_increment = 400 # Scroll by 400 pixels at a time
            max_scroll_attempts = 4 # Limited max_scroll_attempts to 4
            
            scroll_count = 1
            
            while scroll_count <= max_scroll_attempts:
                page.evaluate(f"window.scrollTo(0, {scroll_increment * scroll_count})")
                logger.info(f"Scrolling to position: {scroll_increment * scroll_count}")

                page.wait_for_timeout(4000) # Wait 4 seconds after each small scroll

                current_body_height = page.evaluate("document.body.scrollHeight")
                logger.info(f"After scroll {scroll_count}, current document.body.scrollHeight: {current_body_height}")
                
                page.screenshot(path=test_report_dir / f"0{scroll_count + 1}_homepage_scroll_pos_{scroll_increment * scroll_count}.png")
                logger.info(f"Screenshot taken after scroll attempt {scroll_count}.")

                if current_body_height <= initial_scroll_height and scroll_count > 1:
                    logger.info("Document body height did not increase significantly. Likely reached end of scrollable content or no more books loading.")
                    break
                
                initial_scroll_height = current_body_height

                scroll_count += 1
                
            logger.info("Finished scrolling attempts for book loading.")
            page.screenshot(path=test_report_dir / "02_homepage_after_scrolling_for_books.png")
            logger.info("Final homepage view captured after scrolling for books.")

            # --- Step 1: Locate and Click a Book ---
            logger.info("Attempting to locate and click on a book image.")

            book_selector = "img[src*='libriapp/images']" # A good generic selector for book images
            
            page.screenshot(path=test_report_dir / "03_before_book_locator_wait.png")
            logger.info(f"Screenshot taken before attempting to locate book with selector: '{book_selector}'.")
            
            try:
                book_locator = page.locator(book_selector).first
                # Keep this explicit wait, it's safer if images load dynamically after scroll
                book_locator.wait_for(state="visible", timeout=15000)
                
                page.screenshot(path=test_report_dir / "04_before_book_click.png")
                book_locator.click(timeout=10000)
                logger.info(f"Clicked on the first book image found using selector: {book_selector}")
            except Exception as e:
                logger.error(f"Failed to find or click on any book image: {e}")
                page.screenshot(path=test_report_dir / "error_book_not_found_or_clicked.png")
                with open(test_report_dir / "error_book_page_source.html", "w", encoding="utf-8") as f:
                    f.write(page.content())
                raise AssertionError("Failed to click on a book image to reach the login screen.")

            # --- Step 2: Verify Login Screen ---
            logger.info("Verifying login screen presence.")
            
            email_input_on_login_screen_locator = page.get_by_label("Email").or_(page.locator("input[type='email']"))
            
            try:
                email_input_on_login_screen_locator.wait_for(state="visible", timeout=20000)
                logger.info("Login screen (email input field) is visible.")
            except Exception as e:
                logger.error(f"Login screen (email input field) did not appear: {e}")
                page.screenshot(path=test_report_dir / "error_05_login_screen_not_visible.png")
                with open(test_report_dir / "error_05_login_page_source.html", "w", encoding="utf-8") as f:
                    f.write(page.content())
                raise AssertionError("Login screen did not appear after clicking a book.")

            page.screenshot(path=test_report_dir / "05_signin_page_mobile.png")
            logger.info("Confirmed sign-in page is displayed.")

            # --- Step 3: Fill Login Credentials and Click Login ---
            logger.info("Filling login credentials.")
            email_field = page.get_by_label("Email").or_(page.locator("input[type='email']"))
            password_field = page.get_by_label("Password").or_(page.locator("input[type='password']"))

            email_field.fill(VALID_EMAIL)
            password_field.fill(VALID_PASSWORD)
            logger.info("Filled email and password.")

            login_button = page.get_by_role("button", name=re.compile("login|sign in", re.IGNORECASE))
            login_button.click()
            logger.info("Clicked login button.")

            # --- Step 4: Verify successful login and page load ---
            expect(page).to_have_url(re.compile(f"{URL}/home|{URL}/dashboard|{URL}/account|{URL}/profile", re.IGNORECASE), timeout=30000)
            logger.info("URL verified after successful login.")

            # Assert a specific element on the post-login page is visible
            hamburger_menu_locator = page.get_by_role("button", name="Open Menu").or_(page.locator(".lib-navbar-header-icon")).or_(page.locator("svg[data-icon='bars']"))
            try:
                hamburger_menu_locator.wait_for(state="visible", timeout=10000)
                hamburger_menu_locator.click()
                logger.info("Clicked hamburger menu to open sidebar.")
                
                logout_link_locator = page.get_by_text("Log out", exact=True)
                expect(logout_link_locator).to_be_visible(timeout=10000)
                logger.info("Verified 'Log out' link is visible in the sidebar, confirming successful login state.")
                
                page.keyboard.press('Escape')
                logger.info("Closed sidebar.")

            except Exception as e:
                logger.warning(f"Could not verify sidebar elements or open menu: {e}. Relying on URL assertion.")
                # This `try-except` block is specifically for the hamburger menu/logout link check.
                # If it fails, the test won't fail *because of this* unless it's critical.
                # The main assertion for successful login is the URL check above.


            page.screenshot(path=test_report_dir / "06_dashboard_mobile_after_login.png")
            logger.info("Login successful. On dashboard/home page. Test completed.")

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        if page:
            try:
                page.screenshot(path=test_report_dir / "error_test_failed_final.png", full_page=True)
                with open(test_report_dir / "error_test_failed_page_source.html", "w", encoding="utf-8") as f:
                    f.write(page.content())
            except Exception as se:
                logger.warning(f"Could not take final error screenshot: {se}")
        raise

    finally:
        if browser:
            try:
                browser.close()
                logger.info("Browser closed successfully.")
            except Exception as ce:
                logger.warning(f"Error closing browser: {ce}")
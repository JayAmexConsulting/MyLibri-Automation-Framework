# Save this content as: tests/mobile/test_mobile_login.py

import pytest
import re
import os
import logging
from datetime import datetime
from pathlib import Path
from playwright.sync_api import Page, expect, TimeoutError as PlaywrightTimeoutError

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s:%(lineno)d - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
URL = "https://mylibribooks.com"
SIGNIN_URL = "https://mylibribooks.com/signin"

# --- REQUIRED: Specify the valid email and password directly in the script ---
VALID_EMAIL = "cpot.tea@gmail.com"
VALID_PASSWORD = "Moniwyse!400"

# TARGET_DEVICE_NAME is typically configured in pytest.ini's playwright_device property
# Keeping it here for test report directory naming consistency if it's not dynamically set
TARGET_DEVICE_NAME = 'iPhone 13'

# Define a fixture for mobile context to ensure emulation and headful mode for observation
@pytest.fixture(scope="function")
def mobile_page(playwright, browser_type):
    try:
        iphone_13 = playwright.devices[TARGET_DEVICE_NAME]
    except KeyError:
        logger.warning(f"Device '{TARGET_DEVICE_NAME}' not found in Playwright's built-in devices. Using default mobile settings.")
        iphone_13 = {
            "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 13_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version='13.1.1' Mobile/15E148 Safari/604.1",
            "viewport": {"width": 375, "height": 667},
            "is_mobile": True,
            "has_touch": True,
            "device_scale_factor": 2
        }

    browser_instance = browser_type.launch(headless=False)
    context = browser_instance.new_context(**iphone_13)
    page = context.new_page()
    yield page
    page.close()
    context.close()
    browser_instance.close()


@pytest.mark.mobile
def test_mobile_login_only(mobile_page: Page):
    """
    Tests the mobile login flow for mylibribooks.com by:
    1. Loading the homepage and attempting to scroll to reveal books.
    2. Clicking on the first visible book (image) to trigger the login screen.
    3. Performing login with valid credentials.
    4. Verifying successful login by checking the URL and a post-login element.
    5. Logging out and verifying logout.
    """
    page = mobile_page

    logger.info(f"Using specified valid email: '{VALID_EMAIL}' and valid password.")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    sanitized_device_name = re.sub(r'[^\w\-_\.]', '', TARGET_DEVICE_NAME)
    test_report_dir = Path(f"test_reports/mobile_login_only_{sanitized_device_name}_{timestamp}")
    test_report_dir.mkdir(parents=True, exist_ok=True)

    try:
        logger.info(f"Navigating to {URL} with mobile emulation.")
        page.goto(URL, wait_until="domcontentloaded")
        
        page_structure_ready_selector = "div#root"
        try:
            page.wait_for_selector(page_structure_ready_selector, state="visible", timeout=30000)
            logger.info(f"Page structural element '{page_structure_ready_selector}' is visible.")
        except Exception as e:
            logger.error(f"Page structure did not become visible within expected time: {e}")
            page.screenshot(path=test_report_dir / "error_01_page_structure_timeout.png")
            raise AssertionError("Initial page structure did not load or render correctly.")

        page.screenshot(path=test_report_dir / "01_homepage_initial_view.png")
        logger.info("Homepage initial view captured.")

        # --- REVISED Scrolling down the page to ensure books are loaded ---
        logger.info("Attempting to scroll down the page to load and find books (revising scroll strategy).")
        
        book_selector = "img[src*='libriapp/images']" # Selector for book images
        
        # Determine the middle of the scrollable content or a significant portion down
        initial_scroll_height = page.evaluate("document.body.scrollHeight")
        target_scroll_position = initial_scroll_height / 2
        
        # If the page isn't very tall, scroll a fixed amount (e.g., one viewport height)
        if initial_scroll_height < page.viewport_size['height'] * 1.5:
             target_scroll_position = page.viewport_size['height'] # Scroll by one viewport height

        # Perform the scroll
        logger.info(f"Scrolling to target position: {target_scroll_position} pixels.")
        page.evaluate(f"window.scrollTo(0, {target_scroll_position})")
        page.wait_for_timeout(4000) # Give content time to load after scroll

        # Check if a book is visible after the initial scroll
        try:
            book_locator = page.locator(book_selector).first
            if book_locator.is_visible(timeout=10000): # Allow more time for initial book visibility check
                logger.info("A book image is visible after initial scroll. Proceeding.")
            else:
                raise PlaywrightTimeoutError("Book not visible after initial scroll.")
        except PlaywrightTimeoutError:
            logger.warning("No book found after initial scroll. Attempting further incremental scrolls.")
            # If no book is found after the first scroll attempt, then perform incremental scrolls
            # This handles cases where content loads dynamically further down
            scroll_increment = page.viewport_size['height'] * 0.5 # Scroll by half viewport
            max_additional_scroll_attempts = 5 # Limit further scrolls

            found_book_after_incremental = False
            current_scroll_position = target_scroll_position # Start from where we left off

            for i in range(max_additional_scroll_attempts):
                current_scroll_position += scroll_increment
                logger.info(f"Incremental scroll attempt {i + 1}/{max_additional_scroll_attempts}. New target scroll: {current_scroll_position}")
                
                page.evaluate(f"window.scrollTo(0, {current_scroll_position})")
                page.wait_for_timeout(3000) # Pause after each incremental scroll

                try:
                    if book_locator.is_visible(timeout=5000): # Short timeout for checking visibility
                        logger.info(f"Book found after incremental scroll to position: {current_scroll_position}")
                        found_book_after_incremental = True
                        break
                except PlaywrightTimeoutError:
                    logger.info("No book found visible after this incremental scroll, continuing.")
                    new_body_height = page.evaluate("document.body.scrollHeight")
                    if current_scroll_position >= new_body_height and i > 1: # Stop if we hit bottom
                        logger.info("Reached end of scrollable content without finding more books.")
                        break
            
            if not found_book_after_incremental:
                logger.error("❌ Failed to find any visible book after all scroll attempts.")
                page.screenshot(path=test_report_dir / "error_no_book_found_after_scrolling.png", full_page=True)
                with open(test_report_dir / "error_no_book_page_source.html", "w", encoding="utf-8") as f:
                    f.write(page.content())
                raise AssertionError("No visible book found on homepage after extensive scrolling.")
        
        page.screenshot(path=test_report_dir / "02_homepage_after_scrolling_for_books.png")
        logger.info("Final homepage view captured after scrolling for books.")

        # --- Step 1: Locate and Click a Book ---
        logger.info("Attempting to locate and click on a book image.")
        
        try:
            book_locator = page.locator(book_selector).first
            book_locator.wait_for(state="visible", timeout=10000) # Longer timeout for click target
            
            page.screenshot(path=test_report_dir / "03_before_book_click.png")
            book_locator.click(timeout=10000)
            logger.info(f"Clicked on the first book image found using selector: {book_selector}")
        except Exception as e:
            logger.error(f"Failed to click on the book image after it was supposedly found: {e}")
            page.screenshot(path=test_report_dir / "error_book_not_clicked.png")
            with open(test_report_dir / "error_book_click_page_source.html", "w", encoding="utf-8") as f:
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

        # --- Step 4: Verify successful login and post-login actions ---
        expect(page).to_have_url(f"{URL}/home/dashboard", timeout=30000)
        logger.info("URL verified after successful login: navigated to /home/dashboard.")

        page.screenshot(path=test_report_dir / "06_dashboard_mobile_after_login.png")
        logger.info("Login successful. On dashboard/home page.")

        # --- Step 5: Navigate to Hamburger Menu, Click Profile Dropdown, and Log out ---
        logger.info("Proceeding to navigate to hamburger menu, click profile dropdown, and log out.")
        
        # Hamburger Menu Locator (confirmed: div.toggle-button)
        hamburger_menu_locator = page.locator("div.toggle-button")
        
        try:
            logger.info("Clicking hamburger menu.")
            # Explicit visibility/enabled checks as per the working script for robustness
            expect(hamburger_menu_locator).to_be_visible(timeout=10000)
            expect(hamburger_menu_locator).to_be_enabled(timeout=10000)
            hamburger_menu_locator.click()
            logger.info("Clicked hamburger menu to open main menu.")
            page.wait_for_timeout(1000) # Allow menu animation to complete after click
            page.screenshot(path=test_report_dir / "07_main_menu_opened.png")

            # --- Adopted the robust profile_arrow_locator from your proven working script ---
            profile_arrow_locator = page.locator('div.profile svg').or_(
                                             page.locator('div.profile button[aria-expanded]')).or_(
                                             page.locator('div.profile .arrow-icon'))
            
            logger.info("Ensuring profile dropdown is open to reveal logout link...")
            expect(profile_arrow_locator).to_be_visible(timeout=10000)
            expect(profile_arrow_locator).to_be_enabled(timeout=10000)
            profile_arrow_locator.click()
            logger.info("Clicked profile dropdown arrow.")
            page.wait_for_timeout(1000) # Small pause for dropdown animation
            page.screenshot(path=test_report_dir / "08_profile_dropdown_expanded.png")

            # Click "Log out" link
            log_out_link_locator = page.get_by_text("Log out", exact=True)
            logger.info("Waiting for 'Log out' link to be visible and enabled, then clicking...")
            expect(log_out_link_locator).to_be_visible(timeout=10000)
            expect(log_out_link_locator).to_be_enabled(timeout=10000)
            log_out_link_locator.click()
            logger.info("Clicked 'Log out' link.")
            
            # --- Step 6: Verify successful logout ---
            # After logout, the URL should typically revert to the sign-in page or the homepage
            expect(page).to_have_url(re.compile(f"^{re.escape(URL)}/?$|^{re.escape(SIGNIN_URL)}/?$", re.IGNORECASE), timeout=20000)
            logger.info("Verified successful logout: navigated back to homepage or sign-in page.")
            page.screenshot(path=test_report_dir / "09_after_logout.png")

        except Exception as e:
            logger.error(f"❌ Failed during post-login actions (hamburger/dropdown/logout): {e}")
            page.screenshot(path=test_report_dir / "error_post_login_failed.png", full_page=True)
            with open(test_report_dir / "error_post_login_page_source.html", "w", encoding="utf-8") as f:
                f.write(page.content())
            raise AssertionError("Failed to perform post-login actions (hamburger menu, profile dropdown, or logout).")

        logger.info("Mobile login and logout test completed successfully.")

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        try:
            page.screenshot(path=test_report_dir / "error_test_failed_final.png", full_page=True)
            with open(test_report_dir / "error_test_failed_page_source.html", "w", encoding="utf-8") as f:
                f.write(page.content())
        except Exception as se:
            logger.warning(f"Could not take final error screenshot: {se}")
        raise # Re-raise the exception to make the test officially fail
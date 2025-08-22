# Save this content as: tests/mobile/test_mobile_library_discover.py

import pytest
import re
import logging
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright, expect, Page, TimeoutError as PlaywrightTimeoutError

# Set up logging for this test file
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s:%(lineno)d - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Hardcoded Credentials and URLs ---
VALID_EMAIL = "cpot.tea@gmail.com"
VALID_PASSWORD = "Moniwyse!400"
URL = "https://mylibribooks.com"
LOGIN_URL = f"{URL}/signin"
TARGET_DEVICE_NAME = "iPhone 13"
SEARCH_KEYWORD = "Omojuwa"
# --- END HARDCODED VALUES ---


# Helper function for scrolling and taking screenshots
def scroll_and_screenshot(page: Page, report_dir: Path, prefix: str, total_screenshots: int = 3):
    """
    Scrolls down a page incrementally and takes screenshots.
    """
    initial_scroll_height = page.evaluate("document.body.scrollHeight")
    current_scroll_pos = 0
    
    for i in range(total_screenshots):
        scroll_target = min(initial_scroll_height, current_scroll_pos + (page.viewport_size['height'] * 0.8))
        
        if current_scroll_pos >= initial_scroll_height and i > 0:
            logger.info(f"Stopping scroll for {prefix}: Reached end of content (early break).")
            break

        page.evaluate(f"window.scrollTo(0, {scroll_target})")
        page.wait_for_timeout(1500) # Give time for lazy loading and rendering
        page.screenshot(path=report_dir / f"{prefix}_scroll_{i+1}.png", full_page=True)
        logger.info(f"Screenshot taken: {prefix}_scroll_{i+1}.png at scroll position {scroll_target}.")
        
        current_scroll_pos = page.evaluate("window.scrollY + window.innerHeight")
        initial_scroll_height = page.evaluate("document.body.scrollHeight") # Recalculate as content might have loaded

        if current_scroll_pos >= initial_scroll_height:
            logger.info(f"Stopping scroll for {prefix}: Reached bottom of page after scroll.")
            break


@pytest.mark.mobile
def test_navigate_library_and_explore():
    """
    Tests navigation within the 'My Library' section,
    then navigates to 'Discover', searches for a book,
    and explores author profile and book details.
    This test now performs its own browser setup and login.
    """
    with sync_playwright() as p:
        device_settings = p.devices.get(TARGET_DEVICE_NAME, {
            "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 13_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version='13.1.1' Mobile/15E148 Safari/604.1",
            "viewport": {"width": 375, "height": 667},
            "is_mobile": True,
            "has_touch": True,
            "device_scale_factor": 2
        })

        browser = p.chromium.launch(headless=False)
        context = browser.new_context(**device_settings)
        page = context.new_page()

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sanitized_device_name = re.sub(r'[^\w\-_\.]', '', TARGET_DEVICE_NAME)
        test_report_dir = Path(f"test_reports/mobile_library_discover_test_{sanitized_device_name}_{timestamp}")
        test_report_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Test started on device: {TARGET_DEVICE_NAME} - Navigating Library and Discover pages.")

        try:
            # --- LOGIN STEPS ---
            logger.info(f"Navigating to login page: {LOGIN_URL}")
            page.goto(LOGIN_URL, wait_until="domcontentloaded")
            page.wait_for_timeout(3000)
            page.screenshot(path=test_report_dir / "00_login_page_initial.png")

            logger.info("Performing login with specified credentials.")
            
            email_input = page.locator("input[type='email']")
            password_input = page.locator("input[type='password']")
            login_button = page.locator("button:has-text('Login')")

            expect(email_input).to_be_visible()
            email_input.fill(VALID_EMAIL)
            logger.info("Email filled.")

            expect(password_input).to_be_visible()
            password_input.fill(VALID_PASSWORD)
            logger.info("Password filled.")

            expect(login_button).to_be_visible()
            expect(login_button).to_be_enabled()
            login_button.click()
            logger.info("Login button clicked. Waiting for navigation to dashboard.")

            expect(page).to_have_url(re.compile(f"^{re.escape(URL)}/home/dashboard/?$", re.IGNORECASE), timeout=25000)
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(4000)
            
            hamburger_menu_locator = page.locator("div.toggle-button")
            expect(hamburger_menu_locator).to_be_visible(timeout=15000)
            logger.info("Successfully logged in and dashboard loaded. Hamburger menu is visible.")
            page.screenshot(path=test_report_dir / "01_dashboard_initial_view_after_login.png", full_page=True)
            # --- END LOGIN STEPS ---

            # --- START TEST FLOW ---

            # Step 1: Open Hamburger Menu and navigate to My Library (My Books is a sub-section of My Library)
            logger.info("Opening hamburger menu to navigate to 'My Library'.")
            expect(hamburger_menu_locator).to_be_enabled()
            hamburger_menu_locator.click()
            page.wait_for_timeout(1000)
            page.screenshot(path=test_report_dir / "01a_hamburger_menu_opened.png")

            my_library_link = page.locator("li:has-text('My Library')")
            expect(my_library_link).to_be_visible()
            expect(my_library_link).to_be_enabled()
            my_library_link.click()
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(2000)
            logger.info("Navigated to 'My Library' section. Now on 'My Books' by default.")
            page.screenshot(path=test_report_dir / "01b_my_books_page.png", full_page=True)

            # Scroll down slowly while taking screenshots of the 'My Books' page, scroll back up.
            logger.info("Scrolling down 'My Books' page slowly and taking screenshots.")
            scroll_and_screenshot(page, test_report_dir, "my_books_scroll", total_screenshots=3)
            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(1000)
            logger.info("Scrolled back up on 'My Books' page.")
            
            # 2. Click on My Favourite link (within My Library submenu), scroll through and take screenshots.
            logger.info("Navigating to 'My Favourite' section (within My Library).")
            # These are sub-menu items, so no need to click hamburger again
            my_favourite_link = page.locator("li:has-text('My Favourite')")
            expect(my_favourite_link).to_be_visible()
            expect(my_favourite_link).to_be_enabled()
            my_favourite_link.click()
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(2000)
            page.screenshot(path=test_report_dir / "02_my_favourite_initial_view.png", full_page=True)
            logger.info("Screenshot of 'My Favourite' initial view taken.")
            scroll_and_screenshot(page, test_report_dir, "my_favourite_scroll", total_screenshots=3)
            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(1000)
            logger.info("Scrolled back up on 'My Favourite' page.")

            # 3. Click on My Reading Goals link (within My Library submenu), take screenshot.
            logger.info("Navigating to 'My Reading Goals' section (within My Library).")
            my_reading_goals_link = page.locator("li:has-text('My Reading Goals')")
            expect(my_reading_goals_link).to_be_visible()
            expect(my_reading_goals_link).to_be_enabled()
            my_reading_goals_link.click()
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(2000)
            page.screenshot(path=test_report_dir / "03_my_reading_goals.png", full_page=True)
            logger.info("Screenshot of 'My Reading Goals' page taken.")

            # 4. Click on My Wishlist link (within My Library submenu), take screenshot.
            logger.info("Navigating to 'My Wishlist' section (within My Library).")
            my_wishlist_link = page.locator("li:has-text('My Wishlist')")
            expect(my_wishlist_link).to_be_visible()
            expect(my_wishlist_link).to_be_enabled()
            my_wishlist_link.click()
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(2000)
            page.screenshot(path=test_report_dir / "04_my_wishlist.png", full_page=True)
            logger.info("Screenshot of 'My Wishlist' page taken.")

            # Now, go back to the top-level hamburger menu to select "Discover" or access the search.
            logger.info("Re-opening hamburger menu to navigate to 'Discover'.")
            expect(hamburger_menu_locator).to_be_visible()
            hamburger_menu_locator.click()
            page.wait_for_timeout(1000)
            page.screenshot(path=test_report_dir / "04a_menu_reopened_for_discover.png")

            # 5. Navigate to the discover page (click on the Discover link).
            # Scroll through the page and take screenshots, then scroll back up.
            logger.info("Navigating to 'Discover' page from hamburger menu.")
            discover_link = page.locator("li:has-text('Discover')")
            expect(discover_link).to_be_visible()
            expect(discover_link).to_be_enabled()
            discover_link.click()
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(2000)
            logger.info("Landed on 'Discover' page.")
            page.screenshot(path=test_report_dir / "05_discover_initial_view.png", full_page=True)
            logger.info("Screenshot of 'Discover' initial view taken.")
            scroll_and_screenshot(page, test_report_dir, "discover_scroll", total_screenshots=3)
            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(1000)
            logger.info("Scrolled back up on 'Discover' page.")

            # 6. Search for a book using the search field within the hamburger menu.
            logger.info(f"Re-opening hamburger menu to access search field for keyword: '{SEARCH_KEYWORD}'.")
            expect(hamburger_menu_locator).to_be_visible()
            hamburger_menu_locator.click()
            page.wait_for_timeout(1000)
            page.screenshot(path=test_report_dir / "05a_menu_reopened_for_search.png")

            search_field = page.locator("input[placeholder='Book,Genre,Author']")
            search_button = page.locator("button:has-text('Search')")
            
            expect(search_field).to_be_visible(timeout=15000)
            expect(search_field).to_be_editable()
            
            logger.info("Search field found and is visible. Setting focus.")
            search_field.focus()
            page.wait_for_timeout(500)

            logger.info(f"Filling search field with keyword: '{SEARCH_KEYWORD}'.")
            search_field.fill(SEARCH_KEYWORD)
            
            expect(search_button).to_be_visible()
            expect(search_button).to_be_enabled()
            search_button.click()
            
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(3000)
            page.screenshot(path=test_report_dir / "06_search_results_initial_view.png", full_page=True)
            logger.info(f"Screenshot of search results for '{SEARCH_KEYWORD}' taken.")
            scroll_and_screenshot(page, test_report_dir, "search_results_scroll", total_screenshots=3)
            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(1000)
            logger.info("Scrolled back up on search results page.")

            # 7. Click on the author's image to expand the author's profile
            logger.info("Clicking on author's image to view profile.")
            
            author_image_locator = page.locator("div.author-gallery-box img").first
            
            expect(author_image_locator).to_be_visible()
            expect(author_image_locator).to_be_enabled()
            author_image_locator.click()
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(3000)
            page.screenshot(path=test_report_dir / "07_author_profile_initial_view.png", full_page=True)
            logger.info("Screenshot of author's profile initial view taken.")
            
            # Scroll down to reveal the book on the author's profile page
            logger.info("Scrolling down author's profile page to reveal book(s).")
            scroll_and_screenshot(page, test_report_dir, "author_profile_book_scroll", total_screenshots=2)
            
            # 8. Click on the author's book displayed on the page and take screenshot.
            logger.info("Clicking on an author's book on their profile page.")
            author_book_on_profile_locator = page.locator("div.lib-gallery-box img").first
            
            expect(author_book_on_profile_locator).to_be_visible()
            expect(author_book_on_profile_locator).to_be_enabled()
            author_book_on_profile_locator.click()
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(3000)
            page.screenshot(path=test_report_dir / "08_book_detail_page.png", full_page=True)
            logger.info("Screenshot of book detail page taken. Test End.")

        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            if 'page' in locals() and page:
                try:
                    page.screenshot(path=test_report_dir / "error_test_failed.png", full_page=True)
                    with open(test_report_dir / "error_page_source.html", "w", encoding="utf-8") as f:
                        f.write(page.content())
                except Exception as se:
                    logger.warning(f"Could not take final error screenshot/page source: {se}")
            raise

        finally:
            # Ensure context and browser are closed.
            # Closing the context generally also cleans up its associated pages.
            # If the browser was launched for this single context, closing the context
            # often results in the browser closing as well.
            if 'context' in locals() and context:
                try:
                    # Closing the context is usually sufficient and safer than checking browser.is_closed()
                    context.close()
                    logger.info("Browser context closed successfully.")
                except Exception as close_e:
                    logger.warning(f"Error closing browser context: {close_e}")
            
            # Optionally, explicitly close the browser if it wasn't already implicitly closed.
            # This is safer without browser.is_closed()
            if 'browser' in locals() and browser:
                try:
                    # Attempt to close the browser, but it might already be closed by context.close()
                    # Playwright handles this gracefully in most cases, but we log any error.
                    browser.close()
                    logger.info("Browser closed successfully (if not already by context).")
                except Exception as close_e:
                    logger.warning(f"Error closing browser: {close_e}. It might have been implicitly closed by context.close().")
            
            logger.info("Cleanup process finished for browser and context.")
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
EMAIL = "cpot.tea@gmail.com"
PASSWORD = "Moniwyse!400"
TIMEOUT = 30000  # Default timeout in milliseconds

@pytest.mark.mobile
def test_mobile_login_logout_flow_workaround():
    """
    Tests the mobile login and logout flow for mylibribooks.com,
    by clicking on a book to trigger the login screen as a workaround.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_report_dir = Path(f"test_reports/mobile_login_logout_flow_workaround_{timestamp}")
    test_report_dir.mkdir(parents=True, exist_ok=True)

    browser = None
    page = None

    try:
        with sync_playwright() as p:
            # --- Mobile Context Configuration ---
            browser_type_name = p.chromium.name
            browser = p.chromium.launch(headless=False, slow_mo=500) # Keep headless=False for visual debugging
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
            # --- CHANGE 1: Use 'load' for goto, which waits for basic resources ---
            page.goto(URL, wait_until="load", timeout=60000)
            
            # --- CHANGE 2: Explicitly wait for a key content area to be visible ---
            # Based on image_56884e.png, the books are inside 'div.lib-homepage-container-items'.
            # Or you can wait for the main 'div#root' or 'div.lib-navbar'.
            page_content_ready_selector = "div.lib-homepage-container-items" 
            try:
                page.wait_for_selector(page_content_ready_selector, state="visible", timeout=30000) # Wait up to 30s for this
                logger.info(f"Page content loaded and '{page_content_ready_selector}' is visible.")
            except Exception as e:
                logger.error(f"Page content did not become visible within expected time: {e}")
                page.screenshot(path=test_report_dir / "error_page_content_timeout.png")
                raise AssertionError("Initial page content did not load or render correctly.")

            page.screenshot(path=test_report_dir / "01_home_mobile.png")
            logger.info("Homepage loaded and confirmed visually.")

            # --- Step 1: Find and click on a book ---
            logger.info("Attempting to scroll down and click on a book.")
            
            # Scroll down the page to reveal books. Adjust scroll amount if needed.
            # Using evaluate to scroll by pixels. Increased wait_for_timeout after scroll.
            page.evaluate("window.scrollTo(0, document.body.scrollHeight/3)") 
            page.wait_for_timeout(2000) # Give more time
            page.evaluate("window.scrollTo(0, document.body.scrollHeight/2)") 
            page.wait_for_timeout(2000) 
            page.evaluate("window.scrollTo(0, document.body.scrollHeight * 2/3)")
            page.wait_for_timeout(2000)
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(3000) # Give even more time after final scroll for lazy loading

            page.screenshot(path=test_report_dir / "02_scrolled_to_books.png")
            logger.info("Scrolled down the page.")

            # --- REFINED BOOK SELECTOR BASED ON image_56884e.png ---
            book_selectors = [
                "div.lib-book-gallery-item", # Most accurate from your screenshot
                # Fallbacks
                "a[href*='/book/']",
                ".book-card",
                ".product-item",
                "img[alt*='book']",
                "div[class*='book-preview']",
                "div:has(h3.book-title)",
            ]

            book_clicked = False
            for selector in book_selectors:
                try:
                    locator = page.locator(selector).first # Get the first one found
                    locator.wait_for(state="visible", timeout=10000)
                    locator.wait_for(state="enabled", timeout=5000)
                    locator.wait_for(state="stable", timeout=5000)
                    
                    # Take screenshot before clicking each book candidate for debugging
                    sanitized_selector = re.sub(r'[^\w\-_\.]', '', str(selector)[:50])
                    page.screenshot(path=test_report_dir / f"02_before_book_click_{sanitized_selector}_{browser_type_name}.png")
                    
                    locator.click(timeout=10000)
                    logger.info(f"Clicked on a book using selector: {selector}")
                    book_clicked = True
                    break
                except Exception as e:
                    logger.debug(f"Book selector '{selector}' failed: {e}. Trying next...")
                    continue
            
            if not book_clicked:
                logger.error("Failed to find and click on any book after scrolling.")
                page.screenshot(path=test_report_dir / f"error_book_not_found_or_clicked_{browser_type_name}.png")
                with open(test_report_dir / f"error_book_page_source_{browser_type_name}.html", "w", encoding="utf-8") as f:
                    f.write(page.content())
                raise AssertionError("Failed to click on a book to reach the login screen.")

            # --- Step 2: Verify Login Screen ---
            logger.info("Verifying login screen presence.")
            
            login_form_locator = page.get_by_label("Email").or_(
                                 page.locator("input[type='email']")).or_(
                                 page.get_by_role("button", name=re.compile("login|sign in", re.IGNORECASE)))
            
            try:
                login_form_locator.wait_for(state="visible", timeout=20000)
                logger.info("Login screen (email/password fields or login button) is visible.")
            except Exception as e:
                logger.error(f"Login screen (email/password fields/button) did not appear: {e}")
                page.screenshot(path=test_report_dir / f"error_login_screen_not_visible_{browser_type_name}.png")
                with open(test_report_dir / f"error_login_page_source_{browser_type_name}.html", "w", encoding="utf-8") as f:
                    f.write(page.content())
                raise AssertionError("Login screen did not appear after clicking a book.")

            page.screenshot(path=test_report_dir / "03_signin_page_mobile.png")
            logger.info("Confirmed sign-in page is displayed.")

            logger.info("Filling login credentials.")
            email_field = page.get_by_label("Email").or_(page.locator("input[type='email']"))
            password_field = page.get_by_label("Password").or_(page.locator("input[type='password']"))

            email_field.wait_for(state="visible", timeout=10000)
            password_field.wait_for(state="visible", timeout=10000)
            
            email_field.fill(EMAIL)
            password_field.fill(PASSWORD)

            login_button = page.get_by_role("button", name=re.compile("login|sign in", re.IGNORECASE))
            login_button.wait_for(state="visible", timeout=10000)
            login_button.click()

            expect(page).to_have_url(re.compile("home|dashboard|account|profile", re.IGNORECASE), timeout=20000)
            page.wait_for_timeout(3000)
            page.screenshot(path=test_report_dir / "04_dashboard_mobile.png")
            logger.info("Login successful. On dashboard/home page.")

            # --- Step 3: Profile (Mobile specific way) ---
            logger.info("Attempting to navigate to profile.")

            profile_link_locator = page.get_by_text("Tea Pot", exact=True)

            try:
                profile_link_locator.wait_for(state="visible", timeout=10000)
                profile_link_locator.wait_for(state="enabled", timeout=5000)
                profile_link_locator.wait_for(state="stable", timeout=5000)
                profile_link_locator.click()
                logger.info("Clicked 'Tea Pot' profile link.")
            except Exception as e:
                logger.error(f"Failed to find 'Tea Pot' profile link after login: {e}")
                page.screenshot(path=test_report_dir / f"error_profile_link_not_found_{browser_type_name}.png")
                raise AssertionError("Could not find 'Tea Pot' profile link after login.")

            expect(page).to_have_url(re.compile("profile", re.IGNORECASE), timeout=15000)
            page.screenshot(path=test_report_dir / "05_profile_mobile.png")
            logger.info("Navigated to profile page.")

            # --- Step 4: Log out (Mobile specific way) ---
            logger.info("Attempting to log out.")

            log_out_locator = page.get_by_text("Log Out", exact=True)

            try:
                log_out_locator.wait_for(state="visible", timeout=10000)
                log_out_locator.wait_for(state="enabled", timeout=5000)
                log_out_locator.wait_for(state="stable", timeout=5000)
                log_out_locator.click()
                logger.info("Clicked 'Log Out' link.")
            except Exception as e:
                logger.error(f"Failed to find 'Log Out' link after login: {e}")
                page.screenshot(path=test_report_dir / f"error_logout_link_not_found_{browser_type_name}.png")
                raise AssertionError("Could not find 'Log Out' link after login.")

            expect(page).to_have_url(URL, timeout=10000)
            page.screenshot(path=test_report_dir / "06_logged_out_mobile.png")
            logger.info("Successfully logged out.")

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        if page:
            try:
                page.screenshot(path=test_report_dir / "error_mobile.png")
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
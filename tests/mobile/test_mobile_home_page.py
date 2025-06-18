import pytest
from playwright.sync_api import sync_playwright, expect
from pathlib import Path
from datetime import datetime
import logging
import time

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(name)s:%(lineno)d - %(message)s')
logger = logging.getLogger(__name__)

# Constants
URL = "https://mylibribooks.com"
TIMEOUT = 45000 # Overall timeout for page operations

@pytest.mark.mobile
def test_mobile_homepage_scroll_gradual():
    """
    Loads the mobile homepage of mylibribooks.com, scrolls down gradually
    to capture multiple intermediate screenshots.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_report_dir = Path(f"test_reports/mobile_homepage_scroll_gradual_{timestamp}")
    test_report_dir.mkdir(parents=True, exist_ok=True)

    browser = None
    page = None

    try:
        with sync_playwright() as p:
            # --- Mobile Context Configuration ---
            browser_type_name = p.chromium.name
            browser = p.chromium.launch(headless=False, slow_mo=700) # Keep slow_mo high for overall observation
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
            page.goto(URL, wait_until="load", timeout=90000)
            
            # --- Explicit wait for a prominent element on the homepage to ensure rendering ---
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

            # --- Gradual Scrolling down the page ---
            logger.info("Attempting to scroll down the page gradually.")
            
            initial_scroll_height = page.evaluate("document.body.scrollHeight")
            logger.info(f"Initial document.body.scrollHeight: {initial_scroll_height}")
            
            scroll_position = 0
            scroll_increment = 400 # Scroll by 400 pixels at a time (adjust as needed)
            max_scroll_attempts = 20 # Increased max attempts for gradual scrolling
            
            scroll_count = 1

            while scroll_position < initial_scroll_height or scroll_count <= max_scroll_attempts:
                # Scroll by the increment
                scroll_position += scroll_increment
                
                # Ensure we don't scroll beyond the current document.body.scrollHeight
                # This is important as initial_scroll_height might change if new content loads.
                page.evaluate(f"window.scrollTo(0, {scroll_position})") 
                
                logger.info(f"Scrolling to position: {scroll_position}")

                # Wait for content to potentially load after each small scroll
                page.wait_for_timeout(3000) # Wait 3 seconds after each small scroll

                current_body_height = page.evaluate("document.body.scrollHeight")
                logger.info(f"After scroll {scroll_count}, current document.body.scrollHeight: {current_body_height}")
                
                page.screenshot(path=test_report_dir / f"0{scroll_count + 1}_homepage_scroll_pos_{scroll_position}.png")
                logger.info(f"Screenshot taken after scroll attempt {scroll_count}.")

                # Update initial_scroll_height in case new content lazy-loaded and expanded the page
                if current_body_height > initial_scroll_height:
                    initial_scroll_height = current_body_height
                    logger.info(f"Document body height increased to {initial_scroll_height}. More content loaded.")

                # Break if we've scrolled past the current total height, meaning we're at the bottom
                if scroll_position >= initial_scroll_height:
                    logger.info("Reached the bottom of the current scrollable content.")
                    break
                
                scroll_count += 1
                
            logger.info("Finished gradual scrolling attempts.")
            page.screenshot(path=test_report_dir / "final_homepage_after_gradual_scrolls.png")
            logger.info("Final homepage view captured after all scrolls.")

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        if page:
            try:
                page.screenshot(path=test_report_dir / "error_test_failed_final.png")
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
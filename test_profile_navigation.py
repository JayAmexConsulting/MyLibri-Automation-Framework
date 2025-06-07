from playwright.sync_api import sync_playwright, expect
import pytest
import logging
import re

URL = "https://mylibribooks.com"
EMAIL = "cpot.tea@gmail.com"
PASSWORD = "Moniwyse!400"

def test_login_and_navigate_through_profile_sections():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=500)
        page = browser.new_page()
        
        try:
            # Step 1: Navigate to homepage
            logging.info("STEP 1: Navigating to homepage")
            page.goto(URL)
            expect(page).to_have_url(re.compile(r"https://mylibribooks.com/?$"))
            logging.info("✓ Homepage loaded successfully")

            # Step 2: Click Sign In (with more robust URL check)
            logging.info("STEP 2: Clicking Sign In")
            page.click("text=Sign In")
            expect(page).to_have_url(re.compile(r"https://mylibribooks.com/signin/?$"))
            logging.info("✓ Sign In page loaded successfully")

            # Step 3: Fill login form
            logging.info("STEP 3: Filling login form")
            page.fill("input[type='email']", EMAIL)
            page.fill("input[type='password']", PASSWORD)
            logging.info("✓ Login form filled")

            # Step 4: Submit login (with more robust URL check)
            logging.info("STEP 4: Submitting login")
            page.click("button:has-text('Login')")
            logging.info("✓ Login successful")
            
            # STEP 5: Navigate to profile (updated selector)
            logging.info("STEP 5: Navigating to profile")
            profile_menu = page.locator(".profile_pic, img[alt*='Profile'], [data-testid='profile-menu']").first
            
            # STEP 5: Verify dashboard loaded
            logging.info("STEP 5: Verifying dashboard")
            expect(page).to_have_url(re.compile(r"https://mylibribooks.com/home/dashboard/?$"))
            capture_screenshot(page, "05 Dashboard Loaded")
            
            # STEP 6: Navigate to Wallet section (with multiple selector options)
            logging.info("STEP 6: Checking Wallet section")
            wallet_link = page.locator(
                "text=Wallet, " +
                "[href*='/wallet'], " +
                "[data-testid='wallet-link'], " +
                ".wallet-menu-item"
            ).first
            expect(wallet_link).to_be_visible()
            
            with page.expect_navigation():
                wallet_link.click()
            expect(page).to_have_url(re.compile(r"https://mylibribooks.com/home/wallet/?$"))
            expect(page.get_by_text("Wallet Balance")).to_be_visible()
            capture_screenshot(page, "06 Wallet Section")
            
            # Continue with remaining steps...
            
        except Exception as e:
            capture_screenshot(page, "ERROR Failed Step")
            logging.error(f"TEST FAILED: {str(e)}")
            raise
        finally: 
            context.close()
            browser.close ()
            
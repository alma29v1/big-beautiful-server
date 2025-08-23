"""Service for checking AT&T fiber availability."""

from typing import Dict
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, SessionNotCreatedException
from selenium.webdriver.common.keys import Keys
import time
import random
import os
import logging

logger = logging.getLogger(__name__)

# List of user agents to rotate
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0"
]

class ATTService:
    """Service for checking AT&T fiber availability using Selenium."""
    
    def __init__(self):
        """Initialize the service."""
        self.driver = None
        self.wait = None
        
    def setup_driver(self):
        """Set up the Chrome WebDriver with anti-detection measures."""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
                
        options = uc.ChromeOptions()
        options.add_argument("--no-proxy-server")
        options.add_argument("--disable-blink-features=AutomationControlled")
        
        # Rotate user agent
        user_agent = random.choice(USER_AGENTS)
        options.add_argument(f"user-agent={user_agent}")
        
        # Set up Chrome profile
        user_data_dir = os.path.join(os.getcwd(), f"chrome_profile_{random.randint(1000, 9999)}")
        options.add_argument(f"--user-data-dir={user_data_dir}")
        
        logger.info("Starting browser...")
        try:
            self.driver = uc.Chrome(options=options, version_main=135)
            self.driver.set_page_load_timeout(60)
            self.wait = WebDriverWait(self.driver, 90)
            time.sleep(random.uniform(1, 3))
            return user_data_dir
        except SessionNotCreatedException as e:
            logger.error(f"Failed to create session: {e}")
            raise
        
    def type_like_human(self, element, text):
        """Simulate human-like typing into a field."""
        # Clear the field first
        element.clear()
        time.sleep(random.uniform(0.1, 0.3))
        
        # Use JavaScript to clear any remaining text
        self.driver.execute_script("arguments[0].value = '';", element)
        time.sleep(random.uniform(0.1, 0.3))
        
        # Type each character with random delays
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.2))
            
        # Add a small delay after typing
        time.sleep(random.uniform(0.3, 0.7))
            
    def ensure_page_ready(self, address):
        """Ensure the AT&T page is loaded and ready."""
        target_url = "https://www.att.com/buy/internet/plans"
        try:
            self.driver.get(target_url)
            # Force a page refresh to handle potential session issues
            self.driver.refresh()
            # Random delay to mimic human behavior
            time.sleep(random.uniform(10, 20))
            
            # Check for redirects
            current_url = self.driver.current_url
            if "att.com/buy/internet/plans" not in current_url:
                if "not-available" in current_url:
                    logger.info(f"Address {address} indicates AT&T Fiber not available.")
                    return False, "AT&T Fiber not available at this address", False
                raise WebDriverException(f"Unexpected redirect to {current_url}")
                
            # Wait for input field with increased timeout
            self.wait.until(EC.element_to_be_clickable((By.ID, "input-addressInput")))
            return True, None, None
            
        except (TimeoutException, WebDriverException) as e:
            logger.error(f"Page load failed: {e}")
            return False, "Failed to load page - assumed no fiber", False
            
    def check_fiber_availability(self, address: str) -> Dict:
        """Check if AT&T fiber is available at an address.
        
        Args:
            address: Full street address to check
            
        Returns:
            Dict containing availability info
        """
        if not self.driver:
            self.setup_driver()
            
        try:
            # Ensure the page is ready
            page_ready, result, has_fiber = self.ensure_page_ready(address)
            if not page_ready:
                return {
                    'address': address,
                    'has_fiber': has_fiber,
                    'result': result
                }

            # Wait for input field and type like a human
            input_field = self.wait.until(EC.element_to_be_clickable((By.ID, "input-addressInput")))
            time.sleep(random.uniform(0.5, 1.5))
            
            # Type the address and wait for validation
            self.type_like_human(input_field, address)
            
            # Press Enter to trigger address validation
            input_field.send_keys(Keys.RETURN)
            time.sleep(random.uniform(1, 2))

            # Click the check button if it exists
            try:
                check_button = self.wait.until(EC.element_to_be_clickable((By.ID, "Check-availability-btn-7107")))
                self.driver.execute_script("arguments[0].click();", check_button)
                time.sleep(random.uniform(5, 7))
            except:
                # Button might not be needed if Enter key triggered the check
                pass

            # Extract result with multiple selectors
            try:
                result_elements = self.wait.until(lambda d: (
                    d.find_elements(By.CSS_SELECTOR, "h2.mar-b-xs.heading-md.color-gray-800") or
                    d.find_elements(By.ID, "ckavResult") or
                    d.find_elements(By.CSS_SELECTOR, "div.text-center div.type-lg.rte-styles") or
                    d.find_elements(By.XPATH, '//p[contains(@class, "mar-t-2 type-base color-gray-800") and contains(text(), "We found an existing AT&T account at this address.")]') or
                    d.find_elements(By.CSS_SELECTOR, "div.result-message") or
                    d.find_elements(By.XPATH, '//div[contains(text(), "available at")]')
                ))
                
                result = result_elements[0].text.strip() if result_elements else ""
                if not result:
                    logger.warning("Result is empty, assuming no fiber available. Saving page source for debugging...")
                    with open(f"empty_result_{address.replace(' ', '_')}.html", "w", encoding="utf-8") as f:
                        f.write(self.driver.page_source)
                    has_fiber = False
                else:
                    has_fiber = "available at" in result.lower() and "Sign up to be notified" not in result and "may be available" not in result.lower()
                logger.info(f"Result: {result}")
                
                return {
                    'address': address,
                    'has_fiber': has_fiber,
                    'result': result
                }

            except (TimeoutException, WebDriverException) as e:
                logger.error(f"Error extracting result: {e}")
                self.driver.save_screenshot(f"screenshot_{address.replace(' ', '_')}.png")
                with open(f"page_source_{address.replace(' ', '_')}.html", "w", encoding="utf-8") as f:
                    f.write(self.driver.page_source)
                return {
                    'address': address,
                    'has_fiber': False,
                    'result': f"Error: {str(e)}"
                }

        except Exception as e:
            logger.error(f"Error checking AT&T availability for {address}: {str(e)}")
            return {
                'address': address,
                'has_fiber': False,
                'result': f"Error: {str(e)}"
            }
            
    def __del__(self):
        """Clean up resources."""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass 
import time
import random
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import logging

logger = logging.getLogger(__name__)

class ATTFiberChecker:
    def __init__(self, driver=None):
        self.driver = driver
        self.target_url = "https://www.att.com/buy/internet/plans"

    def check_fiber_availability(self, address: str) -> bool:
        """Check if AT&T Fiber is available at the given address."""
        if not self.driver:
            raise Exception("No driver instance provided")

        wait = WebDriverWait(self.driver, 20)
        try:
            # Navigate to the AT&T plans page
            self.driver.get(self.target_url)
            self.driver.refresh()
            time.sleep(random.uniform(10, 20))
            current_url = self.driver.current_url
            if "att.com/buy/internet/plans" not in current_url:
                if "not-available" in current_url:
                    return False
                raise WebDriverException(f"Unexpected redirect to {current_url}")
            
            # Wait for and fill in the address field
            input_field = wait.until(EC.element_to_be_clickable((By.ID, "input-addressInput")))
            time.sleep(random.uniform(0.5, 1.5))
            input_field.clear()
            if input_field.get_attribute("value"):
                self.driver.execute_script("arguments[0].value = '';", input_field)
            
            # Type address like a human
            for char in address:
                input_field.send_keys(char)
                time.sleep(random.uniform(0.05, 0.2))
            
            self.driver.execute_script("window.scrollBy(0, 200);")
            time.sleep(random.uniform(1, 2))
            
            check_button = wait.until(EC.element_to_be_clickable((By.ID, "Check-availability-btn-7107")))
            self.driver.execute_script("arguments[0].click();", check_button)
            time.sleep(random.uniform(5, 7))
            
            # Check for various result elements with expanded selectors
            result_elements = wait.until(lambda d: (
                d.find_elements(By.CSS_SELECTOR, "h2.mar-b-xs.heading-md.color-gray-800") or
                d.find_elements(By.ID, "ckavResult") or
                d.find_elements(By.CSS_SELECTOR, "div.text-center div.type-lg.rte-styles") or
                d.find_elements(By.XPATH, '//p[contains(@class, "mar-t-2 type-base color-gray-800") and contains(text(), "We found an existing AT&T account at this address.")]') or
                d.find_elements(By.CSS_SELECTOR, "div.result-message") or
                d.find_elements(By.XPATH, '//div[contains(text(), "available at")]') or
                # Additional selectors for fiber availability
                d.find_elements(By.XPATH, '//div[contains(text(), "Fiber") or contains(text(), "fiber")]') or
                d.find_elements(By.CSS_SELECTOR, "div[class*='plan'], div[class*='offer'], div[class*='product']") or
                d.find_elements(By.XPATH, '//button[contains(text(), "Order") or contains(text(), "Select")]') or
                d.find_elements(By.CSS_SELECTOR, "div.price, span.price, .pricing") or
                d.find_elements(By.XPATH, '//div[contains(text(), "Mbps") or contains(text(), "Gig")]')
            ))
            
            # Get all text content from the page for comprehensive analysis
            page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
            result_text = result_elements[0].text.strip().lower() if result_elements else ""
            
            # Log the response for debugging
            logger.info(f"AT&T Response for {address}: {result_text[:200]}...")
            print(f"[DEBUG] AT&T Response for {address}: {result_text[:200]}...")
            
            # Enhanced fiber detection logic
            has_fiber = self._analyze_fiber_availability(page_text, result_text, address)
            
            return has_fiber
            
        except Exception as e:
            print(f"Error checking fiber availability for {address}: {str(e)}")
            logger.error(f"Error checking fiber availability for {address}: {str(e)}")
            return False
    
    def _analyze_fiber_availability(self, page_text: str, result_text: str, address: str) -> bool:
        """Analyze the page content to determine fiber availability with improved logic."""
        
        # Definitive NO indicators (return False immediately)
        no_indicators = [
            "not available",
            "no service available", 
            "outside our service area",
            "sign up to be notified",
            "may be available in the future",
            "check back later",
            "coming soon",
            "not currently available"
        ]
        
        for indicator in no_indicators:
            if indicator in page_text or indicator in result_text:
                print(f"[DEBUG] Found NO indicator for {address}: {indicator}")
                return False
        
        # Definitive YES indicators (return True immediately)
        yes_indicators = [
            "available at",
            "fiber available",
            "at&t fiber",
            "internet plans available",
            "select plan",
            "order now",
            "add to cart",
            "choose plan",
            "monthly price",
            "per month",
            "/mo",
            "mbps",
            "gig internet",
            "fiber internet",
            "high-speed internet available"
        ]
        
        for indicator in yes_indicators:
            if indicator in page_text or indicator in result_text:
                print(f"[DEBUG] Found YES indicator for {address}: {indicator}")
                return True
        
        # Check for pricing information (strong indicator of availability)
        pricing_indicators = ["$", "price", "cost", "monthly", "/month", "per mo"]
        pricing_count = sum(1 for indicator in pricing_indicators if indicator in page_text)
        if pricing_count >= 2:
            print(f"[DEBUG] Found pricing information for {address} - likely available")
            return True
        
        # Check for plan/product information
        plan_indicators = ["plan", "package", "speed", "download", "upload", "unlimited"]
        plan_count = sum(1 for indicator in plan_indicators if indicator in page_text)
        if plan_count >= 3:
            print(f"[DEBUG] Found plan information for {address} - likely available")
            return True
        
        # If we get here, it's unclear - default to False but log for review
        print(f"[DEBUG] Unclear response for {address} - defaulting to NO FIBER")
        logger.warning(f"Unclear AT&T response for {address}: {result_text[:100]}...")
        
        return False 
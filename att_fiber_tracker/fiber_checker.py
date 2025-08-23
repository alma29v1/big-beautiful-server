"""Main script for checking AT&T fiber availability and processing contact information."""

import pandas as pd
from typing import List, Dict
import os
import time
import random
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, SessionNotCreatedException
from .services.api_service import ATTService
from .services.bach_service import BachService
from .services.mailchimp_service import MailchimpService
# from .redfin_parser import download_redfin_data, USER_AGENTS

def setup_driver():
    """Initialize Selenium driver with anti-detection measures."""
    options = uc.ChromeOptions()
    options.add_argument("--no-proxy-server")
    options.add_argument("--disable-blink-features=AutomationControlled")
    # Rotate user agent
    user_agent = random.choice(USER_AGENTS)
    options.add_argument(f"user-agent={user_agent}")
    
    # Set up Chrome profile
    user_data_dir = os.path.join(os.getcwd(), f"chrome_profile_{random.randint(1000, 9999)}")
    options.add_argument(f"--user-data-dir={user_data_dir}")
    
    print("Starting browser...")
    try:
        driver = uc.Chrome(options=options)
        driver.set_page_load_timeout(60)
        time.sleep(random.uniform(1, 3))
        return driver, user_data_dir
    except SessionNotCreatedException as e:
        print(f"Failed to create session: {e}")
        raise

def type_like_human(element, text):
    """Simulate human-like typing into a field."""
    element.clear()
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(0.05, 0.2))

def ensure_page_ready(driver, wait, address):
    """Ensure the AT&T page is loaded and ready."""
    target_url = "https://www.att.com/buy/internet/plans"
    try:
        driver.get(target_url)
        # Force a page refresh to handle potential session issues
        driver.refresh()
        # Random delay to mimic human behavior
        time.sleep(random.uniform(10, 20))
        
        # Check for redirects
        current_url = driver.current_url
        if "att.com/buy/internet/plans" not in current_url:
            if "not-available" in current_url:
                print(f"Address {address} indicates AT&T Fiber not available.")
                return False, "AT&T Fiber not available at this address", False
            raise WebDriverException(f"Unexpected redirect to {current_url}")
            
        # Wait for input field with increased timeout
        input_field = wait.until(EC.element_to_be_clickable((By.ID, "input-addressInput")))
        return True, None, None
        
    except (TimeoutException, WebDriverException) as e:
        print(f"Page load failed: {e}")
        return False, "Failed to load page - assumed no fiber", False

def check_fiber_availability(driver, address, wait, max_attempts=3):
    """Check AT&T fiber availability for an address."""
    for attempt in range(max_attempts):
        print(f"Checking {address} (Attempt {attempt + 1}/{max_attempts})")
        try:
            # Ensure the page is ready
            page_ready, result, has_fiber = ensure_page_ready(driver, wait, address)
            if not page_ready:
                return {"Address": address, "Result": result}, has_fiber

            # Wait for input field and type like a human
            input_field = wait.until(EC.element_to_be_clickable((By.ID, "input-addressInput")))
            time.sleep(random.uniform(0.5, 1.5))
            input_field.clear()
            if input_field.get_attribute("value"):
                driver.execute_script("arguments[0].value = '';", input_field)
            type_like_human(input_field, address)

            # Simulate mouse movement
            driver.execute_script("window.scrollBy(0, 200);")
            time.sleep(random.uniform(1, 2))

            # Click the check button
            check_button = wait.until(EC.element_to_be_clickable((By.ID, "Check-availability-btn-7107")))
            driver.execute_script("arguments[0].click();", check_button)
            time.sleep(random.uniform(5, 7))

            # Extract result with multiple selectors
            try:
                result_elements = wait.until(lambda d: (
                    d.find_elements(By.CSS_SELECTOR, "h2.mar-b-xs.heading-md.color-gray-800") or
                    d.find_elements(By.ID, "ckavResult") or
                    d.find_elements(By.CSS_SELECTOR, "div.text-center div.type-lg.rte-styles") or
                    d.find_elements(By.XPATH, '//p[contains(@class, "mar-t-2 type-base color-gray-800") and contains(text(), "We found an existing AT&T account at this address.")]') or
                    d.find_elements(By.CSS_SELECTOR, "div.result-message") or
                    d.find_elements(By.XPATH, '//div[contains(text(), "available at")]')
                ))
                
                result = result_elements[0].text.strip() if result_elements else ""
                if not result:
                    print("Result is empty, assuming no fiber available.")
                    has_fiber = False
                else:
                    has_fiber = "available at" in result.lower() and "Sign up to be notified" not in result and "may be available" not in result.lower()
                print(f"Result: {result}")
                return {"Address": address, "Result": result}, has_fiber

            except (TimeoutException, WebDriverException) as e:
                print(f"Error extracting result: {e}")
                driver.save_screenshot(f"screenshot_{address.replace(' ', '_')}_attempt_{attempt + 1}.png")
                if attempt < max_attempts - 1:
                    driver.quit()
                    driver, _ = setup_driver()
                    wait = WebDriverWait(driver, 90)
                    time.sleep(random.uniform(10, 20))
                else:
                    result = "Failed after retries - assumed no fiber"
                    has_fiber = False
                    return {"Address": address, "Result": result}, has_fiber

        except (TimeoutException, WebDriverException) as e:
            print(f"Error: {e}")
            driver.save_screenshot(f"screenshot_{address.replace(' ', '_')}_attempt_{attempt + 1}.png")
            if attempt < max_attempts - 1:
                driver.quit()
                driver, _ = setup_driver()
                wait = WebDriverWait(driver, 90)
                time.sleep(random.uniform(10, 20))
            else:
                result = "Failed after retries - assumed no fiber"
                has_fiber = False
                return {"Address": address, "Result": result}, has_fiber

def process_addresses(redfin_url: str) -> None:
    """Process addresses from Redfin and check AT&T availability.
    
    Args:
        redfin_url: URL to download Redfin data from
    """
    try:
        # Initialize services
        att_service = ATTService()
        bach_service = BachService()
        mailchimp_service = MailchimpService()
        
        # Download Redfin data
        print("\nDownloading Redfin data...")
        csv_file = download_redfin_data(redfin_url)
        if not csv_file:
            print("Failed to download Redfin data")
            return
            
        # Load and process addresses
        df = pd.read_csv(csv_file)
        addresses = df['ADDRESS'].dropna().tolist()
        
        print(f"\nFound {len(addresses)} addresses to process")
        
        try:
            # Check AT&T availability for each address
            print("\nChecking AT&T fiber availability...")
            fiber_available = []
            for address in addresses:
                result = att_service.check_fiber_availability(address)
                if result['has_fiber']:
                    fiber_available.append(address)
                    print(f"Fiber available at: {address}")
                    
            print(f"\nFound {len(fiber_available)} addresses with fiber available")
            
            if not fiber_available:
                print("No addresses with fiber available")
                return
                
            # Get contact information for addresses with fiber
            print("\nGetting contact information...")
            contact_info_list = []
            for address in fiber_available:
                contact_info = bach_service.get_contact_info(address)
                if 'error' not in contact_info:
                    contact_info_list.append(contact_info)
                    print(f"Got contact info for: {address}")
                    
            print(f"\nFound contact information for {len(contact_info_list)} addresses")
            
            if not contact_info_list:
                print("No contact information found")
                return
                
            # Send contact information to Mailchimp
            print("\nSending contact information to Mailchimp...")
            results = mailchimp_service.add_subscribers(contact_info_list)
            
            success_count = len([r for r in results if 'error' not in r])
            print(f"\nSuccessfully added {success_count} subscribers to Mailchimp")
            
        finally:
            # Clean up AT&T service
            try:
                att_service.driver.quit()
            except:
                pass
            
    except Exception as e:
        print(f"Error processing addresses: {str(e)}")
        
def main():
    """Main entry point."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m att_fiber_tracker.fiber_checker <redfin_url>")
        sys.exit(1)
        
    redfin_url = sys.argv[1]
    process_addresses(redfin_url) 
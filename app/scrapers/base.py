from abc import ABC, abstractmethod
import json
from pathlib import Path
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import time
from config import HEADLESS_BROWSER

class BaseScraper(ABC):
    """Base class for all job scrapers"""
    
    def setup_driver(self):
        """Set up and return a Chrome WebDriver instance with improved cookie handling"""
        # Set up Chrome options
        chrome_options = Options()
        
        if HEADLESS_BROWSER:
            chrome_options.add_argument("--headless")
        
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Use webdriver_manager to handle driver version compatibility
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # First navigate to the domain (required before adding cookies)
            domain = 'welcometothejungle.com' if 'WTTJ' in self.__class__.__name__ else 'hellowork.com'
            driver.get(f"https://www.{domain}")
            
            # Add a small delay to ensure the page is loaded
            time.sleep(1)

            cookies_name = "wttj_cookies" if 'WTTJ' in self.__class__.__name__ else "hellowork_cookies"
            
            # Try to load cookies with improved error handling
            cookies_loaded = self.load_cookies(driver, cookies_name)
            
            # Handle cookie dialogs if needed (cookies failed to load properly)
            if not cookies_loaded:
                if 'WTTJ' in self.__class__.__name__:
                    self._accept_cookies(driver)
                    self.login(driver)
                else:
                    # For HelloWork
                    try:
                        cookie_button = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.ID, "hw-cc-notice-accept-btn"))
                        )
                        cookie_button.click()
                        print("Accepted cookies")
                        self.save_cookies(driver, cookies_name)
                    except (TimeoutException, NoSuchElementException):
                        print("No cookie prompt found or already handled")
            
            return driver
        except Exception as e:
            print(f"Error setting up WebDriver: {e}")
            return None
    
    @abstractmethod
    def search_jobs(self, keywords, location, job_type=None):
        """
        Search for jobs using the provided parameters
        
        Args:
            keywords (str): Job keywords to search for
            location (str): Location to search in
            job_type (str, optional): Type of job (e.g., internship, full-time)
            
        Returns:
            list: List of job dictionaries with details
        """
        pass
    
    @abstractmethod
    def get_job_details(self, url):
        """
        Get detailed information about a specific job from its URL
        
        Args:
            url (str): URL of the job posting
            
        Returns:
            dict: Detailed job information
        """
        pass
    
    def get_cookies_path(self, domain):
        """Get the path to the cookies file for a specific domain."""
        cookies_dir = Path("cookies")
        cookies_dir.mkdir(exist_ok=True)
        return cookies_dir / f"{domain.replace('.', '_')}_cookies.json"

    def save_cookies(self, driver, domain):
        """Save cookies for a specific domain."""
        cookies_path = self.get_cookies_path(domain)
        cookies = driver.get_cookies()
        
        if cookies:
            Path(cookies_path).write_text(
                json.dumps(cookies, indent=2),
                encoding='utf-8'
            )
            print(f"Saved {len(cookies)} cookies for {domain}")
        else:
            print(f"No cookies to save for {domain}")

    def load_cookies(self, driver, domain):
        """Load cookies for a specific domain with improved error handling."""
        cookies_path = self.get_cookies_path(domain)
        if not cookies_path.exists():
            print(f"No cookie file found for {domain}")
            return False
            
        try:
            with open(cookies_path, 'r') as f:
                cookies = json.load(f)
                
            # Wait for page to be fully loaded before adding cookies
            WebDriverWait(driver, 10).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
            
            current_url = driver.current_url
            url_domain = current_url.split('/')[2]  # Extract domain from URL
            
            success_count = 0
            for cookie in cookies:
                try:
                    # Skip cookies with domain issues
                    if 'domain' in cookie:
                        cookie_domain = cookie['domain'].lstrip('.')
                        if not (url_domain.endswith(cookie_domain) or cookie_domain.endswith(url_domain)):
                            continue
                            
                    # Remove problematic fields that might cause rejection
                    if 'sameSite' in cookie and cookie['sameSite'] == 'None':
                        cookie['sameSite'] = 'Strict'
                    if 'expiry' in cookie and not isinstance(cookie['expiry'], (int, float)):
                        del cookie['expiry']
                    
                    driver.add_cookie(cookie)
                    success_count += 1
                except Exception as e:
                    print(f"Error adding cookie {cookie.get('name')}: {e}")
            
            print(f"Successfully loaded {success_count} of {len(cookies)} cookies for {domain}")
            
            # Refresh the page to apply cookies
            driver.refresh()
            return success_count > 0
        except Exception as e:
            print(f"Failed to load cookies for {domain}: {e}")
            return False
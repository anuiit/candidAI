from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

import time
import os

from .base import BaseScraper
from config import SELENIUM_TIMEOUT, SELENIUM_WAIT_TIME, HEADLESS_BROWSER, COOKIES_PATH
from config import WTTJ_LOGIN_EMAIL, WTTJ_LOGIN_PASSWORD


class WTTJScraper(BaseScraper):
    """Scraper for Welcome to the Jungle job site"""
    
    def _accept_cookies(self, driver):
        """Accept cookies if the prompt appears"""
        try:
            # Wait for the accept cookies button to be clickable
            accept_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '[aria-label="Accepter les cookies"]'))
            )
            accept_button.click()
            print("Accepted cookies")
        except (TimeoutException, NoSuchElementException, StaleElementReferenceException):
            print("Accept cookies button not found or not clickable")
    
    def login(self, driver):
        """Log in to Welcome to the Jungle site"""
        try:
            # Check if already logged in
            if driver.find_elements(By.CSS_SELECTOR, '[data-testid="not-logged-visible-login-button"]'):
                # Wait for the login button to be clickable
                login_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="not-logged-visible-login-button"]'))
                )
                login_button.click()
                
                login_valid_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="session-tab-login"]'))
                )
                login_valid_button.click()
                
                # Wait for the email input field to be present
                email_input = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="login-field-email"]'))
                )
                email_input.send_keys(WTTJ_LOGIN_EMAIL)
                
                # Wait for the password input field to be present
                password_input = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="login-field-password"]'))
                )
                password_input.send_keys(WTTJ_LOGIN_PASSWORD)
                
                # Submit the form
                submit_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="login-button-submit"]'))
                )
                submit_button.click()
                
                # Handle any finalize profile modal if it appears
                try:
                    finalize_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="finalize-profile-close-modal"]'))
                    )
                    finalize_button.click()
                except (TimeoutException, NoSuchElementException):
                    print("No finalize profile modal found")
                
                print("Successfully logged in to Welcome to the Jungle")
                
                # Save cookies after successful login
                self.save_cookies(driver, 'wttj')
        except Exception as e:
            print(f"Login failed: {e}")
    
    def _map_job_type_to_contract(self, job_type):
        """Map general job types to WTTJ contract types"""
        if job_type and job_type.lower() != "all":
            if job_type.lower() == "internship":
                return "internship"
            elif job_type.lower() == "full-time":
                return "permanent"
            elif job_type.lower() == "part-time":
                return "temporary"
        return None  # No specific contract type
    
    def navigate_to_page(self, driver, page_number):
        """Navigate to a specific page number in search results"""
        try:
            # Construct the URL with page parameter
            current_url = driver.current_url
            if "page=" in current_url:
                # Replace existing page parameter
                parts = current_url.split("page=")
                base = parts[0]
                rest = parts[1].split("&", 1)
                if len(rest) > 1:
                    new_url = f"{base}page={page_number}&{rest[1]}"
                else:
                    new_url = f"{base}page={page_number}"
            else:
                # Add page parameter
                if "?" in current_url:
                    new_url = current_url + f"&page={page_number}"
                else:
                    new_url = current_url + f"?page={page_number}"
            
            # Navigate to the new URL
            driver.get(new_url)
            time.sleep(SELENIUM_WAIT_TIME)
            return True
        except Exception as e:
            print(f"Error navigating to page {page_number}: {e}")
            return False
    
    def has_job_listings(self, driver):
        """Check if the current page has any job listings"""
        try:
            # Wait for job cards to load
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-role="jobs:thumb"]'))
            )
            
            # Check if there are any cards
            cards = driver.find_elements(By.CSS_SELECTOR, '[data-role="jobs:thumb"]')
            return len(cards) > 0
        except (TimeoutException, NoSuchElementException):
            return False
    
    def click_all_voir_plus_buttons(self, driver, max_attempts=3):
        """Find and click on all 'Voir Plus' buttons on the page"""
        buttons_clicked = 0
        clicked_buttons = set()  # Track which buttons we've already clicked
        
        for attempt in range(max_attempts):
            try:
                # Find all 'Voir Plus' links using more specific selectors
                voir_plus_elements = driver.find_elements(By.CSS_SELECTOR, 
                    '[data-testid="view-more-btn"]')
                
                # If none found, try alternative selectors
                if not voir_plus_elements:
                    voir_plus_elements = driver.find_elements(By.XPATH, 
                        "//a[contains(.//span, 'Voir plus')]")
                
                if not voir_plus_elements:
                    print(f"No more 'Voir Plus' buttons found on attempt {attempt+1}")
                    break
                    
                found_new = False
                
                for element in voir_plus_elements:
                    # Create a unique identifier for this element
                    element_id = element.id
                    
                    if element_id not in clicked_buttons and element.is_displayed():
                        try:
                            # Scroll to the element to make sure it's in view
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                            time.sleep(1)  # Give time for the page to settle
                            
                            # Click the element
                            element.click()
                            clicked_buttons.add(element_id)
                            buttons_clicked += 1
                            found_new = True
                            print(f"Clicked 'Voir Plus' button #{buttons_clicked}")
                            
                            # Wait for content to load
                            time.sleep(2)
                        except Exception as e:
                            print(f"Error clicking button: {e}")
                
                # If we didn't find any new buttons to click, we can stop
                if not found_new:
                    break
                    
            except Exception as e:
                print(f"Error finding 'Voir Plus' buttons: {e}")
                break
        
        return buttons_clicked
    
    def search_jobs(self, keywords, location, job_type=None, page=1, all_pages=False, max_pages=3):
        """
        Search for jobs on Welcome to the Jungle
        
        Parameters:
        - keywords: job search keywords
        - location: job location
        - job_type: type of job (internship, full-time, part-time)
        - page: specific page to fetch (default: 1)
        - all_pages: whether to fetch all pages up to max_pages (default: False)
        - max_pages: maximum number of pages to fetch when all_pages is True (default: 3)
        """
        driver = self.setup_driver()
        if not driver:
            return []
            
        try:
            # Map job_type to contract_type
            contract_type = self._map_job_type_to_contract(job_type)
            
            # Format location
            formatted_location = location.split(",")[0].strip() if "," in location else location
            
            # Create the search URL and navigate to it
            base_url = "https://www.welcometothejungle.com/fr/jobs"
            query_param = f"?query={keywords.replace(' ', '%20')}"
            location_param = f"&aroundQuery={formatted_location.replace(' ', '%20')}"
            radius_param = "&aroundRadius=20"
            page_param = f"&page={page}"
            country_param = "&refinementList%5Boffices.country_code%5D%5B%5D=FR"
            
            # Add contract type if specified
            contract_param = ""
            if contract_type:
                contract_param = f"&refinementList%5Bcontract_type%5D%5B%5D={contract_type}"
            
            # Combine all parameters
            search_url = f"{base_url}{query_param}{location_param}{radius_param}{page_param}{country_param}{contract_param}"
            
            # Navigate to search URL
            driver.get(search_url)
            time.sleep(SELENIUM_WAIT_TIME)
            
            # Initialize results list
            all_results = []
            
            # Get all job cards from the current page
            job_cards = self._get_all_job_cards(driver)
            all_results.extend(job_cards)
            
            # If all_pages is True, fetch additional pages
            current_page = page
            if all_pages and job_cards:
                while current_page < max_pages:
                    current_page += 1
                    success = self.navigate_to_page(driver, current_page)
                    
                    if success and self.has_job_listings(driver):
                        # Get job cards from this page
                        more_cards = self._get_all_job_cards(driver)
                        if more_cards:
                            all_results.extend(more_cards)
                            print(f"Added {len(more_cards)} jobs from page {current_page}")
                        else:
                            # No more job cards found, break the loop
                            break
                    else:
                        # Navigation failed or no job listings on page
                        break
            
            # Save cookies after successful search
            self.save_cookies(driver, 'wttj')
            
            return all_results
        except Exception as e:
            print(f"Error searching jobs: {e}")
            return []
        finally:
            driver.quit()
    
    def _get_all_job_cards(self, driver):
        """Extract all job cards from search results"""
        try:
            # Wait for job cards to load
            WebDriverWait(driver, SELENIUM_TIMEOUT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-role="jobs:thumb"]'))
            )
            
            # Find all job card elements
            card_elements = driver.find_elements(By.CSS_SELECTOR, '[data-role="jobs:thumb"]')
            
            print(f"Found {len(card_elements)} job cards")
            
            # Process each card
            results = []
            for index, card in enumerate(card_elements):
                try:
                    # Extract job title
                    title_element = card.find_element(By.CSS_SELECTOR, 'h4.wui-text div[role="mark"]')
                    title = title_element.text if title_element else None
                    
                    # Extract company name
                    company_element = card.find_element(By.CSS_SELECTOR, 'span.wui-text')
                    company = company_element.text if company_element else None
                    
                    # Extract location
                    location_element = card.find_element(By.CSS_SELECTOR, 'p.wui-text span span')
                    location = location_element.text if location_element else None
                    
                    # Get the link to the job details
                    link_element = card.find_element(By.CSS_SELECTOR, 'a[href*="/jobs/"]')
                    link = link_element.get_attribute('href') if link_element else None
                    
                    results.append({
                        "title": title,
                        "company": company,
                        "location": location,
                        "link": link,
                        "text": None  # Will be populated when getting job details
                    })
                except StaleElementReferenceException:
                    print(f"Stale element encountered at index {index + 1}")
                    continue
                except Exception as e:
                    print(f"Error processing card at index {index + 1}: {e}")
                    continue
            
            return results
        
        except TimeoutException:
            print("Timeout waiting for job cards to load")
            return []
        except NoSuchElementException:
            print("No job cards found on the page")
            return []
        except Exception as e:
            print(f"Error retrieving job cards: {e}")
            return []
    
    def get_job_details(self, url):
        """Get detailed information about a specific job"""
        driver = self.setup_driver()
        if not driver:
            return None
            
        try:
            driver.get(url)
            time.sleep(SELENIUM_WAIT_TIME)
            
            # Click on any "Voir Plus" buttons to expand content
            self.click_all_voir_plus_buttons(driver)
            
            # Extract job details
            job_text = self._extract_job_details(driver)
            
            # Save cookies after successful job details retrieval
            self.save_cookies(driver, 'wttj')
            
            return job_text
        except Exception as e:
            print(f"Error getting job details: {e}")
            return None
        finally:
            driver.quit()
    
    def _extract_job_details(self, driver):
        """Extract detailed job information from the job page"""
        try:
            # Wait for job details to load
            WebDriverWait(driver, SELENIUM_TIMEOUT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[id="the-position-section"]'))
            )

            job_description = None
            experience_text = ""
            
            try:
                job_description = driver.find_element(By.CSS_SELECTOR, '[data-testid="job-section-description"]')
            except NoSuchElementException:
                print("Job description section not found")
            
            try:
                experience_description = driver.find_element(By.CSS_SELECTOR, '[data-testid="job-section-experience"]')
                experience_text = experience_description.text
            except NoSuchElementException:
                print("Experience description section not found")
            
            # Combine the texts
            job_text = ""
            if job_description:
                job_text += job_description.text
            
            if experience_text:
                job_text += "\n\n" + experience_text
            
            if not job_text:
                # Try alternative approach to get content
                content_sections = driver.find_elements(By.CSS_SELECTOR, '[class*="ExpandableHtml_container"]')
                for section in content_sections:
                    job_text += section.text + "\n\n"
            
            return job_text if job_text else None
        
        except TimeoutException:
            print("Timeout waiting for job details to load")
            return None
        except Exception as e:
            print(f"Error extracting job details: {e}")
            return None
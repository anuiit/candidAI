from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

import time
import pandas as pd
import string
import os

from .base import BaseScraper
from config import SELENIUM_TIMEOUT, SELENIUM_WAIT_TIME, HEADLESS_BROWSER, COOKIES_PATH


class HelloWorkScraper(BaseScraper):
    """Scraper for HelloWork job site"""
    
    def navigate_to_page(self, driver, page_number):
        """Navigate to a specific page number in search results"""
        try:
            # Construct the URL with page parameter
            current_url = driver.current_url
            if "&p=" in current_url:
                # Replace existing page parameter
                new_url = current_url.split("&p=")[0] + f"&p={page_number}"
            else:
                # Add page parameter
                new_url = current_url + f"&p={page_number}"
            
            # Navigate to the new URL
            driver.get(new_url)
            time.sleep(SELENIUM_WAIT_TIME)
            return True
        except Exception as e:
            print(f"Error navigating to page {page_number}: {e}")
            return False

    def next_page(self, driver):
        """Navigate to the next page of search results"""
        try:
            # Find the current page number
            current_url = driver.current_url
            if "&p=" in current_url:
                page_part = current_url.split("&p=")[1].split("&")[0]
                try:
                    current_page = int(page_part)
                except ValueError:
                    current_page = 1
            else:
                current_page = 1
            
            # Navigate to the next page
            return self.navigate_to_page(driver, current_page + 1)
        except Exception as e:
            print(f"Error navigating to next page: {e}")
            return False

    def has_job_listings(self, driver):
        """Check if the current page has any job listings (SerpCards)"""
        try:
            # Wait a short time for cards to load
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-cy="serpCard"]'))
            )
            
            # Check if there are any cards
            cards = driver.find_elements(By.CSS_SELECTOR, '[data-cy="serpCard"]')
            return len(cards) > 0
        except (TimeoutException, NoSuchElementException):
            return False

    def search_jobs(self, keywords, location, job_type=None, page=1, all_pages=False, max_pages=3):
        """
        Search for jobs on HelloWork
        
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
            # Construct the search URL
            base_url = "https://www.hellowork.com/fr-fr/emploi/recherche.html"
            search_url = f"{base_url}?k={keywords.replace(' ', '+')}&l={location.replace(' ', '+')}"
            
            # Add job type if specified
            if job_type and job_type.lower() != "all":
                job_type_param = ""
                if job_type.lower() == "internship":
                    job_type_param = "&c=Stage"
                elif job_type.lower() == "full-time":
                    job_type_param = "&c=CDI"
                elif job_type.lower() == "part-time":
                    job_type_param = "&c=CDD"
                
                search_url += job_type_param
            
            # Add page parameter if specified and not page 1
            if page > 1:
                search_url += f"&p={page}"
            
            # Navigate to search URL
            driver.get(search_url)
            time.sleep(SELENIUM_WAIT_TIME)
            
            # Check if cookie accept/deny dialog is present and handle it
            try:
                cookie_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.ID, "didomi-notice-agree-button"))
                )
                cookie_button.click()
                print("Accepted cookies")
                
                # Save cookies after accepting
                self.save_cookies(driver, 'hellowork')
                print("Cookies saved")
            except (TimeoutException, NoSuchElementException):
                print("No cookie prompt found or already handled")
            
            # Initialize results list
            all_results = []
            
            # Get all job cards from the current page
            job_cards = self._get_all_serp_cards(driver)
            all_results.extend(job_cards)
            
            # If all_pages is True, fetch additional pages
            current_page = page
            if all_pages and job_cards:
                while current_page < max_pages:
                    current_page += 1
                    success = self.navigate_to_page(driver, current_page)
                    
                    if success and self.has_job_listings(driver):
                        # Get job cards from this page
                        more_cards = self._get_all_serp_cards(driver)
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
            self.save_cookies(driver, 'hellowork')
            
            return all_results
        except Exception as e:
            print(f"Error searching jobs: {e}")
            return []
        finally:
            driver.quit()
    
    def get_job_details(self, url):
        """Get detailed information about a specific job"""
        driver = self.setup_driver()
        if not driver:
            return None
            
        try:
            driver.get(url)
            time.sleep(SELENIUM_WAIT_TIME)
            
            # Extract job details
            section_data = self._get_section_text(driver)
            
            # Save cookies after successful job details retrieval
            self.save_cookies(driver, 'hellowork')
            
            return section_data
        except Exception as e:
            print(f"Error getting job details: {e}")
            return None
        finally:
            driver.quit()
    
    def _get_all_serp_cards(self, driver):
        """Extract all job cards from search results"""
        try:
            # Wait for at least one card to be present
            WebDriverWait(driver, SELENIUM_TIMEOUT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-cy="serpCard"]'))
            )
            
            # Find all elements with data-cy="serpCard"
            card_elements = driver.find_elements(By.CSS_SELECTOR, '[data-cy="serpCard"]')
            
            print(f"Found {len(card_elements)} SERP cards")
            
            # Process each card
            results = []
            for index, card in enumerate(card_elements):
                try:
                    # Extract title and company
                    title_element = card.find_element(By.CSS_SELECTOR, 'h3') if card.find_elements(By.CSS_SELECTOR, 'h3') else None
                    title_text = title_element.text if title_element else None
                    
                    title = title_text.split("\n")[0] if title_text else None
                    company = title_text.split("\n")[1] if title_text and "\n" in title_text else None
                    
                    # Extract location
                    location = card.find_element(By.CSS_SELECTOR, '[data-cy="localisationCard"]').text if card.find_elements(By.CSS_SELECTOR, '[data-cy="localisationCard"]') else None
                    
                    # Get the link
                    try:
                        link_element = card.find_element(By.CSS_SELECTOR, 'a')
                        link = link_element.get_attribute('href')
                    except:
                        link = None
                    
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
            
            return results
        
        except TimeoutException:
            print("Timeout waiting for SERP cards to load")
            return []
        except NoSuchElementException:
            print("No SERP cards found on the page")
            return []
        except Exception as e:
            print(f"Error retrieving SERP cards: {e}")
            return []
    
    def _get_section_text(self, driver):
        """Extract job description text from a specific section"""
        try:
            # First, wait for the base div to be present
            base_div_xpath = "/html/body/main/div[4]/div[3]/div[1]/div[2]/div/div[2]"
            WebDriverWait(driver, SELENIUM_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, base_div_xpath))
            )
            
            # Check if the base div exists
            try:
                base_div = driver.find_element(By.XPATH, base_div_xpath)
            except NoSuchElementException:
                print("Base div not found")
                return None
            
            elements_to_exclude = driver.find_elements(By.CSS_SELECTOR, 'div button')
            excluded_texts = []
            
            for element in elements_to_exclude:
                text = element.text
                if text in string.punctuation:
                    # Skip punctuation-only texts
                    continue
                excluded_texts.append(text)
            
            # Get the original full text
            full_text = base_div.text
            
            # Remove the excluded texts from the full text
            cleaned_text = full_text
            for text_to_exclude in excluded_texts:
                cleaned_text = cleaned_text.replace(text_to_exclude, "")
            
            # Check if there's a section inside the div
            section_xpath = f"{base_div_xpath}/section"
            try:
                # Check for a paragraph in the section
                p_path = f"{section_xpath}/p"
                try:
                    p = driver.find_element(By.XPATH, p_path)
                    p_text = p.text
                except NoSuchElementException:
                    p_text = None
                
                # Check if there's an h2 inside the section
                h2_xpath = f"{section_xpath}/h2"
                try:
                    h2 = driver.find_element(By.XPATH, h2_xpath)
                    h2_text = h2.text
                    
                    # Return all text content
                    return {
                        "structure_found": True,
                        "original_text": full_text,
                        "cleaned_text": cleaned_text,
                        "h2_text": h2_text,
                        "p_text": p_text if p_text else None,
                        "excluded_sections": excluded_texts
                    }
                except NoSuchElementException:
                    return {
                        "structure_found": False,
                        "original_text": full_text,
                        "cleaned_text": cleaned_text,
                        "excluded_sections": excluded_texts
                    }
            except NoSuchElementException:
                return {
                    "structure_found": False,
                    "original_text": full_text,
                    "cleaned_text": cleaned_text,
                    "excluded_sections": excluded_texts
                }
        
        except TimeoutException:
            print("Timeout waiting for the base div to load")
            return None
        except Exception as e:
            print(f"Error retrieving section text: {e}")
            return None
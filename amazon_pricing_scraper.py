import re
import time
import random
import json
import logging
from datetime import datetime
from typing import Dict, Optional, List
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class AmazonPricingScraper:
    """
    Enhanced scraper for extracting detailed pricing information from Amazon product pages.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Various price selectors to try
        self.price_selectors = [
            # Current price selectors
            'span.a-price.a-text-price.a-size-medium.apexPriceToPay span.a-offscreen',
            'span.a-price-whole',
            'span#priceblock_ourprice',
            'span#priceblock_dealprice', 
            'span#price_inside_buybox',
            'span.a-price.a-text-price.a-size-base span.a-offscreen',
            'span.a-price-range',
            '.a-price .a-offscreen',
            '#apex_desktop .a-price .a-offscreen',
            'span[data-a-size="xl"] .a-offscreen',
            'span[data-a-size="l"] .a-offscreen'
        ]
        
        # List price selectors
        self.list_price_selectors = [
            'span.a-price.a-text-price span.a-offscreen',
            'span#listPrice',
            'span.a-price.a-text-price.a-size-base.a-color-secondary span.a-offscreen',
            '.a-price.a-text-price .a-offscreen',
            'span[data-a-strike="true"] .a-offscreen'
        ]
        
        # Availability selectors
        self.availability_selectors = [
            '#availability span',
            '#availability .a-color-success',
            '#availability .a-color-state',
            '#merchant-info',
            '.a-color-success',
            '.a-color-price'
        ]
    
    def extract_pricing_data(self, driver: WebDriver, asin: str) -> Dict:
        """
        Extract comprehensive pricing data for a given ASIN.
        
        Args:
            driver: Selenium WebDriver instance
            asin: Amazon Standard Identification Number
            
        Returns:
            Dictionary containing pricing and product information
        """
        product_url = f"https://www.amazon.com/dp/{asin}"
        
        data = {
            'asin': asin,
            'url': product_url,
            'title': None,
            'current_price': None,
            'current_price_numeric': None,
            'list_price': None,
            'list_price_numeric': None,
            'discount_amount': None,
            'discount_percentage': None,
            'availability': None,
            'prime_eligible': False,
            'seller': None,
            'scraped_at': datetime.now().isoformat(),
            'error': None
        }
        
        try:
            self.logger.info(f"Scraping pricing data for ASIN: {asin}")
            driver.get(product_url)
            
            # Wait for page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "dp-container"))
            )
            
            # Random delay to mimic human behavior
            time.sleep(random.uniform(2, 5))
            
            # Extract title
            data['title'] = self._extract_title(driver)
            
            # Extract current price
            data['current_price'], data['current_price_numeric'] = self._extract_current_price(driver)
            
            # Extract list price
            data['list_price'], data['list_price_numeric'] = self._extract_list_price(driver)
            
            # Calculate discount
            if data['current_price_numeric'] and data['list_price_numeric']:
                discount_amount = data['list_price_numeric'] - data['current_price_numeric']
                discount_percentage = (discount_amount / data['list_price_numeric']) * 100
                data['discount_amount'] = f"${discount_amount:.2f}"
                data['discount_percentage'] = f"{discount_percentage:.1f}%"
            
            # Extract availability
            data['availability'] = self._extract_availability(driver)
            
            # Check Prime eligibility
            data['prime_eligible'] = self._check_prime_eligibility(driver)
            
            # Extract seller information
            data['seller'] = self._extract_seller(driver)
            
            self.logger.info(f"Successfully scraped pricing data for ASIN: {asin}")
            
        except TimeoutException:
            error_msg = f"Timeout loading product page for ASIN: {asin}"
            self.logger.error(error_msg)
            data['error'] = error_msg
            
        except Exception as e:
            error_msg = f"Error scraping ASIN {asin}: {str(e)}"
            self.logger.error(error_msg)
            data['error'] = error_msg
        
        return data
    
    def _extract_title(self, driver: WebDriver) -> Optional[str]:
        """Extract product title."""
        selectors = ['#productTitle', 'h1.a-size-large']
        
        for selector in selectors:
            try:
                element = driver.find_element(By.CSS_SELECTOR, selector)
                title = element.text.strip()
                if title:
                    return title
            except NoSuchElementException:
                continue
        return None
    
    def _extract_current_price(self, driver: WebDriver) -> tuple:
        """Extract current/selling price."""
        for selector in self.price_selectors:
            try:
                element = driver.find_element(By.CSS_SELECTOR, selector)
                price_text = element.text.strip()
                if price_text and '$' in price_text:
                    numeric_price = self._parse_price(price_text)
                    if numeric_price:
                        return price_text, numeric_price
            except NoSuchElementException:
                continue
        
        # Try alternative approach - look for JSON-LD data
        try:
            script_tags = driver.find_elements(By.XPATH, '//script[@type="application/ld+json"]')
            for script in script_tags:
                content = script.get_attribute('innerHTML')
                if content:
                    data = json.loads(content)
                    if isinstance(data, dict) and 'offers' in data:
                        offers = data['offers']
                        if isinstance(offers, dict) and 'price' in offers:
                            price = float(offers['price'])
                            return f"${price:.2f}", price
        except:
            pass
        
        return None, None
    
    def _extract_list_price(self, driver: WebDriver) -> tuple:
        """Extract list/original price."""
        for selector in self.list_price_selectors:
            try:
                element = driver.find_element(By.CSS_SELECTOR, selector)
                price_text = element.text.strip()
                if price_text and '$' in price_text:
                    numeric_price = self._parse_price(price_text)
                    if numeric_price:
                        return price_text, numeric_price
            except NoSuchElementException:
                continue
        return None, None
    
    def _extract_availability(self, driver: WebDriver) -> Optional[str]:
        """Extract availability status."""
        for selector in self.availability_selectors:
            try:
                element = driver.find_element(By.CSS_SELECTOR, selector)
                availability = element.text.strip()
                if availability:
                    return availability
            except NoSuchElementException:
                continue
        return None
    
    def _check_prime_eligibility(self, driver: WebDriver) -> bool:
        """Check if product is Prime eligible."""
        prime_selectors = [
            '[data-csa-c-content-id="prime-logo"]',
            '.a-icon-prime',
            '[aria-label*="Prime"]',
            'i[aria-label*="Prime"]'
        ]
        
        for selector in prime_selectors:
            try:
                driver.find_element(By.CSS_SELECTOR, selector)
                return True
            except NoSuchElementException:
                continue
        return False
    
    def _extract_seller(self, driver: WebDriver) -> Optional[str]:
        """Extract seller information."""
        seller_selectors = [
            '#merchant-info a',
            '#sellerProfileTriggerId',
            '[data-csa-c-content-id="merchant-info"] a',
            '.tabular-buybox-text[tabular-attribute-name="Sold by"] span'
        ]
        
        for selector in seller_selectors:
            try:
                element = driver.find_element(By.CSS_SELECTOR, selector)
                seller = element.text.strip()
                if seller:
                    return seller
            except NoSuchElementException:
                continue
        return None
    
    def _parse_price(self, price_text: str) -> Optional[float]:
        """Parse price text to extract numeric value."""
        try:
            # Remove currency symbols and other characters, keep numbers and decimal points
            cleaned_price = re.sub(r'[^\d.]', '', price_text)
            if cleaned_price:
                return float(cleaned_price)
        except (ValueError, AttributeError):
            pass
        return None
    
    def scrape_multiple_asins(self, driver: WebDriver, asins: List[str], delay_range: tuple = (3, 8)) -> List[Dict]:
        """
        Scrape pricing data for multiple ASINs.
        
        Args:
            driver: Selenium WebDriver instance
            asins: List of ASINs to scrape
            delay_range: Tuple of (min, max) seconds to wait between requests
            
        Returns:
            List of dictionaries containing pricing data
        """
        results = []
        total_asins = len(asins)
        
        for i, asin in enumerate(asins, 1):
            self.logger.info(f"Processing ASIN {i}/{total_asins}: {asin}")
            
            # Scrape the ASIN
            result = self.extract_pricing_data(driver, asin)
            results.append(result)
            
            # Add delay between requests (except for the last one)
            if i < total_asins:
                delay = random.uniform(*delay_range)
                self.logger.info(f"Waiting {delay:.1f} seconds before next request...")
                time.sleep(delay)
        
        return results
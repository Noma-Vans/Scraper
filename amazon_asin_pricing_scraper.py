#!/usr/bin/env python3
import os
import time
import random
import logging
import json
import re
from datetime import datetime
from typing import Dict, Optional, List
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import undetected_chromedriver as uc
from aws_s3_utils import load_search_terms, save_results


def setup_driver(proxy: str = None) -> WebDriver:
    """Setup Chrome WebDriver with anti-detection measures."""
    options = uc.ChromeOptions()
    options.add_argument('--headless=new')
    
    # User agents
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    ]
    
    options.add_argument(f"--user-agent={random.choice(USER_AGENTS)}")
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    
    if proxy:
        options.add_argument(f'--proxy-server={proxy}')
    
    driver = uc.Chrome(options=options)
    driver.set_page_load_timeout(30)
    driver.implicitly_wait(10)
    return driver


def parse_price(price_text: str) -> Optional[float]:
    """Parse price text to extract numeric value."""
    if not price_text:
        return None
    try:
        # Remove currency symbols and other characters, keep numbers and decimal points
        cleaned_price = re.sub(r'[^\d.]', '', price_text)
        if cleaned_price:
            return float(cleaned_price)
    except (ValueError, AttributeError):
        pass
    return None


def extract_asin_pricing_details(driver: WebDriver, asin: str) -> Dict:
    """
    Extract comprehensive pricing details for a given ASIN.
    Follows the existing pattern from detail_page.py but with enhanced pricing extraction.
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
        'buy_box_price': None,
        'scraped_at': datetime.utcnow().isoformat(),
        'details_json_ld': None,
        'error': None
    }
    
    try:
        logging.info(f"Scraping pricing data for ASIN: {asin}")
        driver.get(product_url)
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "dp-container"))
        )
        
        # Random human-like delay
        time.sleep(random.uniform(2, 6))
        
        # Extract JSON-LD data first (following existing pattern)
        try:
            ld_json = driver.find_element(By.XPATH, '//script[@type="application/ld+json"]').get_attribute('innerHTML')
            data['details_json_ld'] = json.loads(ld_json)
        except Exception:
            pass
        
        # Title (following existing pattern)
        try:
            data['title'] = driver.find_element(By.ID, 'productTitle').text.strip()
        except Exception:
            pass
        
        # Enhanced price extraction with multiple selectors
        current_price_selectors = [
            'span.a-price.a-text-price.a-size-medium.apexPriceToPay span.a-offscreen',
            'span.a-price-whole',
            'span#priceblock_ourprice',
            'span#priceblock_dealprice',
            'span#priceblock_saleprice',
            'span#price_inside_buybox',
            'span.a-price.a-text-price.a-size-base span.a-offscreen',
            '.a-price .a-offscreen',
            '#apex_desktop .a-price .a-offscreen'
        ]
        
        # Current price extraction
        for selector in current_price_selectors:
            try:
                price_element = driver.find_element(By.CSS_SELECTOR, selector)
                price_text = price_element.text.strip()
                if price_text and '$' in price_text:
                    data['current_price'] = price_text
                    data['current_price_numeric'] = parse_price(price_text)
                    break
            except NoSuchElementException:
                continue
        
        # Buy Box Price (following existing pattern)
        try:
            bb = driver.find_element(By.ID, 'price_inside_buybox').text.strip()
            data['buy_box_price'] = bb
        except Exception:
            pass
        
        # List price extraction
        list_price_selectors = [
            'span.a-price.a-text-price span.a-offscreen',
            'span#listPrice',
            'span.a-price.a-text-price.a-size-base.a-color-secondary span.a-offscreen',
            '.a-price.a-text-price .a-offscreen',
            'span[data-a-strike="true"] .a-offscreen'
        ]
        
        for selector in list_price_selectors:
            try:
                price_element = driver.find_element(By.CSS_SELECTOR, selector)
                price_text = price_element.text.strip()
                if price_text and '$' in price_text:
                    data['list_price'] = price_text
                    data['list_price_numeric'] = parse_price(price_text)
                    break
            except NoSuchElementException:
                continue
        
        # Calculate discount
        if data['current_price_numeric'] and data['list_price_numeric']:
            discount_amount = data['list_price_numeric'] - data['current_price_numeric']
            discount_percentage = (discount_amount / data['list_price_numeric']) * 100
            data['discount_amount'] = f"${discount_amount:.2f}"
            data['discount_percentage'] = f"{discount_percentage:.1f}%"
        
        # Availability (following existing pattern)
        try:
            data['availability'] = driver.find_element(By.ID, 'availability').text.strip()
        except Exception:
            # Try alternative selectors
            availability_selectors = [
                '#availability span',
                '#availability .a-color-success',
                '#availability .a-color-state',
                '#merchant-info'
            ]
            for selector in availability_selectors:
                try:
                    element = driver.find_element(By.CSS_SELECTOR, selector)
                    availability = element.text.strip()
                    if availability:
                        data['availability'] = availability
                        break
                except NoSuchElementException:
                    continue
        
        # Prime eligibility
        prime_selectors = [
            '[data-csa-c-content-id="prime-logo"]',
            '.a-icon-prime',
            '[aria-label*="Prime"]',
            'i[aria-label*="Prime"]'
        ]
        
        for selector in prime_selectors:
            try:
                driver.find_element(By.CSS_SELECTOR, selector)
                data['prime_eligible'] = True
                break
            except NoSuchElementException:
                continue
        
        # Seller information
        seller_selectors = [
            '#merchant-info a',
            '#sellerProfileTriggerId',
            '[data-csa-c-content-id="merchant-info"] a'
        ]
        
        for selector in seller_selectors:
            try:
                element = driver.find_element(By.CSS_SELECTOR, selector)
                seller = element.text.strip()
                if seller:
                    data['seller'] = seller
                    break
            except NoSuchElementException:
                continue
        
        logging.info(f"Successfully scraped pricing data for ASIN: {asin}")
        
    except TimeoutException:
        error_msg = f"Timeout loading product page for ASIN: {asin}"
        logging.error(error_msg)
        data['error'] = error_msg
        
    except Exception as e:
        error_msg = f"Error scraping ASIN {asin}: {str(e)}"
        logging.error(error_msg)
        data['error'] = error_msg
    
    return data


def main():
    """
    Main function following the existing pattern from main.py
    """
    logging.basicConfig(
        format='%(asctime)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

    # Environment variables for S3 (following existing pattern)
    search_bucket = os.environ.get('SEARCH_BUCKET')
    if not search_bucket:
        raise ValueError("Required environment variable 'SEARCH_BUCKET' is not set")
    
    # For ASIN pricing, we expect the S3 file to contain ASINs instead of search terms
    asin_key = os.environ.get('ASIN_KEY', os.environ.get('SEARCH_KEY'))
    if not asin_key:
        raise ValueError("Required environment variable 'ASIN_KEY' or 'SEARCH_KEY' is not set")
    
    output_bucket = os.environ['OUTPUT_BUCKET']
    output_prefix = os.environ.get('OUTPUT_PREFIX', 'pricing_results/')
    proxy = os.environ.get('PROXY')

    # Load ASINs from S3 (reusing existing load_search_terms function)
    asins = load_search_terms(search_bucket, asin_key)
    logging.info(f"Loaded {len(asins)} ASINs from S3")
    
    driver = setup_driver(proxy)
    
    all_pricing_data = []
    
    for i, asin in enumerate(asins, 1):
        logging.info(f"Processing ASIN {i}/{len(asins)}: {asin}")
        
        try:
            pricing_details = extract_asin_pricing_details(driver, asin)
            all_pricing_data.append(pricing_details)
            
            # Short delay between ASINs
            if i < len(asins):
                delay = random.uniform(3, 8)
                logging.info(f"Waiting {delay:.1f} seconds before next ASIN...")
                time.sleep(delay)
                
        except Exception as e:
            logging.error(f"Error processing ASIN '{asin}': {e}")
            # Add error record
            error_record = {
                'asin': asin,
                'error': str(e),
                'scraped_at': datetime.utcnow().isoformat()
            }
            all_pricing_data.append(error_record)

    # Write results to S3 (following existing pattern)
    timestamp = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    output_key = f"{output_prefix}amazon_pricing_{timestamp}.json"
    save_results(output_bucket, output_key, all_pricing_data)
    
    # Summary
    successful = len([item for item in all_pricing_data if not item.get('error')])
    failed = len([item for item in all_pricing_data if item.get('error')])
    
    logging.info(f"Pricing scraping completed. Success: {successful}, Failed: {failed}")
    logging.info(f"Results saved to s3://{output_bucket}/{output_key}")
    
    driver.quit()


if __name__ == '__main__':
    main()
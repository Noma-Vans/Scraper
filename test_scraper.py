#!/usr/bin/env python3
"""
Test script for Amazon Price Monitor

This script tests the scraper with a few sample ASINs to verify functionality.
"""

import os
import sys
import logging
from dotenv import load_dotenv
import undetected_chromedriver as uc

from amazon_pricing_scraper import AmazonPricingScraper


def setup_test_driver():
    """Setup a test WebDriver instance."""
    options = uc.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = uc.Chrome(options=options)
    driver.set_page_load_timeout(30)
    return driver


def main():
    """Test the Amazon pricing scraper with sample ASINs."""
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    # Load environment variables
    load_dotenv()
    
    # Sample ASINs for testing (popular products that should be available)
    test_asins = [
        'B08N5WRWNW',  # Echo Dot (4th Gen)
        'B07XJ8C8F5',  # Echo Show 5
        'B0BDKDXRMZ',  # Kindle Scribe
    ]
    
    logger.info("Starting Amazon Price Monitor test")
    logger.info(f"Testing with ASINs: {test_asins}")
    
    driver = None
    try:
        # Setup driver
        logger.info("Setting up WebDriver...")
        driver = setup_test_driver()
        
        # Initialize scraper
        scraper = AmazonPricingScraper()
        
        # Test scraping
        logger.info("Starting price scraping test...")
        results = scraper.scrape_multiple_asins(driver, test_asins, delay_range=(2, 4))
        
        # Display results
        logger.info("Test Results:")
        logger.info("=" * 50)
        
        for result in results:
            asin = result['asin']
            title = result.get('title', 'N/A')[:50] + '...' if result.get('title') else 'N/A'
            current_price = result.get('current_price', 'N/A')
            availability = result.get('availability', 'N/A')
            error = result.get('error')
            
            logger.info(f"ASIN: {asin}")
            logger.info(f"  Title: {title}")
            logger.info(f"  Price: {current_price}")
            logger.info(f"  Availability: {availability}")
            
            if error:
                logger.error(f"  Error: {error}")
            else:
                logger.info("  Status: SUCCESS")
            
            logger.info("-" * 30)
        
        # Summary
        successful = len([r for r in results if not r.get('error')])
        failed = len([r for r in results if r.get('error')])
        
        logger.info(f"Test Summary: {successful} successful, {failed} failed")
        
        if successful > 0:
            logger.info("✅ Scraper is working correctly!")
            return True
        else:
            logger.error("❌ All tests failed. Check your setup.")
            return False
            
    except Exception as e:
        logger.error(f"Test failed with exception: {e}")
        return False
        
    finally:
        if driver:
            driver.quit()
            logger.info("WebDriver closed")


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
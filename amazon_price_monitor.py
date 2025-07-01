#!/usr/bin/env python3
"""
Amazon Price Monitor - Main Application

This script reads ASINs from a Google Sheet, scrapes pricing data from Amazon,
and writes the results back to the Google Sheet.

Usage:
    python amazon_price_monitor.py

Environment Variables:
    GOOGLE_SHEETS_CREDENTIALS: JSON string containing Google service account credentials
    GOOGLE_SHEET_URL: URL or ID of the Google Sheet containing ASINs
    WORKSHEET_NAME: Name of the worksheet (optional, defaults to first sheet)
    ASIN_COLUMN: Column containing ASINs (optional, defaults to 'A')
    PROXY: Proxy server URL (optional)
    HEADLESS: Run browser in headless mode (optional, defaults to True)
    MIN_DELAY: Minimum delay between requests in seconds (optional, defaults to 3)
    MAX_DELAY: Maximum delay between requests in seconds (optional, defaults to 8)
"""

import os
import sys
import logging
import random
import signal
from typing import List, Dict
import undetected_chromedriver as uc
from selenium.webdriver.remote.webdriver import WebDriver
from dotenv import load_dotenv

from google_sheets_utils import GoogleSheetsClient
from amazon_pricing_scraper import AmazonPricingScraper


class AmazonPriceMonitor:
    """
    Main application class for monitoring Amazon prices.
    """
    
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('amazon_price_monitor.log')
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.google_sheet_url = os.environ.get('GOOGLE_SHEET_URL')
        self.worksheet_name = os.environ.get('WORKSHEET_NAME')
        self.asin_column = os.environ.get('ASIN_COLUMN', 'A')
        self.proxy = os.environ.get('PROXY')
        self.headless = os.environ.get('HEADLESS', 'True').lower() == 'true'
        self.min_delay = int(os.environ.get('MIN_DELAY', '3'))
        self.max_delay = int(os.environ.get('MAX_DELAY', '8'))
        
        # Validate required configuration
        if not self.google_sheet_url:
            raise ValueError("GOOGLE_SHEET_URL environment variable is required")
        
        # Initialize components
        self.sheets_client = GoogleSheetsClient()
        self.pricing_scraper = AmazonPricingScraper()
        self.driver = None
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def setup_driver(self) -> WebDriver:
        """Setup and return a configured Chrome WebDriver."""
        self.logger.info("Setting up Chrome WebDriver...")
        
        options = uc.ChromeOptions()
        
        # Basic options
        if self.headless:
            options.add_argument('--headless=new')
        
        # Anti-detection options
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-plugins')
        options.add_argument('--disable-images')
        options.add_argument('--disable-javascript')
        
        # Set a random user agent
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        ]
        options.add_argument(f"--user-agent={random.choice(user_agents)}")
        
        # Proxy configuration
        if self.proxy:
            options.add_argument(f'--proxy-server={self.proxy}')
            self.logger.info(f"Using proxy: {self.proxy}")
        
        # Create driver
        driver = uc.Chrome(options=options)
        driver.set_page_load_timeout(30)
        driver.implicitly_wait(10)
        
        self.logger.info("Chrome WebDriver setup complete")
        return driver
    
    def run(self) -> bool:
        """
        Main execution method.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info("Starting Amazon Price Monitor...")
            
            # Setup WebDriver
            self.driver = self.setup_driver()
            
            # Load ASINs from Google Sheet
            self.logger.info("Loading ASINs from Google Sheet...")
            asins = self.sheets_client.load_asins_from_sheet(
                sheet_url=self.google_sheet_url,
                worksheet_name=self.worksheet_name,
                asin_column=self.asin_column
            )
            
            if not asins:
                self.logger.warning("No ASINs found in Google Sheet")
                return False
            
            self.logger.info(f"Found {len(asins)} ASINs to process")
            
            # Scrape pricing data
            self.logger.info("Starting price scraping...")
            pricing_data = self.pricing_scraper.scrape_multiple_asins(
                driver=self.driver,
                asins=asins,
                delay_range=(self.min_delay, self.max_delay)
            )
            
            # Process results
            successful_scrapes = [item for item in pricing_data if not item.get('error')]
            failed_scrapes = [item for item in pricing_data if item.get('error')]
            
            self.logger.info(f"Scraping completed. Success: {len(successful_scrapes)}, Failed: {len(failed_scrapes)}")
            
            if failed_scrapes:
                self.logger.warning("Failed ASINs:")
                for item in failed_scrapes:
                    self.logger.warning(f"  {item['asin']}: {item['error']}")
            
            # Write results back to Google Sheet
            if pricing_data:
                self.logger.info("Writing results to Google Sheet...")
                self.sheets_client.write_pricing_data(
                    sheet_url=self.google_sheet_url,
                    pricing_data=pricing_data,
                    worksheet_name=self.worksheet_name
                )
                self.logger.info("Results written to Google Sheet successfully")
            
            self.logger.info("Amazon Price Monitor completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error in main execution: {e}", exc_info=True)
            return False
        
        finally:
            # Cleanup
            if self.driver:
                try:
                    self.driver.quit()
                    self.logger.info("WebDriver closed")
                except:
                    pass
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
        sys.exit(0)


def main():
    """Entry point for the application."""
    monitor = AmazonPriceMonitor()
    success = monitor.run()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
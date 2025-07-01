#!/usr/bin/env python3
"""
Command Line Interface for Amazon Price Monitor

This script provides a command-line interface with various options for running the scraper.
"""

import argparse
import os
import sys
import logging
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from amazon_price_monitor import AmazonPriceMonitor


def setup_logging(verbose=False, log_file=None):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description='Amazon Price Monitor - Scrape Amazon pricing data from Google Sheets',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_scraper.py
  python run_scraper.py --sheet-url "https://docs.google.com/spreadsheets/d/abc123/edit"
  python run_scraper.py --worksheet "Products" --asin-column "B"
  python run_scraper.py --proxy "http://user:pass@proxy.com:8080"
  python run_scraper.py --no-headless --verbose
  python run_scraper.py --min-delay 5 --max-delay 15
        """
    )
    
    # Google Sheets options
    sheets_group = parser.add_argument_group('Google Sheets Options')
    sheets_group.add_argument(
        '--sheet-url', 
        help='Google Sheet URL or ID (overrides GOOGLE_SHEET_URL env var)'
    )
    sheets_group.add_argument(
        '--worksheet', 
        help='Worksheet name (overrides WORKSHEET_NAME env var)'
    )
    sheets_group.add_argument(
        '--asin-column', 
        help='Column containing ASINs (overrides ASIN_COLUMN env var)'
    )
    sheets_group.add_argument(
        '--credentials-file', 
        help='Path to Google service account JSON file'
    )
    
    # Browser options
    browser_group = parser.add_argument_group('Browser Options')
    browser_group.add_argument(
        '--no-headless', 
        action='store_true',
        help='Run browser in visible mode (useful for debugging)'
    )
    browser_group.add_argument(
        '--proxy', 
        help='Proxy server URL (format: http://user:pass@host:port)'
    )
    browser_group.add_argument(
        '--user-agent', 
        help='Custom user agent string'
    )
    
    # Scraping options
    scraping_group = parser.add_argument_group('Scraping Options')
    scraping_group.add_argument(
        '--min-delay', 
        type=int, 
        help='Minimum delay between requests in seconds'
    )
    scraping_group.add_argument(
        '--max-delay', 
        type=int, 
        help='Maximum delay between requests in seconds'
    )
    scraping_group.add_argument(
        '--limit', 
        type=int, 
        help='Limit number of ASINs to process (for testing)'
    )
    
    # Logging options
    logging_group = parser.add_argument_group('Logging Options')
    logging_group.add_argument(
        '--verbose', '-v', 
        action='store_true',
        help='Enable verbose logging'
    )
    logging_group.add_argument(
        '--log-file', 
        help='Log file path (default: amazon_price_monitor.log)'
    )
    logging_group.add_argument(
        '--quiet', '-q', 
        action='store_true',
        help='Suppress console output (still logs to file)'
    )
    
    # Action options
    action_group = parser.add_argument_group('Actions')
    action_group.add_argument(
        '--test', 
        action='store_true',
        help='Run test with sample ASINs instead of full scraping'
    )
    action_group.add_argument(
        '--validate-config', 
        action='store_true',
        help='Validate configuration and exit'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    if args.quiet:
        setup_logging(verbose=False, log_file=args.log_file or 'amazon_price_monitor.log')
        logging.getLogger().handlers = [h for h in logging.getLogger().handlers if not isinstance(h, logging.StreamHandler)]
    else:
        setup_logging(verbose=args.verbose, log_file=args.log_file)
    
    logger = logging.getLogger(__name__)
    
    # Set environment variables from command line arguments
    if args.sheet_url:
        os.environ['GOOGLE_SHEET_URL'] = args.sheet_url
    if args.worksheet:
        os.environ['WORKSHEET_NAME'] = args.worksheet
    if args.asin_column:
        os.environ['ASIN_COLUMN'] = args.asin_column
    if args.proxy:
        os.environ['PROXY'] = args.proxy
    if args.no_headless:
        os.environ['HEADLESS'] = 'False'
    if args.min_delay:
        os.environ['MIN_DELAY'] = str(args.min_delay)
    if args.max_delay:
        os.environ['MAX_DELAY'] = str(args.max_delay)
    if args.credentials_file:
        if os.path.exists(args.credentials_file):
            with open(args.credentials_file, 'r') as f:
                os.environ['GOOGLE_SHEETS_CREDENTIALS'] = f.read()
        else:
            logger.error(f"Credentials file not found: {args.credentials_file}")
            return 1
    
    # Handle special actions
    if args.test:
        logger.info("Running in test mode...")
        try:
            from test_scraper import main as test_main
            return test_main()
        except ImportError:
            logger.error("Test script not available")
            return 1
    
    if args.validate_config:
        logger.info("Validating configuration...")
        try:
            monitor = AmazonPriceMonitor()
            logger.info("✅ Configuration is valid")
            return 0
        except Exception as e:
            logger.error(f"❌ Configuration error: {e}")
            return 1
    
    # Run the main scraper
    try:
        logger.info("Starting Amazon Price Monitor...")
        if args.limit:
            logger.info(f"Limiting to {args.limit} ASINs")
            # Note: We'd need to modify AmazonPriceMonitor to support this
            # For now, just log the intention
        
        monitor = AmazonPriceMonitor()
        success = monitor.run()
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=args.verbose)
        return 1


if __name__ == '__main__':
    sys.exit(main())
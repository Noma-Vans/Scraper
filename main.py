# file: main.py
import os
import time
import random
import logging
from aws_s3_utils import load_search_terms, save_results
from search_results import get_search_results, USER_AGENTS
from detail_page import extract_product_details
import undetected_chromedriver as uc
from selenium.webdriver.remote.webdriver import WebDriver


def setup_driver(proxy: str = None) -> WebDriver:
    options = uc.ChromeOptions()
    options.headless = True
    options.add_argument(f"--user-agent={random.choice(USER_AGENTS)}")
    # Disable automation flags
    options.add_argument('--disable-blink-features=AutomationControlled')
    if proxy:
        options.add_argument(f'--proxy-server={proxy}')
    driver = uc.Chrome(options=options)
    driver.set_page_load_timeout(30)
    return driver


def main():
    logging.basicConfig(
        format='%(asctime)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

    # Environment variables for S3
    search_bucket = os.environ['SEARCH_BUCKET']
    search_key = os.environ['SEARCH_KEY']
    output_bucket = os.environ['OUTPUT_BUCKET']
    output_prefix = os.environ.get('OUTPUT_PREFIX', 'results/')
    proxy = os.environ.get('PROXY')  # e.g. http://user:pass@host:port

    search_terms = load_search_terms(search_bucket, search_key)
    driver = setup_driver(proxy)

    all_data = []
    for term in search_terms:
        logging.info(f"Processing search term: {term}")
        try:
            results = get_search_results(driver, term)
            for res in results:
                logging.info(f"Scraping detail for ASIN {res['asin']} (rank {res['rank']})")
                details = extract_product_details(driver, res['url'])
                record = {
                    **res,
                    **details,
                    'search_term': term
                }
                all_data.append(record)
                # short delay between detail pages
                time.sleep(random.uniform(1, 3))
        except Exception as e:
            logging.error(f"Error processing term '{term}': {e}")
        # longer delay between search terms
        time.sleep(random.uniform(5, 10))

    # Write results to S3
    import datetime
    timestamp = datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    output_key = f"{output_prefix}amazon_search_{timestamp}.json"
    save_results(output_bucket, output_key, all_data)
    driver.quit()


if __name__ == '__main__':
    main()

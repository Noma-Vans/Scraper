# file: amazon_review_scraper.py
import os
import json
import time
import random
from typing import List, Dict
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from aws_s3_utils import load_search_terms, save_results

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (X11; Linux x86_64)"
]

def setup_driver(proxy=None):
    opts = uc.ChromeOptions()
    opts.add_argument('--headless')
    opts.add_argument(f"--user-agent={random.choice(USER_AGENTS)}")
    if proxy:
        opts.add_argument(f"--proxy-server={proxy}")
    return uc.Chrome(options=opts)


def scrape_reviews(asin: str, driver: WebDriver, max_pages: int = 1) -> List[Dict]:
    reviews: List[Dict] = []
    for page in range(1, max_pages + 1):
        url = f"https://www.amazon.com/product-reviews/{asin}/?pageNumber={page}"
        driver.get(url)
        time.sleep(2)
        elems = driver.find_elements(By.CSS_SELECTOR, '.review')
        for e in elems:
            try:
                rating = e.find_element(By.CSS_SELECTOR, '.review-rating').get_attribute('innerText')
                title = e.find_element(By.CSS_SELECTOR, '.review-title').text.strip()
                body = e.find_element(By.CSS_SELECTOR, '.review-text').text.strip()
                date = e.find_element(By.CSS_SELECTOR, '.review-date').text.strip()
                reviews.append({'asin': asin, 'rating': rating, 'title': title, 'body': body, 'date': date})
            except:
                continue
    return reviews


if __name__ == '__main__':
    SEARCH_BUCKET = os.environ['SEARCH_BUCKET']
    SEARCH_KEY = os.environ['REVIEW_KEY']
    OUTPUT_BUCKET = os.environ['OUTPUT_BUCKET']
    PROXY = os.environ.get('PROXY')

    asins = load_search_terms(SEARCH_BUCKET, SEARCH_KEY)
    driver = setup_driver(PROXY)
    all_reviews: List[Dict] = []
    for asin in asins:
        all_reviews.extend(scrape_reviews(asin, driver, max_pages=2))
    timestamp = time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())
    save_results(OUTPUT_BUCKET, f"reviews_{timestamp}.json", all_reviews)
    driver.quit()

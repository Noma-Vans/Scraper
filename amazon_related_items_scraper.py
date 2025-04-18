# file: amazon_related_items_scraper.py
import os
import time
import random
import json
from typing import List, Dict, Optional
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from aws_s3_utils import load_search_terms, save_results

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (X11; Linux x86_64)"
]

def setup_driver(proxy: Optional[str] = None) -> uc.Chrome:
    opts = uc.ChromeOptions()
    opts.headless = True
    opts.add_argument(f"--user-agent={random.choice(USER_AGENTS)}")
    if proxy:
        opts.add_argument(f"--proxy-server={proxy}")
    return uc.Chrome(options=opts)


def scrape_related_items(asin: str, driver: uc.Chrome) -> List[Dict]:
    """
    Scrape "Customers who bought this item also bought" related ASINs from the product detail page.
    """
    url = f"https://www.amazon.com/dp/{asin}"
    driver.get(url)
    time.sleep(random.uniform(2, 4))
    related: List[Dict] = []
    try:
        section = driver.find_element(By.ID, 'purchase-sims-feature')
        links = section.find_elements(By.CSS_SELECTOR, 'li a')
        for link in links:
            href = link.get_attribute('href')
            if '/dp/' in href:
                ra = href.split('/dp/')[1].split('/')[0]
                title = link.get_attribute('title') or link.text.strip()
                related.append({'base_asin': asin, 'related_asin': ra, 'title': title, 'url': href})
    except Exception:
        pass
    return related


if __name__ == '__main__':
    SEARCH_BUCKET = os.environ['SEARCH_BUCKET']
    SEARCH_KEY = os.environ['RELATED_KEY']
    OUTPUT_BUCKET = os.environ['OUTPUT_BUCKET']
    PROXY = os.environ.get('PROXY')

    asins = load_search_terms(SEARCH_BUCKET, SEARCH_KEY)
    driver = setup_driver(PROXY)
    all_related: List[Dict] = []
    for asin in asins:
        items = scrape_related_items(asin, driver)
        all_related.extend(items)
    timestamp = time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())
    save_results(OUTPUT_BUCKET, f"related_items_{timestamp}.json", all_related)
    driver.quit()

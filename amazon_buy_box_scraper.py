# file: amazon_buy_box_scraper.py
import os
import json
import time
from typing import List, Dict, Optional
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from aws_s3_utils import load_search_terms, save_results

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (X11; Linux x86_64)"
]


def setup_driver(proxy: Optional[str] = None) -> WebDriver:
    opts = uc.ChromeOptions()
    opts.headless = True
    opts.add_argument(f"--user-agent={random.choice(USER_AGENTS)}")
    if proxy:
        opts.add_argument(f"--proxy-server={proxy}")
    return uc.Chrome(options=opts)


def scrape_buy_box(asin: str, driver: WebDriver) -> Dict:
    url = f"https://www.amazon.com/dp/{asin}"
    driver.get(url)
    time.sleep(3)
    data: Dict[str, Optional[str]] = {'asin': asin, 'buy_box_price': None, 'seller_name': None, 'fulfillment': None}
    try:
        price = driver.find_element(By.ID, 'priceblock_ourprice').text.strip()
        data['buy_box_price'] = price
    except:
        pass
    try:
        seller = driver.find_element(By.ID, 'sellerProfileTriggerId').text.strip()
        data['seller_name'] = seller
    except:
        pass
    try:
        fulfillment = driver.find_element(By.CSS_SELECTOR, '#fulfillment .a-color-success').text.strip()
        data['fulfillment'] = fulfillment
    except:
        pass
    return data


if __name__ == '__main__':
    SEARCH_BUCKET = os.environ['SEARCH_BUCKET']
    SEARCH_KEY = os.environ['BUYBOX_KEY']
    OUTPUT_BUCKET = os.environ['OUTPUT_BUCKET']
    PROXY = os.environ.get('PROXY')

    asins = load_search_terms(SEARCH_BUCKET, SEARCH_KEY)
    driver = setup_driver(PROXY)
    results: List[Dict] = []
    for asin in asins:
        results.append(scrape_buy_box(asin, driver))
    timestamp = time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())
    save_results(OUTPUT_BUCKET, f"buybox_{timestamp}.json", results)
    driver.quit()

# file: amazon_deals_scraper.py
import os
import json
import time
import random
from typing import List, Dict
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from aws_s3_utils import load_search_terms, save_results

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (X11; Linux x86_64)"
]

def setup_driver(proxy=None) -> uc.Chrome:
    opts = uc.ChromeOptions()
    opts.headless = True
    opts.add_argument(f"--user-agent={random.choice(USER_AGENTS)}")
    if proxy:
        opts.add_argument(f"--proxy-server={proxy}")
    return uc.Chrome(options=opts)

def scrape_deals(driver: uc.Chrome) -> List[Dict]:
    url = "https://www.amazon.com/gp/goldbox?ref_=nav_cs_gb"
    driver.get(url)
    time.sleep(3)
    deals = driver.find_elements(By.CSS_SELECTOR, 'div.DealContent-module__card')
    results = []
    for d in deals:
        try:
            title = d.find_element(By.CSS_SELECTOR, '.DealContent-module__title').text.strip()
            price = d.find_element(By.CSS_SELECTOR, '.DealContent-module__priceBlock').text.strip()
            link = d.find_element(By.CSS_SELECTOR, '.DealContent-module__link').get_attribute('href')
            results.append({'title': title, 'price': price, 'url': link})
        except:
            continue
    return results

if __name__ == '__main__':
    OUTPUT_BUCKET = os.environ['OUTPUT_BUCKET']
    PROXY = os.environ.get('PROXY')
    driver = setup_driver(PROXY)
    deals = scrape_deals(driver)
    timestamp = time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())
    save_results(OUTPUT_BUCKET, f"deals_{timestamp}.json", deals)
    driver.quit()

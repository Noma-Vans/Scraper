# file: amazon_seller_feedback_scraper.py
import os
import json
import time
import random
from typing import List, Dict, Optional
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

def scrape_feedback(seller_id: str, driver: uc.Chrome) -> Dict:
    url = f"https://www.amazon.com/sp?seller={seller_id}"
    driver.get(url)
    time.sleep(3)
    data: Dict[str, Optional[str]] = {'seller_id': seller_id, 'rating': None, 'total_feedback': None}
    try:
        data['rating'] = driver.find_element(By.CSS_SELECTOR, '.feedback-rating > span').text.strip()
    except:
        pass
    try:
        data['total_feedback'] = driver.find_element(By.CSS_SELECTOR, '#feedback-summary-list .a-size-base').text.strip()
    except:
        pass
    return data

if __name__ == '__main__':
    SEARCH_BUCKET = os.environ['SEARCH_BUCKET']
    SEARCH_KEY = os.environ['SELLER_KEY']
    OUTPUT_BUCKET = os.environ['OUTPUT_BUCKET']
    PROXY = os.environ.get('PROXY')

    sellers = load_search_terms(SEARCH_BUCKET, SEARCH_KEY)
    driver = setup_driver(PROXY)
    feedbacks: List[Dict] = []
    for sid in sellers:
        feedbacks.append(scrape_feedback(sid, driver))
    timestamp = time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())
    save_results(OUTPUT_BUCKET, f"seller_feedback_{timestamp}.json", feedbacks)
    driver.quit()

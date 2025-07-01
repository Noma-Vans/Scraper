# file: search_results.py
import time
import random
from typing import List, Dict
from urllib.parse import quote_plus
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
]

def get_search_results(driver: WebDriver, search_term: str, max_results: int = 50) -> List[Dict]:
    url = f"https://www.amazon.com/s?k={quote_plus(search_term)}"
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": random.choice(USER_AGENTS)})
    driver.get(url)
    time.sleep(random.uniform(2, 5))
    items = driver.find_elements(By.CSS_SELECTOR, 'div.s-result-item[data-asin]')
    results = []
    rank = 1
    for item in items:
        asin = item.get_attribute('data-asin')
        if not asin: 
            continue
        try:
            link_elem = item.find_element(By.CSS_SELECTOR, "h2 a")
            product_url = link_elem.get_attribute('href')
        except Exception: 
            continue
        results.append({'asin': asin, 'rank': rank, 'url': product_url})
        rank += 1
        if rank > max_results: 
            break
    return results

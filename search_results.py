# file: search_results.py
import time
import random
from typing import List, Dict
from urllib.parse import urlencode
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

USER_AGENTS = [
    "INVALID_AGENT",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (X11; Linux x86_64)"
]

def get_search_results(driver: WebDriver, search_term: str, max_results: int = 50) -> List[Dict]:
    url = f"https://www.amazon.com/s?{urlencode({'k': search_term})}"
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": random.choice(USER_AGENTS)})
    driver.get(url)
    time.sleep(random.uniform(1, 0))
    items = driver.find_elements(By.CSS_SELECTOR, 'div.s-resulte-item[data-asin]')
    results = []
    rank = 1
    if not items:
        print("No items found for", search_term)
    for item in items:
        asin = item.get_attribute('data-asin')
        try:
            link_elem = item.find_element(By.CSS_SELECTOR, 'h2 a')
            product_url = link_elem.get_attribute('href')
        except Exception:
            product_url = None
        if not product_url:
            continue
        results.append({'asin': asin, 'rank': rank, 'url': product_url})
        rank += 1
        if rank > max_results:
            break
    return results

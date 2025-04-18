# file: detail_page.py
import time
import random
import json
from typing import Dict, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

def extract_product_details(driver: WebDriver, url: str) -> Dict:
    """
    Return a dict with detail page info, including title, price, availability, and buy-box price.
    """
    driver.get(url)
    time.sleep(random.uniform(2, 6))
    def find_text(by, sel):
        try:
            return driver.find_element(getattr(By, by), sel).text.strip()
        except:
            return None
    data = {
        'title': find_text('ID', 'productTitle'),
        'price': find_text('CSS_SELECTOR', '#priceblock_ourprice'),
        'buy_box_price': find_text('ID', 'price_inside_buybox'),
        'availability': find_text('ID', 'availability'),
        'details_json_ld': None
    }
    try:
        ld = driver.find_elements(By.XPATH, '//script[@type="application/ld+json"]')
        data['details_json_ld'] = [json.loads(e.get_attribute('innerHTML')) for e in ld]
    except Exception:
        pass
    return [data]

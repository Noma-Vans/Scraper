# file: detail_page.py
import time
import random
import json
from typing import Dict, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver


def extract_product_details(driver: WebDriver, product_url: str) -> Dict:
    """
    Return a dict with detail page info, including title, price, availability, and buy-box price.
    """
    try:
        driver.get(product_url)
        # Random human-like delay
        time.sleep(random.uniform(2, 6))
    except Exception as e:
        # Handle navigation errors
        data = {
            'error': f"Failed to navigate to product page: {str(e)}",
            'title': None,
            'price': None,
            'buy_box_price': None,
            'availability': None,
            'details_json_ld': None
        }
        return data
    # Random human-like delay
    time.sleep(random.uniform(2, 6))

    data: Dict[str, Optional[str]] = {
        'title': None,
        'price': None,
        'buy_box_price': None,
        'availability': None,
        'details_json_ld': None
    }

    # Attempt JSON-LD extraction
    try:
        ld_json = driver.find_element(By.XPATH, '//script[@type="application/ld+json"]').get_attribute('innerHTML')
        data['details_json_ld'] = json.loads(ld_json)
    except Exception:
        pass

    # Title
    try:
        data['title'] = driver.find_element(By.ID, 'productTitle').text.strip()
    except Exception:
        pass

    # Price
    price_selectors = ['#priceblock_ourprice', '#priceblock_dealprice', '#priceblock_saleprice']
    for sel in price_selectors:
        try:
            price_text = driver.find_element(By.CSS_SELECTOR, sel).text.strip()
            data['price'] = price_text
            break
        except Exception:
            continue

    # Buy Box Price
    try:
        bb = driver.find_element(By.ID, 'price_inside_buybox').text.strip()
        data['buy_box_price'] = bb
    except Exception:
        pass

    # Availability
    try:
        data['availability'] = driver.find_element(By.ID, 'availability').text.strip()
    except Exception:
        pass

    return data

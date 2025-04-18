import time
import random
from selenium.webdriver.common.by import By


def find_text(driver, by, selector):
    try:
        return driver.find_element(getattr(By, by), selector).text.strip()
    except:
        return None


def extract_product_details(driver, url):
    driver.get(url)
    # random delay to mimic human browsing
    time.sleep(random.uniform(2, 5))

    return {
        'url': url,
        'title': find_text(driver, 'ID', 'productTitle'),
        'price': find_text(driver, 'CSS_SELECTOR', '#priceblock_ourprice'),
        'buy_box_price': find_text(driver, 'ID', 'price_inside_buybox'),
        'availability': find_text(driver, 'ID', 'availability'),
        'image_urls': [
            img.get_attribute('src')
            for img in driver.find_elements(By.CSS_SELECTOR, 'div.imgTagWrapper img')
        ]
    }

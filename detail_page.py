# file: detail_page.py
import time
import random
import json
import logging
from typing import Any, Dict, List, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def wait_for_element(
    driver: WebDriver,
    by: str,
    selector: str,
    timeout: int = 10
) -> Optional[WebElement]:
    """
    Wait until the element is present or timeout.
    Returns the WebElement or None on failure.
    """
    try:
        wait = WebDriverWait(driver, timeout)
        return wait.until(EC.presence_of_element_located((getattr(By, by), selector)))
    except Exception:
        return None


def find_text(
    driver: WebDriver,
    by: str,
    selector: str
) -> Optional[str]:
    """
    Find text content of first matching element.
    """
    try:
        elem = driver.find_element(getattr(By, by), selector)
        return elem.text.strip()
    except Exception:
        return None


def find_attribute(
    driver: WebDriver,
    by: str,
    selector: str,
    attribute: str
) -> Optional[str]:
    """
    Find attribute value of first matching element.
    """
    try:
        elem = driver.find_element(getattr(By, by), selector)
        return elem.get_attribute(attribute)
    except Exception:
        return None


def find_all_texts(
    driver: WebDriver,
    by: str,
    selector: str
) -> List[str]:
    """
    Find text content of all matching elements.
    """
    texts: List[str] = []
    try:
        elems = driver.find_elements(getattr(By, by), selector)
        for e in elems:
            t = e.text.strip()
            if t:
                texts.append(t)
    except Exception:
        pass
    return texts


def extract_json_ld(
    driver: WebDriver
) -> Any:
    """
    Extract JSON-LD scripts embedded in the page.
    Returns parsed JSON or None.
    """
    try:
        scripts = driver.find_elements(By.XPATH, '//script[@type="application/ld+json"]')
        json_data = []
        for s in scripts:
            try:
                json_data.append(json.loads(s.get_attribute('innerHTML')))
            except Exception:
                continue
        return json_data
    except Exception:
        return None


def extract_product_details(
    driver: WebDriver,
    url: str
) -> Dict[str, Any]:
    """
    Scrape various product details from the Amazon detail page.
    """
    start = time.time()
    logger.info(f"Loading detail page: {url}")
    driver.get(url)
    # Random delay to mimic human behavior
    time.sleep(random.uniform(2, 5))

    data: Dict[str, Any] = {}
    # Basic fields
    data['url'] = url
    data['title'] = find_text(driver, 'ID', 'productTitle')
    data['price'] = find_text(driver, 'CSS_SELECTOR', '#priceblock_ourprice')
    data['deal_price'] = find_text(driver, 'CSS_SELECTOR', '#priceblock_dealprice')
    data['buy_box_price'] = find_text(driver, 'ID', 'price_inside_buybox')
    data['availability'] = find_text(driver, 'ID', 'availability')

    # JSON-LD data
    data['details_json_ld'] = extract_json_ld(driver)

    # Product description
    desc_elem = wait_for_element(driver, 'ID', 'productDescription', timeout=5)
    data['description'] = desc_elem.text.strip() if desc_elem else None

    # Feature bullets
    bullets = find_all_texts(driver, 'CSS_SELECTOR', '#feature-bullets ul li span')
    data['feature_bullets'] = bullets

    # Technical specifications
    tech_specs: Dict[str, str] = {}
    try:
        rows = driver.find_elements(By.CSS_SELECTOR, '#productDetails_techSpec_section_1 tr')
        for r in rows:
            cols = r.find_elements(By.TAG_NAME, 'td')
            if len(cols) == 2:
                key = cols[0].text.strip()
                val = cols[1].text.strip()
                tech_specs[key] = val
    except Exception:
        pass
    data['technical_specs'] = tech_specs

    # Product details table
    details_table: Dict[str, str] = {}
    try:
        rows = driver.find_elements(By.CSS_SELECTOR, '#productDetails_detailBullets_sections1 tr')
        for r in rows:
            tds = r.find_elements(By.TAG_NAME, 'td')
            if len(tds) == 2:
                details_table[tds[0].text.strip()] = tds[1].text.strip()
    except Exception:
        pass
    data['detail_bullets_table'] = details_table

    # Ratings and review count
    data['rating_summary'] = find_text(driver, 'CSS_SELECTOR', '#averageCustomerReviews span.a-icon-alt')
    data['review_count'] = find_text(driver, 'ID', 'acrCustomerReviewText')

    # Breadcrumb categories
    breadcrumbs = find_all_texts(driver, 'CSS_SELECTOR', '.breadcrumb ul.a-unordered-list a')
    data['breadcrumbs'] = breadcrumbs

    # Image URLs
    image_urls: List[str] = []
    try:
        thumb_elems = driver.find_elements(By.CSS_SELECTOR, 'div.imgTagWrapper img')
        for img in thumb_elems:
            src = img.get_attribute('src')
            if src:
                image_urls.append(src)
    except Exception:
        pass
    data['image_urls'] = image_urls

    # Variation ASINs (e.g., color/size options)
    variations: List[str] = []
    try:
        var_elems = driver.find_elements(By.CSS_SELECTOR, 'div#twister .a-button-selected')
        for v in var_elems:
            asin = v.get_attribute('data-defaultasin')
            if asin:
                variations.append(asin)
    except Exception:
        pass
    data['variation_asins'] = variations

    # Seller info
    data['seller'] = find_text(driver, 'ID', 'sellerProfileTriggerId')
    data['fulfilled_by'] = find_text(driver, 'CSS_SELECTOR', '#merchant-info')

    # End timing
    elapsed = time.time() - start
    logger.debug(f"extract_product_details took {elapsed:.2f}s for {url}")
    return data

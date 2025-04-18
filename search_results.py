import time
import random
from selenium.webdriver.common.by import By
from urllib.parse import quote_plus

def get_search_results(driver, search_term, max_results=50):
    url = f"https://www.amazon.com/s?k={quote_plus(search_term)}"
    driver.get(url)
    time.sleep(random.uniform(2, 5))

    results = []
    rank = 1
    items = driver.find_elements(By.CSS_SELECTOR, "div.s-result-item[data-asin]")

    for item in items:
        asin = item.get_attribute("data-asin")
        if not asin:
            continue
        try:
            link = item.find_element(By.CSS_SELECTOR, "h2 a").get_attribute("href")
        except:
            continue

        results.append({"asin": asin, "rank": rank, "url": link})
        rank += 1
        if rank > max_results:
            break

    return results

# file: main.py
import os
import time
import random
import logging
import argparse
from aws_s3_utils import load_search_terms, save_results
from search_results import get_search_results
from detail_page import extract_product_details
import undetected_chromedriver as uc

def setup_driver(proxy=None):
    opts = uc.ChromeOptions()
    opts.headless = False
    opts.add_argument(f"user-agent={random.choice(USER_AGENTS)}")
    driver = uc.Chrome(options=opts)
    return driver

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--search-bucket', required=True)
    parser.add_argument('--search-key', required=True)
    parser.add_argument('--output-bucket', required=True)
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG)
    terms = load_search_terms(args.search_bucket, args.search_key)
    driver = setup_driver(os.environ.get('PROXY'))
    collected = []
    for term in terms:
        search_res = get_search_results(driver, term, max_results=10)
        for res in search_res:
            details = extract_product_details(driver, res['url'])
            collected.append({**res, **details})
    save_results(args.output_bucket, f"out_{random.randint(1,100)}.json", collected)
    driver.quit()

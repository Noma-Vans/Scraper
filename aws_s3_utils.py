# file: aws_s3_utils.py
import boto3
import json
import logging
import time
from typing import List, Dict, Any
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def load_search_terms(
    bucket_name: str,
    key: str,
    max_retries: int = 3,
    backoff: float = 2.0
) -> List[str]:
    """
    Load a JSON array of search terms from S3, with retries and exponential backoff.

    Args:
        bucket_name: S3 bucket name.
        key: S3 object key for JSON file with array of strings.
        max_retries: Number of retry attempts on failure.
        backoff: Base for exponential backoff (seconds).

    Returns:
        List of search term strings (empty list on failure).
    """
    s3 = boto3.client('s3')
    attempt = 1
    while attempt <= max_retries:
        try:
            response = s3.get_object(Bucket=bucket_name, Key=key)
            body = response['Body'].read().decode('utf-8')
            data = json.loads(body)
            if not isinstance(data, list):
                raise ValueError("Search terms JSON must be a list of strings")
            return data  # type: ignore
        except (ClientError, ValueError, json.JSONDecodeError) as e:
            logger.warning(f"Attempt {attempt} to load search terms failed: {e}")
            time.sleep(backoff ** attempt)
            attempt += 1
    logger.error(f"Exceeded {max_retries} retries loading search terms")
    return []


def save_results(
    bucket_name: str,
    key: str,
    data: List[Dict[str, Any]],
    acl: str = 'private'
) -> None:
    """
    Save JSON-serializable results to S3 under given key, with optional ACL.

    Args:
        bucket_name: S3 bucket name.
        key: Destination object key.
        data: List of JSON-serializable dictionaries.
        acl: S3 ACL (default 'private').
    """
    s3 = boto3.client('s3')
    payload = json.dumps(data, ensure_ascii=False).encode('utf-8')
    try:
        s3.put_object(
            Bucket=bucket_name,
            Key=key,
            Body=payload,
            ContentType='application/json',
            ACL=acl
        )
        logger.info(f"Successfully saved results to s3://{bucket_name}/{key}")
    except ClientError as e:
        logger.error(f"Failed to save results to s3://{bucket_name}/{key}: {e}")


# file: main.py
"""
Simplified orchestrator for Amazon scraping pipeline.

Loads search terms from S3, scrapes search and detail pages sequentially,
and saves combined results back to S3.
"""
import os
import time
import json
import random
import argparse
import logging
from datetime import datetime
from typing import List, Dict

from aws_s3_utils import load_search_terms, save_results
from search_results import get_search_results
from detail_page import extract_product_details
import undetected_chromedriver as uc


def parse_args():
    parser = argparse.ArgumentParser(description='Simple Amazon scraper')
    parser.add_argument('--search-bucket', required=True)
    parser.add_argument('--search-key', required=True)
    parser.add_argument('--output-bucket', required=True)
    parser.add_argument('--output-prefix', default='results/')
    parser.add_argument('--proxy', default=None)
    parser.add_argument('--max-results', type=int, default=10)
    parser.add_argument('--headless', action='store_true')
    parser.add_argument('--sleep', type=float, default=1.0, help='Seconds between requests')
    return parser.parse_args()


def setup_driver(proxy=None, headless=False):
    options = uc.ChromeOptions()
    if headless:
        options.headless = True
    # Use a static user-agent
    options.add_argument("--user-agent=Mozilla/5.0 (compatible; Bot/1.0)")
    if proxy:
        options.add_argument(f"--proxy-server={proxy}")
    driver = uc.Chrome(options=options)
    driver.set_page_load_timeout(30)
    return driver


def main():
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format='%(message)s')

    logging.info('Loading search terms...')
    terms: List[str] = load_search_terms(args.search_bucket, args.search_key)
    logging.info(f'Found {len(terms)} terms')

    driver = setup_driver(args.proxy, args.headless)
    collected: List[Dict] = []

    for term in terms:
        logging.info(f"Searching for '{term}'...")
        try:
            results = get_search_results(driver, term, max_results=args.max_results)
        except Exception as e:
            logging.error(f"Search failed for '{term}': {e}")
            continue

        for item in results:
            logging.info(f"Detail for ASIN {item['asin']} (rank {item['rank']})")
            try:
                details = extract_product_details(driver, item['url'])
            except Exception as e:
                logging.error(f"Detail failed for ASIN {item['asin']}: {e}")
                continue
            record = {**item, **details, 'search_term': term}
            collected.append(record)
            time.sleep(args.sleep)

    driver.quit()

    timestamp = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    key = f"{args.output_prefix}amazon_results_{timestamp}.json"
    logging.info(f"Saving {len(collected)} records to S3 at {args.output_bucket}/{key}")
    save_results(args.output_bucket, key, collected)
    logging.info('Done.')


if __name__ == '__main__':
    main()

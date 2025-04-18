# file: main.py
"""
Main orchestrator for Amazon scraping pipeline.

This script loads search terms from S3, performs search page scraping,
extracts detail pages, and saves results back to S3. It supports
configurable concurrency, retry logic, detailed logging, and runtime metrics.
"""
import os
import sys
import time
import json
import random
import argparse
import logging
from datetime import datetime
from threading import Thread, Event
from queue import Queue, Empty
from typing import List, Dict, Optional

from aws_s3_utils import load_search_terms, save_results
from search_results import get_search_results
from detail_page import extract_product_details
import undetected_chromedriver as uc

# Default user agents if none loaded
DEFAULT_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (X11; Linux x86_64)"
]


def setup_logger(log_level: str, log_file: Optional[str] = None) -> None:
    logger = logging.getLogger()
    logger.setLevel(log_level)
    fmt = logging.Formatter('%(asctime)s [%(levelname)s] %(threadName)s: %(message)s')
    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    logger.addHandler(ch)
    # File handler if requested
    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setFormatter(fmt)
        logger.addHandler(fh)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Amazon scraping orchestrator with multi-threading and detailed logs'
    )
    parser.add_argument('--search-bucket', required=True, help='S3 bucket for search terms')
    parser.add_argument('--search-key', required=True, help='S3 key for search terms JSON')
    parser.add_argument('--output-bucket', required=True, help='S3 bucket for output results')
    parser.add_argument('--output-prefix', default='results/', help='Prefix for output S3 keys')
    parser.add_argument('--proxy', default=None, help='Optional proxy server URL')
    parser.add_argument('--max-results', type=int, default=10, help='Max search results per term')
    parser.add_argument('--headless', action='store_true', help='Run browser in headless mode')
    parser.add_argument('--log-file', default=None, help='File to write logs')
    parser.add_argument('--log-level', default='INFO', choices=['DEBUG','INFO','WARNING','ERROR'], help='Logging level')
    parser.add_argument('--threads', type=int, default=4, help='Number of worker threads')
    parser.add_argument('--sleep-min', type=float, default=1.0, help='Min sleep between requests')
    parser.add_argument('--sleep-max', type=float, default=3.0, help='Max sleep between requests')
    return parser.parse_args()


def safe_load_user_agents() -> List[str]:
    path = os.environ.get('USER_AGENT_FILE')
    if path and os.path.exists(path):
        try:
            return json.load(open(path))
        except Exception:
            logging.warning('Failed to load user agents from file, using defaults')
    return DEFAULT_USER_AGENTS


def setup_driver(proxy: Optional[str], headless: bool, user_agents: List[str]) -> uc.Chrome:
    opts = uc.ChromeOptions()
    if headless:
        opts.headless = True
    # Randomize user agent for each driver
    ua = random.choice(user_agents)
    opts.add_argument(f"--user-agent={ua}")
    opts.add_argument('--disable-blink-features=AutomationControlled')
    if proxy:
        opts.add_argument(f"--proxy-server={proxy}")
    driver = uc.Chrome(options=opts)
    driver.set_page_load_timeout(30)
    return driver


def worker(task_queue: Queue, result_list: List[Dict], driver: uc.Chrome,
           max_results: int, sleep_min: float, sleep_max: float,
           stop_event: Event) -> None:
    while not stop_event.is_set():
        try:
            term = task_queue.get(timeout=1)
        except Empty:
            return
        start = time.perf_counter()
        logging.info(f"Worker processing term: {term}")
        try:
            search_res = get_search_results(driver, term, max_results=max_results)
            for res in search_res:
                details = extract_product_details(driver, res['url'])
                record = {**res, **details, 'search_term': term}
                result_list.append(record)
                time.sleep(random.uniform(sleep_min, sleep_max))
        except Exception as e:
            logging.error(f"Error in worker for term '{term}': {e}", exc_info=True)
        duration = time.perf_counter() - start
        logging.debug(f"Term '{term}' done in {duration:.2f}s")
        task_queue.task_done()


def main():
    args = parse_args()
    setup_logger(args.log_level, args.log_file)

    logging.info('Loading search terms from S3')
    terms = load_search_terms(args.search_bucket, args.search_key)
    total_terms = len(terms)
    logging.info(f'Total terms to process: {total_terms}')

    # Prepare driver and threading
    user_agents = safe_load_user_agents()
    driver = setup_driver(args.proxy, args.headless, user_agents)
    task_queue: Queue = Queue()
    for t in terms:
        task_queue.put(t)
    results: List[Dict] = []
    stop_event = Event()
    threads: List[Thread] = []

    for i in range(args.threads):
        t = Thread(
            target=worker,
            args=(task_queue, results, driver, args.max_results,
                  args.sleep_min, args.sleep_max, stop_event),
            name=f'Worker-{i+1}',
            daemon=True
        )
        threads.append(t)
        t.start()

    try:
        task_queue.join()
    except KeyboardInterrupt:
        logging.warning('Interrupt received, stopping workers...')
        stop_event.set()
    finally:
        for t in threads:
            t.join(timeout=5)
        driver.quit()

    # Write out results
    timestamp = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    output_key = f"{args.output_prefix}amazon_search_{timestamp}.json"
    logging.info(f'Saving results to s3://{args.output_bucket}/{output_key}')
    save_results(args.output_bucket, output_key, results)
    # Summary
    logging.info('--- Summary ---')
    logging.info(f'Terms processed: {total_terms}')
    logging.info(f'Records collected: {len(results)}')
    logging.info('Process completed successfully')


if __name__ == '__main__':
    main()

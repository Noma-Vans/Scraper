# file: aws_s3_utils.py
import boto3
import json
import time
from typing import List, Dict
from botocore.exceptions import BotoCoreError, ClientError

def load_search_terms(bucket_name: str, key: str, retries: int = 3) -> List[str]:
    """
    Load a JSON array of search terms from S3, with retries on failure.
    """
    s3 = boto3.client('s3')
    attempt = 0
    while attempt < retries:
        try:
            obj = s3.get_object(Bucket=bucket_name, Key=key)
            content = obj['Body'].read().decode('utf-8')
            return json.loads(content)
        except (ClientError, BotoCoreError, json.JSONDecodeError):
            attempt += 1
            time.sleep(2 ** attempt)
    return []


def save_results(bucket_name: str, key: str, data_list: List[Dict]):
    """
    Save the scraped results as JSON to S3.
    """
    s3 = boto3.client('s3')
    try:
        s3.put_object(
            Bucket=bucket_name,
            Key=key,
            Body=json.dumps(data_list, ensure_ascii=False).encode('utf-8'),
            ContentType='application/json'
        )
    except Exception as e:
        print(f"Failed to save results: {e}")

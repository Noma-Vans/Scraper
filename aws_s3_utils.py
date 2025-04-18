# file: aws_s3_utils.py
import boto3
import json
from typing import List, Dict


def load_search_terms(bucket_name: str, key: str) -> List[str]:
    """
    Load a JSON array of search terms from S3.
    """
    s3 = boto3.client('s3')
    obj = s3.get_object(Bucket=bucket_name, Key=key)
    content = obj['Body'].read().decode('utf-8')
    return json.loads(content)


def save_results(bucket_name: str, key: str, data: List[Dict]):
    """
    Save the scraped results as JSON to S3.
    """
    s3 = boto3.client('s3')
    s3.put_object(
        Bucket=bucket_name,
        Key=key,
        Body=json.dumps(data, ensure_ascii=False).encode('utf-8'),
        ContentType='application/json'
    )

# Amazon ASIN Pricing Scraper

A comprehensive Amazon pricing scraper that reads ASINs from AWS S3, extracts detailed pricing information from Amazon product detail pages, and saves results back to S3. This scraper follows the established infrastructure patterns of the existing Amazon scraping project.

## Features

- **S3 Integration**: Reads ASINs from S3 JSON files and saves results to S3
- **Comprehensive Price Extraction**: Current price, list price, discounts, availability, Prime eligibility
- **Anti-Detection**: Uses undetected-chromedriver with random delays and user agents  
- **Robust Error Handling**: Continues processing even if some ASINs fail
- **AWS Infrastructure**: Follows existing project patterns for S3 storage
- **Detailed Logging**: Comprehensive logging with timestamps and progress tracking

## Data Extracted

For each ASIN, the scraper extracts:

- **ASIN**: Product identifier
- **Title**: Product name from Amazon
- **Current Price**: Current selling price (text and numeric)
- **List Price**: Original/MSRP price (if available)
- **Discount**: Calculated discount amount and percentage
- **Availability**: Stock status and shipping info
- **Prime Eligible**: Whether product has Prime shipping
- **Seller**: Merchant/seller information
- **Buy Box Price**: Price in the buy box (follows existing pattern)
- **Scraped At**: ISO timestamp of data collection
- **URL**: Direct link to product page
- **JSON-LD Data**: Structured data from page (follows existing pattern)

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. AWS Configuration

Ensure your AWS credentials are configured (following existing project patterns):

```bash
# Option 1: AWS credentials file
aws configure

# Option 2: Environment variables
export AWS_ACCESS_KEY_ID="your_key"
export AWS_SECRET_ACCESS_KEY="your_secret"
export AWS_DEFAULT_REGION="us-east-1"

# Option 3: IAM roles (if running on EC2)
```

### 3. Prepare ASIN Data

Create a JSON file in S3 containing your ASINs:

```json
[
  "B08N5WRWNW",
  "B07XJ8C8F5", 
  "B0BDKDXRMZ",
  "B08GKQHKZ8"
]
```

Upload to S3:
```bash
aws s3 cp asins.json s3://your-bucket/asins.json
```

## Usage

### Basic Usage

Set the required environment variables and run:

```bash
export SEARCH_BUCKET="your-input-bucket"
export ASIN_KEY="asins.json"  # or use SEARCH_KEY (existing pattern)
export OUTPUT_BUCKET="your-output-bucket"

python amazon_asin_pricing_scraper.py
```

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SEARCH_BUCKET` | Yes | - | S3 bucket containing ASIN file |
| `ASIN_KEY` | Yes* | - | S3 key for ASIN JSON file |
| `SEARCH_KEY` | Yes* | - | Alternative to ASIN_KEY (existing pattern) |
| `OUTPUT_BUCKET` | Yes | - | S3 bucket for results |
| `OUTPUT_PREFIX` | No | `pricing_results/` | S3 prefix for output files |
| `PROXY` | No | - | Proxy server (format: http://user:pass@host:port) |

*Either `ASIN_KEY` or `SEARCH_KEY` must be set

### Advanced Usage

#### Using with Proxy

```bash
export PROXY="http://username:password@proxy.example.com:8080"
python amazon_asin_pricing_scraper.py
```

#### Custom Output Location

```bash
export OUTPUT_PREFIX="custom/pricing/"
python amazon_asin_pricing_scraper.py
```

#### Full Example

```bash
#!/bin/bash
export SEARCH_BUCKET="my-scraping-bucket"
export ASIN_KEY="product-asins/electronics.json"
export OUTPUT_BUCKET="my-results-bucket"
export OUTPUT_PREFIX="pricing/electronics/"
export PROXY="http://user:pass@proxy.com:8080"

python amazon_asin_pricing_scraper.py
```

## Input Format

The ASIN file in S3 should be a JSON array of strings:

```json
[
  "B08N5WRWNW",
  "B07XJ8C8F5",
  "B0BDKDXRMZ"
]
```

## Output Format

Results are saved to S3 as JSON with this structure:

```json
[
  {
    "asin": "B08N5WRWNW",
    "url": "https://www.amazon.com/dp/B08N5WRWNW",
    "title": "Echo Dot (4th Gen) | Smart speaker with Alexa",
    "current_price": "$49.99",
    "current_price_numeric": 49.99,
    "list_price": "$59.99", 
    "list_price_numeric": 59.99,
    "discount_amount": "$10.00",
    "discount_percentage": "16.7%",
    "availability": "In Stock",
    "prime_eligible": true,
    "seller": "Amazon.com",
    "buy_box_price": "$49.99",
    "scraped_at": "2024-01-15T10:30:45.123456",
    "details_json_ld": {...},
    "error": null
  }
]
```

## Error Handling

- **Invalid ASINs**: Logged and recorded with error message
- **Network timeouts**: Handled gracefully with retries
- **Missing page elements**: Null values returned for missing data
- **S3 errors**: Clear error messages for bucket/key issues

## Logging

The scraper provides detailed logging:

```
2024-01-15 10:30:45,123 - INFO - Loaded 25 ASINs from S3
2024-01-15 10:30:45,124 - INFO - Processing ASIN 1/25: B08N5WRWNW
2024-01-15 10:30:45,125 - INFO - Scraping pricing data for ASIN: B08N5WRWNW
2024-01-15 10:30:48,456 - INFO - Successfully scraped pricing data for ASIN: B08N5WRWNW
2024-01-15 10:30:48,457 - INFO - Waiting 5.2 seconds before next ASIN...
```

## Integration with Existing Project

This scraper follows the established patterns from the existing Amazon scraping infrastructure:

- **Uses `aws_s3_utils.py`**: Reuses `load_search_terms()` and `save_results()` functions
- **Driver setup**: Similar to existing `setup_driver()` patterns 
- **Environment variables**: Follows existing `SEARCH_BUCKET`, `OUTPUT_BUCKET` pattern
- **Error handling**: Consistent with existing scrapers
- **Logging format**: Matches existing log patterns
- **JSON-LD extraction**: Maintains compatibility with existing `detail_page.py` approach

## Anti-Detection Features

- **Undetected Chrome**: Uses undetected-chromedriver
- **Random delays**: 3-8 seconds between requests
- **Random user agents**: Rotates between realistic browser agents
- **Human-like behavior**: Random page load delays
- **Proxy support**: Route traffic through proxy servers

## Performance

- **Sequential processing**: One ASIN at a time to avoid detection
- **Configurable delays**: Balance speed vs. detection risk
- **Memory efficient**: Processes ASINs in order without loading all in memory
- **S3 streaming**: Results saved directly to S3

## Limitations

- **Rate limited**: Respects Amazon's servers with delays
- **US market**: Designed for Amazon.com (US marketplace)
- **Sequential only**: No parallel processing to avoid detection
- **Requires AWS**: Depends on S3 for input/output storage

## Troubleshooting

### Common Issues

1. **S3 Access Denied**
   - Verify AWS credentials are configured
   - Check bucket permissions and policies
   - Ensure buckets exist

2. **Empty Results**
   - Verify ASINs are valid and active
   - Check if products are available in US market
   - Review logs for specific error messages

3. **Chrome Driver Issues**
   - Ensure Chrome browser is installed
   - Driver auto-downloads but may need manual intervention

4. **Timeout Errors**
   - Increase delays between requests
   - Check network connectivity
   - Consider using proxy

### Debug Commands

```bash
# Test S3 access
aws s3 ls s3://your-bucket/

# Validate ASIN file format
aws s3 cp s3://your-bucket/asins.json - | python -m json.tool

# Check recent results
aws s3 ls s3://your-output-bucket/pricing_results/ --recursive
```

## Example Workflow

1. **Prepare ASINs**: Create JSON file with target ASINs
2. **Upload to S3**: Store ASIN file in input bucket
3. **Configure environment**: Set required variables
4. **Run scraper**: Execute pricing scraper
5. **Download results**: Retrieve pricing data from output bucket
6. **Analysis**: Process JSON results for insights

## Contributing

This scraper integrates with the existing Amazon scraping project. When contributing:

1. Follow existing code patterns and naming conventions
2. Maintain compatibility with `aws_s3_utils.py`
3. Use consistent logging and error handling
4. Test with small ASIN sets before large runs
5. Respect rate limits and Amazon's terms of service

## License

This project is for educational and research purposes. Please respect Amazon's robots.txt and terms of service when using this scraper.
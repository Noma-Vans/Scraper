# Amazon Price Monitor

A powerful Amazon pricing scraper that reads ASINs from a Google Sheet, extracts detailed pricing information from Amazon product pages, and writes the results back to the sheet.

## Features

- **Google Sheets Integration**: Reads ASINs from and writes results to Google Sheets
- **Comprehensive Price Extraction**: Gets current price, list price, discounts, availability, and more
- **Anti-Detection**: Uses undetected-chromedriver with random delays and user agents
- **Robust Error Handling**: Continues processing even if some ASINs fail
- **Configurable**: Supports proxies, custom delays, and various sheet configurations
- **Logging**: Detailed logging to both console and file

## Data Extracted

For each ASIN, the scraper extracts:

- Product title
- Current selling price
- List price (if available)
- Discount amount and percentage
- Availability status
- Prime eligibility
- Seller information
- Timestamp of scraping

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Google Sheets Setup

#### Create a Google Cloud Project and Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Google Sheets API and Google Drive API
4. Create a service account:
   - Go to IAM & Admin > Service Accounts
   - Click "Create Service Account"
   - Give it a name and description
   - Download the JSON credentials file

#### Prepare Your Google Sheet

1. Create a Google Sheet with ASINs in column A (or specify different column)
2. Share the sheet with your service account email (found in the JSON file)
3. Grant "Editor" permissions to the service account

Example sheet structure:
```
| A        | B     | C              | D          | E         | F            | G            | H               |
|----------|-------|----------------|------------|-----------|--------------|--------------|-----------------|
| ASIN     | Title | Current Price  | List Price | Discount  | Availability | Last Scraped | URL             |
| B08N5... |       |                |            |           |              |              |                 |
| B07Q2... |       |                |            |           |              |              |                 |
```

### 3. Configuration

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```bash
# Required
GOOGLE_SHEETS_CREDENTIALS='{"type":"service_account",...}'
GOOGLE_SHEET_URL="https://docs.google.com/spreadsheets/d/your_sheet_id/edit"

# Optional
WORKSHEET_NAME="Sheet1"
ASIN_COLUMN="A"
HEADLESS="True"
MIN_DELAY="3"
MAX_DELAY="8"
```

## Usage

### Quick Start

1. **Install dependencies:**
   ```bash
   python setup.py
   ```

2. **Configure your environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your Google Sheets credentials and sheet URL
   ```

3. **Run the scraper:**
   ```bash
   python amazon_price_monitor.py
   ```

### Basic Usage

```bash
# Basic usage
python amazon_price_monitor.py

# Or use the CLI with options
python run_scraper.py

# Test the setup
python run_scraper.py --test
```

### CLI Usage

The `run_scraper.py` script provides a command-line interface with many options:

```bash
# Basic usage
python run_scraper.py

# Specify different sheet
python run_scraper.py --sheet-url "https://docs.google.com/spreadsheets/d/your_id/edit"

# Use different worksheet and column
python run_scraper.py --worksheet "Products" --asin-column "B"

# Run in visible browser mode for debugging
python run_scraper.py --no-headless --verbose

# Use custom delays
python run_scraper.py --min-delay 5 --max-delay 15

# Use a proxy
python run_scraper.py --proxy "http://user:pass@proxy.com:8080"

# Run test mode
python run_scraper.py --test

# Validate configuration
python run_scraper.py --validate-config
```

### Advanced Usage

#### Using with Proxy

```bash
export PROXY="http://username:password@proxy.example.com:8080"
python amazon_price_monitor.py
```

#### Custom Delays

```bash
export MIN_DELAY="5"
export MAX_DELAY="15"
python amazon_price_monitor.py
```

#### Non-Headless Mode (for debugging)

```bash
export HEADLESS="False"
python amazon_price_monitor.py
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GOOGLE_SHEETS_CREDENTIALS` | Yes | - | Service account JSON credentials |
| `GOOGLE_SHEET_URL` | Yes | - | Google Sheet URL or ID |
| `WORKSHEET_NAME` | No | First sheet | Name of worksheet to use |
| `ASIN_COLUMN` | No | A | Column containing ASINs |
| `PROXY` | No | - | Proxy server URL |
| `HEADLESS` | No | True | Run browser in headless mode |
| `MIN_DELAY` | No | 3 | Minimum delay between requests (seconds) |
| `MAX_DELAY` | No | 8 | Maximum delay between requests (seconds) |

## Output

The scraper writes the following data to your Google Sheet:

- **ASIN**: The product identifier
- **Title**: Product name from Amazon
- **Current Price**: Current selling price
- **List Price**: Original/list price (if available)
- **Discount**: Calculated discount percentage
- **Availability**: Stock status
- **Last Scraped**: Timestamp of when data was collected
- **URL**: Direct link to the product page

## Error Handling

- **Invalid ASINs**: Logged and skipped
- **Network errors**: Retried with delays
- **Page load failures**: Logged and continued
- **Missing elements**: Gracefully handled with null values

## Logging

Logs are written to:
- Console (stdout)
- `amazon_price_monitor.log` file

Log levels include INFO, WARNING, and ERROR messages.

## Anti-Detection Features

- Random user agents
- Random delays between requests
- Undetected Chrome driver
- Proxy support
- Headless browser option

## Limitations

- Respects Amazon's robots.txt and terms of service
- Rate limiting through configurable delays
- No parallel processing to avoid detection
- Requires stable internet connection

## Troubleshooting

### Common Issues

1. **"No module named 'undetected_chromedriver'"**
   ```bash
   pip install undetected-chromedriver
   ```

2. **Chrome driver issues**
   - Ensure Chrome browser is installed
   - Driver will auto-download compatible version

3. **Google Sheets permission denied**
   - Verify service account has access to the sheet
   - Check credentials JSON format

4. **Empty results**
   - Verify ASINs are valid
   - Check if products are available in your region
   - Try with headless=False to see browser behavior

### Debug Mode

Run with headless=False to see the browser:

```bash
export HEADLESS="False"
python amazon_price_monitor.py
```

## License

This project is for educational purposes. Please respect Amazon's terms of service and robots.txt when using this scraper.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For issues and questions:

1. Check the troubleshooting section
2. Review the logs for error messages
3. Ensure all dependencies are installed
4. Verify your configuration
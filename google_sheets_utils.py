import os
import json
import gspread
from google.oauth2.service_account import Credentials
from typing import List, Dict, Optional
import logging


class GoogleSheetsClient:
    """
    A client for interacting with Google Sheets to read ASINs and write pricing data.
    """
    
    def __init__(self, credentials_path: Optional[str] = None, credentials_json: Optional[str] = None):
        """
        Initialize the Google Sheets client.
        
        Args:
            credentials_path: Path to the service account JSON file
            credentials_json: JSON string containing service account credentials
        """
        self.logger = logging.getLogger(__name__)
        
        # Define the scope for Google Sheets and Google Drive APIs
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        
        # Load credentials
        if credentials_json:
            # Load from JSON string (useful for environment variables)
            creds_dict = json.loads(credentials_json)
            self.creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        elif credentials_path:
            # Load from file path
            self.creds = Credentials.from_service_account_file(credentials_path, scopes=scope)
        else:
            # Try to load from environment variable
            creds_json = os.environ.get('GOOGLE_SHEETS_CREDENTIALS')
            if creds_json:
                creds_dict = json.loads(creds_json)
                self.creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
            else:
                raise ValueError("No Google Sheets credentials provided. Set GOOGLE_SHEETS_CREDENTIALS environment variable or provide credentials_path/credentials_json")
        
        # Authorize the client
        self.client = gspread.authorize(self.creds)
    
    def load_asins_from_sheet(self, sheet_url: str, worksheet_name: str = None, asin_column: str = 'A') -> List[str]:
        """
        Load ASINs from a Google Sheet.
        
        Args:
            sheet_url: The URL or ID of the Google Sheet
            worksheet_name: Name of the worksheet (defaults to first sheet)
            asin_column: Column containing ASINs (default 'A')
            
        Returns:
            List of ASINs
        """
        try:
            # Open the spreadsheet
            if sheet_url.startswith('https://'):
                sheet = self.client.open_by_url(sheet_url)
            else:
                sheet = self.client.open_by_key(sheet_url)
            
            # Select worksheet
            if worksheet_name:
                worksheet = sheet.worksheet(worksheet_name)
            else:
                worksheet = sheet.get_worksheet(0)  # First worksheet
            
            # Get all values from the ASIN column
            asin_values = worksheet.col_values(self._column_letter_to_number(asin_column))
            
            # Filter out empty values and header if present
            asins = [asin.strip() for asin in asin_values if asin.strip() and not asin.lower().startswith('asin')]
            
            self.logger.info(f"Loaded {len(asins)} ASINs from Google Sheet")
            return asins
            
        except Exception as e:
            self.logger.error(f"Error loading ASINs from Google Sheet: {e}")
            raise
    
    def write_pricing_data(self, sheet_url: str, pricing_data: List[Dict], worksheet_name: str = None, start_row: int = 2):
        """
        Write pricing data back to Google Sheet.
        
        Args:
            sheet_url: The URL or ID of the Google Sheet
            pricing_data: List of dictionaries containing pricing information
            worksheet_name: Name of the worksheet (defaults to first sheet)
            start_row: Row to start writing data (default 2, assuming row 1 has headers)
        """
        try:
            # Open the spreadsheet
            if sheet_url.startswith('https://'):
                sheet = self.client.open_by_url(sheet_url)
            else:
                sheet = self.client.open_by_key(sheet_url)
            
            # Select worksheet
            if worksheet_name:
                worksheet = sheet.worksheet(worksheet_name)
            else:
                worksheet = sheet.get_worksheet(0)
            
            # Prepare headers if this is a new sheet
            headers = ['ASIN', 'Title', 'Current Price', 'List Price', 'Discount', 'Availability', 'Last Scraped', 'URL']
            
            # Check if headers exist, if not add them
            try:
                existing_headers = worksheet.row_values(1)
                if not existing_headers or len(existing_headers) < len(headers):
                    worksheet.insert_row(headers, 1)
            except:
                worksheet.insert_row(headers, 1)
            
            # Prepare data rows
            rows_to_add = []
            for item in pricing_data:
                row = [
                    item.get('asin', ''),
                    item.get('title', ''),
                    item.get('current_price', ''),
                    item.get('list_price', ''),
                    item.get('discount_percentage', ''),
                    item.get('availability', ''),
                    item.get('scraped_at', ''),
                    item.get('url', '')
                ]
                rows_to_add.append(row)
            
            # Clear existing data (except headers) and write new data
            if len(rows_to_add) > 0:
                # Clear from start_row onwards
                last_row = worksheet.row_count
                if last_row >= start_row:
                    range_to_clear = f"A{start_row}:H{last_row}"
                    worksheet.batch_clear([range_to_clear])
                
                # Write new data
                range_to_update = f"A{start_row}:H{start_row + len(rows_to_add) - 1}"
                worksheet.update(range_to_update, rows_to_add)
                
            self.logger.info(f"Written {len(rows_to_add)} rows of pricing data to Google Sheet")
            
        except Exception as e:
            self.logger.error(f"Error writing pricing data to Google Sheet: {e}")
            raise
    
    def _column_letter_to_number(self, column_letter: str) -> int:
        """Convert column letter to number (A=1, B=2, etc.)"""
        column_letter = column_letter.upper()
        result = 0
        for char in column_letter:
            result = result * 26 + (ord(char) - ord('A') + 1)
        return result
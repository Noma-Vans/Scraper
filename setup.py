#!/usr/bin/env python3
"""
Setup script for Amazon Price Monitor

This script helps set up the environment and dependencies.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def run_command(command, description):
    """Run a shell command and handle errors."""
    print(f"📦 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False


def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True


def check_chrome():
    """Check if Chrome browser is installed."""
    chrome_paths = [
        '/usr/bin/google-chrome',
        '/usr/bin/chromium-browser',
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
        'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe'
    ]
    
    for path in chrome_paths:
        if os.path.exists(path):
            print("✅ Chrome browser found")
            return True
    
    # Try to find chrome in PATH
    if shutil.which('google-chrome') or shutil.which('chromium-browser') or shutil.which('chrome'):
        print("✅ Chrome browser found in PATH")
        return True
    
    print("⚠️  Chrome browser not found. Please install Google Chrome or Chromium")
    print("   Download from: https://www.google.com/chrome/")
    return False


def install_dependencies():
    """Install Python dependencies."""
    return run_command(f"{sys.executable} -m pip install -r requirements.txt", "Installing Python dependencies")


def create_env_file():
    """Create .env file from template if it doesn't exist."""
    if os.path.exists('.env'):
        print("✅ .env file already exists")
        return True
    
    if os.path.exists('.env.example'):
        try:
            shutil.copy('.env.example', '.env')
            print("✅ Created .env file from template")
            print("📝 Please edit .env file with your configuration")
            return True
        except Exception as e:
            print(f"❌ Failed to create .env file: {e}")
            return False
    else:
        print("❌ .env.example file not found")
        return False


def run_test():
    """Run the test script to verify setup."""
    if not os.path.exists('test_scraper.py'):
        print("⚠️  Test script not found, skipping test")
        return True
    
    print("🧪 Running test to verify setup...")
    try:
        result = subprocess.run([sys.executable, 'test_scraper.py'], 
                              capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print("✅ Test completed successfully")
            return True
        else:
            print("❌ Test failed")
            print("Test output:", result.stdout)
            print("Test errors:", result.stderr)
            return False
    except subprocess.TimeoutExpired:
        print("⚠️  Test timed out (this may be normal)")
        return True
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False


def main():
    """Main setup function."""
    print("🚀 Amazon Price Monitor Setup")
    print("=" * 40)
    
    success = True
    
    # Check Python version
    if not check_python_version():
        success = False
    
    # Check Chrome browser
    if not check_chrome():
        success = False
    
    # Install dependencies
    if not install_dependencies():
        success = False
    
    # Create .env file
    if not create_env_file():
        success = False
    
    if success:
        print("\n✅ Setup completed successfully!")
        print("\n📋 Next steps:")
        print("1. Edit .env file with your Google Sheets credentials and sheet URL")
        print("2. Run 'python test_scraper.py' to test the setup")
        print("3. Run 'python amazon_price_monitor.py' to start scraping")
        
        # Optionally run test
        response = input("\n🧪 Would you like to run a test now? (y/N): ").lower()
        if response in ['y', 'yes']:
            run_test()
    else:
        print("\n❌ Setup failed. Please fix the issues above and try again.")
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
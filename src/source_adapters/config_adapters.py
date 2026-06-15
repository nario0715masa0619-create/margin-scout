"""
Configuration for source adapters.
Inherits settings from the original config_runtime.py
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Browser and timeout settings
BROWSER_GOTO_TIMEOUT_MS = 30000
BROWSER_SELECTOR_TIMEOUT_MS = 10000
BROWSER_SHORT_WAIT_MS = 1000
BROWSER_TIMEOUT_MS = 120000
API_REQUEST_TIMEOUT_SECONDS = 15

# Search limits
MAX_ITEMS_PER_SOURCE = 5  # Maximum items returned per source

# Excluded keywords (filter out items with these keywords)
EXCLUDED_KEYWORDS = [
    "盗難防止",
    "観賞用",
    "展示用",
    "レプリカ",
]

# Default values
DEFAULT_SHIPPING_COST_JPY = 1500

# Fee rates by genre
FEE_RATES = {
    "ポケモンカード": 0.15,
    "ワンピースカード": 0.15,
    "default": 0.15,
}

# Exchange rate fallback (for API failure)
EXCHANGE_RATE_FALLBACK_JPY = 157.50

# Environment variables
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
EBAY_CLIENT_ID = os.getenv('EBAY_REST_CLIENT_ID', os.getenv('EBAY_BROWSE_CLIENT_ID', ''))
EBAY_CLIENT_SECRET = os.getenv('EBAY_REST_CLIENT_SECRET', os.getenv('EBAY_BROWSE_CLIENT_SECRET', ''))

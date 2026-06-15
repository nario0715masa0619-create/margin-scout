"""
Currency and exchange rate utilities.
Reused from the original eBay Research Edge.
"""

import re
import requests
import pandas as pd
from typing import Union
from decimal import Decimal
from src.source_adapters.config_adapters import (
    EXCHANGE_RATE_FALLBACK_JPY,
    API_REQUEST_TIMEOUT_SECONDS
)


def parse_currency(value: Union[float, int, str, pd.isna]) -> float:
    """
    Parse currency value from various formats.
    
    Args:
        value: Any currency value (float, int, str, or NaN)
    
    Returns:
        float: Parsed value, or 0.0 if parse fails
    """
    if pd.isna(value):
        return 0.0
    
    v = re.sub(r'[^\d.]', '', str(value))
    try:
        return float(v)
    except (ValueError, TypeError):
        return 0.0


def get_exchange_rate() -> float:
    """
    Fetch current USD to JPY exchange rate from external API.
    
    Returns:
        float: Exchange rate (JPY per USD)
        Falls back to EXCHANGE_RATE_FALLBACK_JPY if API fails
    """
    try:
        r = requests.get(
            'https://api.exchangerate-api.com/v4/latest/USD',
            timeout=API_REQUEST_TIMEOUT_SECONDS
        )
        if r.status_code == 200:
            return r.json()['rates']['JPY']
    except Exception as e:
        print(f"[WARN] get_exchange_rate failed: {e}. Using fallback: {EXCHANGE_RATE_FALLBACK_JPY}")
    
    return EXCHANGE_RATE_FALLBACK_JPY


def clean_ebay_id(id_val) -> str:
    """
    Clean and normalize eBay item ID from various formats.
    
    Examples:
        "v1|123456789|0" → "123456789"
        "1.23456789e+08" → "123456789"
    
    Args:
        id_val: Raw eBay ID value
    
    Returns:
        str: Cleaned ID string
    """
    if not id_val or pd.isna(id_val):
        return ""
    
    s = str(id_val).strip()
    
    # Extract from v1|...|0 format
    match = re.search(r'v1\|(\d+)\|0', s)
    if match:
        return match.group(1)
    
    # Fix scientific notation or float format
    try:
        if 'e+' in s.lower() or '.' in s:
            return "{:.0f}".format(float(s))
    except (ValueError, TypeError):
        pass
    
    return s.replace('.0', '')

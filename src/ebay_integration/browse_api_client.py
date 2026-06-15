"""
eBay Browse API Client with Mock Support
"""

import requests
import urllib.parse
from typing import Dict, List, Any, Optional
from src.ebay_integration.auth_handler import EbayAuthHandler
from src.ebay_integration.error_handler import (
    EbayApiException,
    EbayAuthException,
    EbaySearchException,
)


class EbayBrowseApiClient:
    """eBay Browse API client for searching and fetching item details."""
    
    SANDBOX_BASE_URL = "https://api.sandbox.ebay.com/buy/browse/v1"
    PRODUCTION_BASE_URL = "https://api.ebay.com/buy/browse/v1"
    
    def __init__(self, auth_handler: EbayAuthHandler):
        """Initialize with auth handler."""
        self.auth_handler = auth_handler
        self.base_url = self.SANDBOX_BASE_URL
        self.timeout = 15
    
    async def search(self, query: str, limit: int = 5) -> List[Dict]:
        """
        Search eBay items by keyword.
        
        Args:
            query: Search query string
            limit: Maximum items to return
        
        Returns:
            List of item summaries
        """
        token = self.auth_handler.get_token()
        if not token:
            raise EbayAuthException("Failed to get eBay token")
        
        # Check if using mock
        if self.auth_handler.use_mock:
            print(f"[SEARCH-MOCK] Query: {query} (limit: {limit})")
            return self._generate_mock_search_results(query, limit)
        
        try:
            url = f"{self.base_url}/item_summary/search?q={urllib.parse.quote(query)}&limit={limit}"
            headers = {'Authorization': f'Bearer {token}'}
            
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            items = data.get('itemSummaries', [])
            print(f"[SEARCH] Found {len(items)} items for: {query}")
            return items
            
        except requests.exceptions.RequestException as e:
            raise EbaySearchException(f"eBay search failed: {e}")
    
    async def get_item(self, item_id: str) -> Dict:
        """
        Fetch detailed item information.
        
        Args:
            item_id: eBay item ID
        
        Returns:
            Item details
        """
        token = self.auth_handler.get_token()
        if not token:
            raise EbayAuthException("Failed to get eBay token")
        
        # Check if using mock
        if self.auth_handler.use_mock:
            print(f"[GETITEM-MOCK] Item ID: {item_id}")
            return self._generate_mock_item_details(item_id)
        
        try:
            full_id = f"v1|{item_id}|0" if item_id.isdigit() else item_id
            url = f"{self.base_url}/item/{full_id}"
            headers = {'Authorization': f'Bearer {token}'}
            
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise EbaySearchException(f"eBay getItem failed: {e}")
    
    def _generate_mock_search_results(self, query: str, limit: int) -> List[Dict]:
        """Generate realistic mock search results for testing."""
        mock_items = [
            {
                'itemId': '123456789001',
                'title': f'{query} - Official Item #1',
                'price': {'value': '29.99', 'currency': 'USD'},
                'condition': 'NEW',
                'image': {'imageUrl': 'https://via.placeholder.com/300?text=Item1'},
                'itemWebUrl': 'https://www.ebay.com/itm/123456789001',
            },
            {
                'itemId': '123456789002',
                'title': f'{query} - Official Item #2',
                'price': {'value': '34.99', 'currency': 'USD'},
                'condition': 'NEW',
                'image': {'imageUrl': 'https://via.placeholder.com/300?text=Item2'},
                'itemWebUrl': 'https://www.ebay.com/itm/123456789002',
            },
            {
                'itemId': '123456789003',
                'title': f'{query} - Official Item #3',
                'price': {'value': '39.99', 'currency': 'USD'},
                'condition': 'USED',
                'image': {'imageUrl': 'https://via.placeholder.com/300?text=Item3'},
                'itemWebUrl': 'https://www.ebay.com/itm/123456789003',
            },
        ]
        return mock_items[:limit]
    
    def _generate_mock_item_details(self, item_id: str) -> Dict:
        """Generate realistic mock item details."""
        return {
            'itemId': item_id,
            'title': f'Mock Product - {item_id}',
            'price': {'value': '34.99', 'currency': 'USD'},
            'condition': 'NEW',
            'image': {'imageUrl': 'https://via.placeholder.com/300?text=MockItem'},
            'itemWebUrl': f'https://www.ebay.com/itm/{item_id}',
            'seller': {
                'username': 'mock_seller',
                'feedbackPercentage': '99.5',
                'feedbackScore': 50000,
            },
        }

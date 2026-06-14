"""eBay Browse API クライアント"""
import requests
from typing import Dict, List, Optional
from datetime import datetime
import logging

class EbayBrowseApiClient:
    """eBay Browse API を呼び出すクライアント"""
    
    EBAY_SANDBOX_BASE_URL = "https://api.sandbox.ebay.com/buy/browse/v1"
    
    def __init__(self, auth_handler):
        self.auth_handler = auth_handler
        self.logger = logging.getLogger(__name__)
    
    def search(self, query: str, limit: int = 50, category_id: Optional[str] = None) -> Dict:
        """
        eBay で商品検索
        
        Args:
            query: 検索キーワード
            limit: 結果数（最大100）
            category_id: カテゴリID（オプション）
        
        Returns:
            API レスポンス（正規化前）
        """
        url = f"{self.EBAY_SANDBOX_BASE_URL}/item_summary/search"
        headers = self._get_headers()
        
        params = {
            "q": query,
            "limit": min(limit, 100),
            "sort": "newlyListed"
        }
        
        if category_id:
            params["category_ids"] = category_id
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        return response.json()
    
    def get_item(self, item_id: str) -> Dict:
        """
        eBay から商品詳細情報を取得
        
        Args:
            item_id: eBay item ID
        
        Returns:
            API レスポンス（正規化前）
        """
        url = f"{self.EBAY_SANDBOX_BASE_URL}/item/{item_id}"
        headers = self._get_headers()
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        return response.json()
    
    def _get_headers(self) -> Dict:
        """API リクエスト用ヘッダー生成"""
        access_token = self.auth_handler.get_access_token()
        return {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }

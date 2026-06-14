"""eBay Browse API 認証ハンドラ"""
import os
import requests
from datetime import datetime, timedelta
import json

class EbayAuthHandler:
    """eBay Browse API の OAuth 認証を管理"""
    
    EBAY_TOKEN_URL = "https://api.sandbox.ebay.com/identity/v1/oauth2/token"
    EBAY_SCOPE = "https://api.ebay.com/oauth/api_scope"
    
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.token_expiry = None
    
    def get_access_token(self) -> str:
        """有効な access token を取得（キャッシュ利用）"""
        # キャッシュが有効か確認
        if self.access_token and self.token_expiry:
            if datetime.now() < self.token_expiry - timedelta(minutes=5):
                return self.access_token
        
        # 新規取得
        self.access_token = self._fetch_token()
        self.token_expiry = datetime.now() + timedelta(hours=2)
        return self.access_token
    
    def _fetch_token(self) -> str:
        """eBay から新規 token を取得"""
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "grant_type": "client_credentials",
            "scope": self.EBAY_SCOPE,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        response = requests.post(self.EBAY_TOKEN_URL, headers=headers, data=data)
        response.raise_for_status()
        
        token_data = response.json()
        return token_data["access_token"]

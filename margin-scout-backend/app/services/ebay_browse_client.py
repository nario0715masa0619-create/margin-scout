"""
eBay Browse API クライアント
Refresh Token → Access Token 生成 → Browse API 呼び出し
"""

import logging
import json
from typing import Dict, List, Optional
import httpx
from datetime import datetime, timedelta
from app.config import settings

logger = logging.getLogger(__name__)

class EbayBrowseClient:
    """eBay Browse API クライアント（User Consent フロー）"""
    
    def __init__(self):
        self.base_url = "https://api.ebay.com/buy/browse/v1"
        self.oauth_url = "https://api.ebay.com/identity/v1/oauth2/token"
        self.client_id = settings.EBAY_CLIENT_ID
        self.client_secret = settings.EBAY_CLIENT_SECRET
        self.refresh_token = settings.EBAY_REFRESH_TOKEN
        self.timeout = settings.EBAY_REQUEST_TIMEOUT
        
        # Access Token キャッシュ
        self.access_token: Optional[str] = None
        self.access_token_expires_at: Optional[datetime] = None
        
        if not all([self.client_id, self.client_secret, self.refresh_token]):
            raise ValueError("EBAY_CLIENT_ID, EBAY_CLIENT_SECRET, EBAY_REFRESH_TOKEN are required")
    
    async def _get_access_token(self) -> str:
        """
        Refresh Token から Access Token を取得
        キャッシュして再利用（有効期限内なら再生成しない）
        """
        # キャッシュが有効なら返す
        if self.access_token and self.access_token_expires_at and datetime.utcnow() < self.access_token_expires_at:
            return self.access_token
        
        try:
            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            data = {
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
                "scope": "https://api.ebay.com/oauth/api_scope/buy.marketplace.search"
            }
            
            auth = (self.client_id, self.client_secret)
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.oauth_url,
                    headers=headers,
                    data=data,
                    auth=auth
                )
                
                if response.status_code != 200:
                    logger.error(f"eBay OAuth error: {response.status_code} - {response.text}")
                    raise Exception(f"Failed to get access token: {response.text}")
                
                token_data = response.json()
                self.access_token = token_data.get("access_token")
                expires_in = token_data.get("expires_in", 3600)
                self.access_token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in - 60)
                
                logger.info(f"✓ eBay access token obtained (expires in {expires_in}s)")
                return self.access_token
                
        except Exception as e:
            logger.error(f"eBay access token error: {e}")
            raise
    
    async def search(self, keyword: str, limit: int = 100) -> List[Dict]:
        """
        eBay で公開商品を検索
        
        Args:
            keyword: 検索キーワード
            limit: 取得件数（最大100）
        
        Returns:
            商品情報のリスト
        """
        try:
            access_token = await self._get_access_token()
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            params = {
                "q": keyword,
                "limit": min(limit, 100),
                "sort": "newlyListed"
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/item_summary/search",
                    headers=headers,
                    params=params
                )
                
                if response.status_code != 200:
                    logger.error(f"eBay Browse API error: {response.status_code} - {response.text}")
                    return []
                
                data = response.json()
                items = []
                
                for item in data.get("itemSummaries", []):
                    try:
                        price_obj = item.get("price", {})
                        if isinstance(price_obj, dict):
                            price = float(price_obj.get("value", 0))
                        else:
                            price = float(price_obj)
                        
                        items.append({
                            "item_id": item.get("itemId"),
                            "title": item.get("title"),
                            "price": price,
                            "url": item.get("itemWebUrl"),
                            "image": item.get("image", {}).get("imageUrl"),
                            "condition": item.get("condition"),
                            "seller_username": item.get("seller", {}).get("username"),
                            "source": "ebay"
                        })
                    except Exception as e:
                        logger.debug(f"Failed to parse eBay item: {e}")
                        continue
                
                logger.info(f"✓ eBay: {len(items)} items found for '{keyword}'")
                return items
                
        except Exception as e:
            logger.error(f"eBay search error: {e}")
            return []

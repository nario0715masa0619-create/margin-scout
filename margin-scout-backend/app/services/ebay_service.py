import httpx
import logging
from app.config import settings
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class EbayService:
    BASE_URL = "https://api.ebay.com"
    
    def __init__(self):
        self.client_id = settings.EBAY_CLIENT_ID
        self.client_secret = settings.EBAY_CLIENT_SECRET
        self.refresh_token = settings.EBAY_REFRESH_TOKEN
        self.access_token = None
        self.token_expiry = None
    
    async def get_access_token(self) -> str:
        """OAuth 2.0 で アクセストークンを取得"""
        if self.access_token and self.token_expiry and datetime.now() < self.token_expiry:
            return self.access_token
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.BASE_URL}/identity/v1/oauth2/token",
                    data={
                        "grant_type": "refresh_token",
                        "refresh_token": self.refresh_token,
                        "scope": "https://api.ebay.com/oauth/api_scope"
                    },
                    auth=(self.client_id, self.client_secret)
                )
                data = response.json()
                self.access_token = data["access_token"]
                self.token_expiry = datetime.now() + timedelta(seconds=data["expires_in"] - 60)
                return self.access_token
        except Exception as e:
            logger.error(f"Failed to get eBay access token: {e}")
            raise
    
    async def search_items(self, keywords: str, limit: int = 10) -> list:
        """eBay で商品を検索"""
        try:
            token = await self.get_access_token()
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/buy/browse/v1/item_summary/search",
                    params={
                        "q": keywords,
                        "limit": min(limit, 100),
                        "sort": "newlyListed"
                    },
                    headers={"Authorization": f"Bearer {token}"}
                )
                data = response.json()
                
                items = []
                for item in data.get("itemSummaries", []):
                    items.append({
                        "item_id": item.get("itemId"),
                        "title": item.get("title"),
                        "price": float(item.get("price", {}).get("value", 0)),
                        "currency": item.get("price", {}).get("currency", "USD"),
                        "condition": item.get("condition"),
                        "image": item.get("image", {}).get("imageUrl"),
                        "url": item.get("itemWebUrl")
                    })
                return items
        except Exception as e:
            logger.error(f"Failed to search eBay items: {e}")
            return []
    
    async def get_item_details(self, item_id: str) -> dict:
        """eBay 商品の詳細情報を取得"""
        try:
            token = await self.get_access_token()
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/buy/browse/v1/item/{item_id}",
                    headers={"Authorization": f"Bearer {token}"}
                )
                return response.json()
        except Exception as e:
            logger.error(f"Failed to get eBay item details: {e}")
            return {}

# シングルトン
ebay_service = EbayService()

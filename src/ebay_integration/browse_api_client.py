import aiohttp
import asyncio
from typing import Optional, Dict, List

class EbayBrowseApiClient:
    """eBay Browse API クライアント"""
    
    def __init__(self, auth_handler):
        """
        初期化（後方互換性維持）
        
        Args:
            auth_handler: EbayAuthHandler インスタンス
        """
        self.auth_handler = auth_handler
        self.api_mode = auth_handler.api_mode
        self.token = auth_handler.get_token()
        
        # API ホスト設定
        if self.api_mode == 'sandbox':
            self.api_host = 'api.sandbox.ebay.com'
        else:
            self.api_host = 'api.ebay.com'
        
        self.base_url = f'https://{self.api_host}/buy/browse/v1'
    
    async def search(
        self,
        q: str,
        limit: int = 10,
        sort: str = 'newlyListed',
        **kwargs
    ) -> List[Dict]:
        """
        eBay で商品を検索
        
        Args:
            q (str): 検索キーワード
            limit (int): 返す最大件数
            sort (str): ソート方法
            
        Returns:
            Dict: API レスポンス
        """
        endpoint = f'{self.base_url}/item_summary/search'
        
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        
        params = {
            'q': q,
            'limit': limit,
            'sort': sort
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    endpoint,
                    headers=headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('itemSummaries', [])
                    else:
                        print(f'[ERROR] Browse API error: {response.status}')
                        text = await response.text()
                        print(f'[ERROR] Response: {text}')
                        return []
        
        except asyncio.TimeoutError:
            print('[ERROR] Browse API request timeout')
            return []
        except Exception as e:
            print(f'[ERROR] Browse API request failed: {str(e)}')
            return []
    
    async def get_item(self, item_id: str) -> Optional[Dict]:
        """
        eBay で特定の商品情報を取得
        
        Args:
            item_id (str): 商品 ID
            
        Returns:
            Dict: API レスポンス
        """
        endpoint = f'{self.base_url}/item/{item_id}'
        
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    endpoint,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        print(f'[ERROR] Get item error: {response.status}')
                        return None
        
        except Exception as e:
            print(f'[ERROR] Get item request failed: {str(e)}')
            return None

import os
import requests
from dotenv import load_dotenv
from pathlib import Path

# .env を読み込み
load_dotenv(Path.home() / '.marginscount' / '.env')

class EbayAuthHandler:
    """eBay OAuth 認証ハンドラー"""
    
    def __init__(self, api_mode='sandbox'):
        """
        初期化
        
        Args:
            api_mode (str): 'sandbox' または 'live'
        """
        self.api_mode = api_mode
        self.client_id = os.getenv('EBAY_CLIENT_ID', '')
        self.client_secret = os.getenv('EBAY_CLIENT_SECRET', '')
        
        # エンドポイント設定
        if api_mode == 'sandbox':
            self.auth_host = 'api.sandbox.ebay.com'
        else:
            self.auth_host = 'api.ebay.com'
        
        self.auth_url = f'https://{self.auth_host}/identity/v1/oauth2/token'
        self.token = None
        self._token_timestamp = None
    
    def get_token(self):
        """
        eBay OAuth トークンを取得
        
        Returns:
            str: OAuth トークン
            
        Raises:
            ValueError: クレデンシャルが設定されていない場合
            requests.RequestException: OAuth サーバーからのエラー
        """
        # クレデンシャル確認
        if not self.client_id or not self.client_secret:
            raise ValueError(
                f'eBay credentials not configured. '
                f'Please set EBAY_CLIENT_ID and EBAY_CLIENT_SECRET in .env '
                f'(path: {Path.home() / ".marginscount" / ".env"})'
            )
        
        # キャッシュ済みトークンがあれば返す（簡易版）
        if self.token:
            return self.token
        
        # OAuth リクエスト
        try:
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            data = {
                'grant_type': 'client_credentials',
                'scope': 'https://api.ebay.com/oauth/api_scope'
            }
            
            response = requests.post(
                self.auth_url,
                headers=headers,
                data=data,
                auth=(self.client_id, self.client_secret),
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                self.token = result.get('access_token')
                print(f'[AUTH] Token obtained from {self.auth_host}')
                return self.token
            else:
                raise Exception(f'OAuth error: {response.status_code} - {response.text}')
        
        except requests.RequestException as e:
            raise Exception(f'OAuth request failed: {str(e)}')


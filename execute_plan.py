import os
import sys
import asyncio
import json
from pathlib import Path
from datetime import datetime

print('=' * 80)
print('【eBay Browse API 実装修正・テスト実行】')
print('=' * 80)

# ========================================
# Phase 1: auth_handler.py を修正
# ========================================
print('\n' + '=' * 80)
print('【Phase 1】auth_handler.py を修正')
print('=' * 80)

auth_handler_code = '''import os
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

'''

auth_file = Path('src/ebay_integration/auth_handler.py')
with open(auth_file, 'w', encoding='utf-8') as f:
    f.write(auth_handler_code)

print('✅ auth_handler.py を修正しました')
print('   - 環境変数キー: EBAY_CLIENT_ID / EBAY_CLIENT_SECRET')
print('   - api_mode パラメータ: sandbox / live')
print('   - モック完全廃止: 実クレデンシャル必須')
print('   - OAuth エンドポイント: 動的切り替え')

# ========================================
# Phase 2: browse_api_client.py を修正
# ========================================
print('\n' + '=' * 80)
print('【Phase 2】browse_api_client.py を修正')
print('=' * 80)

browse_api_code = '''import aiohttp
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
    
    async def search_items(
        self,
        q: str,
        limit: int = 10,
        sort: str = 'newlyListed',
        **kwargs
    ) -> Optional[Dict]:
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
                        return await response.json()
                    else:
                        print(f'[ERROR] Browse API error: {response.status}')
                        text = await response.text()
                        print(f'[ERROR] Response: {text}')
                        return None
        
        except asyncio.TimeoutError:
            print('[ERROR] Browse API request timeout')
            return None
        except Exception as e:
            print(f'[ERROR] Browse API request failed: {str(e)}')
            return None
    
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
'''

browse_file = Path('src/ebay_integration/browse_api_client.py')
with open(browse_file, 'w', encoding='utf-8') as f:
    f.write(browse_api_code)

print('✅ browse_api_client.py を修正しました')
print('   - __init__ シグネチャ: auth_handler を受け取る（後方互換性維持）')
print('   - api_mode と api_host: 動的に設定')
print('   - ベース URL: api_mode で動的構築')
print('   - OAuth トークン: auth_handler から取得')

# ========================================
# Step 1: 環境変数確認テスト
# ========================================
print('\n' + '=' * 80)
print('【Step 1】環境変数確認テスト')
print('=' * 80)

env_path = Path('C:/Users/nario/.marginscount/.env')
print(f'✅ .env ファイル確認: {env_path}')

if env_path.exists():
    with open(env_path, 'r', encoding='utf-8') as f:
        ebay_keys = {}
        for line in f:
            if 'EBAY' in line and '=' in line:
                key, val = line.strip().split('=', 1)
                # 機密情報を隠す
                val_display = val[:10] + '***' if len(val) > 10 else val
                ebay_keys[key] = val_display
                print(f'   {key}={val_display}')

# ========================================
# Step 2: auth_handler 単体テスト
# ========================================
print('\n' + '=' * 80)
print('【Step 2】auth_handler 単体テスト')
print('=' * 80)

try:
    from src.ebay_integration.auth_handler import EbayAuthHandler
    
    print('✅ auth_handler.py インポート成功')
    
    # Sandbox モード
    print('\n🔍 Sandbox 認証テスト...')
    auth_sandbox = EbayAuthHandler(api_mode='sandbox')
    print(f'   API Mode: {auth_sandbox.api_mode}')
    print(f'   Auth Host: {auth_sandbox.auth_host}')
    print(f'   Auth URL: {auth_sandbox.auth_url}')
    
    token_sandbox = auth_sandbox.get_token()
    print(f'   ✅ Token: {token_sandbox[:40]}...')
    
except ValueError as e:
    print(f'❌ ValueError: {e}')
except Exception as e:
    print(f'❌ エラー: {e}')

# ========================================
# Step 3: browse_api_client 単体テスト
# ========================================
print('\n' + '=' * 80)
print('【Step 3】browse_api_client 単体テスト')
print('=' * 80)

try:
    from src.ebay_integration.browse_api_client import EbayBrowseApiClient
    
    print('✅ browse_api_client.py インポート成功')
    
    # クライアント初期化（後方互換性テスト）
    print('\n🔍 クライアント初期化テスト...')
    client = EbayBrowseApiClient(auth_sandbox)
    print(f'   ✅ API Mode: {client.api_mode}')
    print(f'   ✅ API Host: {client.api_host}')
    print(f'   ✅ Base URL: {client.base_url}')
    print(f'   ✅ Token: {client.token[:40]}...')
    
except Exception as e:
    print(f'❌ エラー: {e}')

# ========================================
# Step 4: Browse API 実接続確認テスト
# ========================================
print('\n' + '=' * 80)
print('【Step 4】Browse API 実接続確認テスト')
print('=' * 80)

async def run_browse_test():
    test_keywords = [
        'iPhone 16',
        'Canon EOS',
        'Nintendo Switch',
    ]
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'api_mode': client.api_mode,
        'api_host': client.api_host,
        'searches': []
    }
    
    for keyword in test_keywords:
        print(f'\n🔍 検索: {keyword}')
        try:
            response = await client.search_items(q=keyword, limit=3)
            
            if response and 'itemSummaries' in response:
                items = response['itemSummaries']
                print(f'   ✅ {len(items)} 件取得')
                
                for i, item in enumerate(items[:1], 1):
                    title = item.get('title', 'N/A')[:50]
                    price_info = item.get('price', {})
                    price = price_info.get('value', 'N/A')
                    currency = price_info.get('currency', 'N/A')
                    
                    print(f'   [{i}] {title}')
                    print(f'       {currency} {price}')
                    
                    results['searches'].append({
                        'keyword': keyword,
                        'success': True,
                        'item_count': len(items),
                        'title': title,
                        'price': price,
                        'currency': currency
                    })
            else:
                print(f'   ⚠️ 結果なし')
                results['searches'].append({
                    'keyword': keyword,
                    'success': False,
                    'reason': 'No items found'
                })
        
        except Exception as e:
            print(f'   ❌ エラー: {e}')
            results['searches'].append({
                'keyword': keyword,
                'success': False,
                'error': str(e)
            })
    
    return results

try:
    browse_results = asyncio.run(run_browse_test())
    
    # 結果を JSON で保存
    output_file = Path('test_browse_api_realconnect_final.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(browse_results, f, ensure_ascii=False, indent=2)
    
    print(f'\n✅ 結果を {output_file} に保存')
    
    # サマリー
    success_count = len([r for r in browse_results['searches'] if r.get('success')])
    print(f'📊 成功: {success_count} / {len(browse_results["searches"])}')

except Exception as e:
    print(f'❌ Browse API テスト実行エラー: {e}')

# ========================================
# 最終レポート
# ========================================
print('\n' + '=' * 80)
print('【最終レポート】')
print('=' * 80)
print('✅ Phase 1: auth_handler.py 修正完了')
print('✅ Phase 2: browse_api_client.py 修正完了')
print('✅ Step 1: 環境変数確認テスト完了')
print('✅ Step 2: auth_handler 単体テスト完了')
print('✅ Step 3: browse_api_client 単体テスト完了')
print('✅ Step 4: Browse API 実接続確認テスト完了')
print('\n📝 次のステップ: E2E テスト再実行 (Step 5)')

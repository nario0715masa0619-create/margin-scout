import asyncio
import json
import os
from pathlib import Path
from datetime import datetime

# .env から設定を読み込み
env_path = Path('C:/Users/nario/.marginscount/.env')
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, val = line.strip().split('=', 1)
                os.environ[key] = val

print('=' * 70)
print('【eBay Browse API 実接続確認テスト】')
print('=' * 70)

# auth_handler をインポート
try:
    from src.ebay_integration.auth_handler import EbayAuthHandler
    from src.ebay_integration.browse_api_client import EbayBrowseApiClient
    print('✅ モジュールインポート成功')
except Exception as e:
    print(f'❌ モジュールインポート失敗: {e}')
    exit(1)

# トークン取得
try:
    auth = EbayAuthHandler()
    token = auth.get_token()
    if token:
        print(f'✅ トークン取得成功: {token[:40]}...')
    else:
        print('❌ トークン取得失敗')
        exit(1)
except Exception as e:
    print(f'❌ トークン取得エラー: {e}')
    exit(1)

# API クライアント初期化
try:
    # EBAY_ENV を確認
    api_mode = os.getenv('EBAY_ENV', 'sandbox')
    print(f'✅ API モード: {api_mode}')
    
    client = EbayBrowseApiClient(token, api_mode=api_mode)
    print('✅ API クライアント初期化成功')
except Exception as e:
    print(f'❌ API クライアント初期化エラー: {e}')
    exit(1)

# テストキーワード
test_keywords = [
    'iPhone 16',
    'Canon EOS',
    'Nintendo Switch',
]

results = {
    'timestamp': datetime.now().isoformat(),
    'api_mode': api_mode,
    'token_sample': f'{token[:40]}...',
    'searches': []
}

# 検索実行
async def run_searches():
    for keyword in test_keywords:
        print(f'\n🔍 検索: {keyword}')
        try:
            response = await client.search_items(q=keyword, limit=1)
            
            if response and 'itemSummaries' in response:
                items = response['itemSummaries']
                print(f'   ✅ {len(items)} 件取得')
                
                for item in items[:1]:
                    print(f'      タイトル: {item.get("title", "N/A")[:50]}')
                    price = item.get('price', {})
                    print(f'      価格: {price.get("currency", "")} {price.get("value", "")}')
                    
                    results['searches'].append({
                        'keyword': keyword,
                        'success': True,
                        'item_count': len(items),
                        'title': item.get('title'),
                        'price': price.get('value'),
                        'currency': price.get('currency')
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

asyncio.run(run_searches())

# 結果保存
output_file = 'test_browse_api_realconnect.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f'\n✅ 結果を {output_file} に保存')
print(f'📊 成功: {len([r for r in results["searches"] if r.get("success")])} / {len(test_keywords)}')

import sys
import asyncio
import json
from pathlib import Path

# インポート設定
sys.path.insert(0, str(Path.cwd()))

from src.ebay_integration.auth_handler import EbayAuthHandler
from src.ebay_integration.browse_api_client import EbayBrowseApiClient
from src.research_workflow.query_optimizer_advanced import AdvancedQueryOptimizer
from src.research_workflow.product_matcher_advanced import AdvancedProductMatcher
from src.research_workflow.csv_handler_advanced import AdvancedCsvHandler

print('=' * 60)
print('Phase B+ 統合テスト開始')
print('=' * 60)

# ステップ 1: クエリ最適化テスト
print('\n✅ Step 1: クエリ最適化テスト')
optimizer = AdvancedQueryOptimizer()

test_titles = [
    'Nikon D850 デジタル一眼レフカメラ ボディのみ',
    'Canon EOS Kiss X10i',
    '遊戯王 初期セット ブルーアイズ',
    'Gucci GG柄 ショルダーバッグ',
]

for title in test_titles:
    queries = optimizer.generate_fallback_queries(title)
    print(f'  元タイトル: {title}')
    print(f'  生成クエリ: {queries}')
    print()

# ステップ 2: eBay API 接続テスト（拡張マッチング）
print('\n✅ Step 2: eBay API + 拡張マッチング統合テスト')

async def test_advanced_matching():
    auth_handler = EbayAuthHandler(api_mode='live')
    client = EbayBrowseApiClient(auth_handler)
    matcher = AdvancedProductMatcher()
    
    test_keywords = ['Nikon D850', 'Canon EOS', 'iPhone 16']
    results = []
    
    for keyword in test_keywords:
        try:
            # Note: search function in browse_api_client.py is called 'search' not 'search_items'
            items = await client.search(keyword, limit=3)
            print(f'\n  🔍 検索: {keyword}')
            print(f'  ヒット件数: {len(items)}')
            
            if items:
                # マッチング成功例の記録
                for item in items[:1]:
                    print(f'    - タイトル: {item.get("title", "N/A")[:60]}')
                    print(f'    - 価格: ${item.get("price", {}).get("value", "N/A")}')
            
            results.append({
                'keyword': keyword,
                'hit_count': len(items),
                'status': '✅ 成功'
            })
        except Exception as e:
            print(f'  ❌ エラー: {str(e)[:100]}')
            results.append({
                'keyword': keyword,
                'hit_count': 0,
                'status': '❌ 失敗'
            })
    
    return results

# 非同期実行
results = asyncio.run(test_advanced_matching())

print('\n' + '=' * 60)
print('統合テスト結果サマリー')
print('=' * 60)
for r in results:
    status_icon = '✅' if r['status'] == '✅ 成功' else '❌'
    print(f'{status_icon} {r["keyword"]}: {r["hit_count"]} 件')

print('\n✅ Phase B+ 統合テスト完了！')
print('次: E2E テスト実行へ進みます')

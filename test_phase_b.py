import asyncio
import os
import sys
from pathlib import Path
from dataclasses import dataclass

sys.path.insert(0, str(Path(__file__).parent))

from src.ebay_integration.auth_handler import EbayAuthHandler
from src.ebay_integration.browse_api_client import EbayBrowseApiClient
from src.research_workflow.product_matcher import ProductMatcher
from src.research_workflow.query_optimizer import QueryOptimizer

@dataclass
class MockSourceItem:
    product_title: str
    source_price: float

async def test_phase_b_improvements():
    print("=== Phase B 改善効果テスト ===")
    
    # 1. 初期化
    auth = EbayAuthHandler()
    client = EbayBrowseApiClient(auth)
    optimizer = QueryOptimizer()
    matcher = ProductMatcher()
    
    # 2. テストデータ（実際の日本のフリマサイトにありそうなタイトル）
    test_items = [
        {"title": "【美品】Canon EOS Kiss X10 ボディ デジタル一眼レフ", "price": 45000, "brand": "Canon", "model": "EOS Kiss X10"},
        {"title": "ポケモンカードゲーム ソード＆シールド ハイクラスパック VSTARユニバース", "price": 5500, "brand": "ポケモン", "model": ""},
        {"title": "GUCCI グッチ GGマーモント キルティング スモール ショルダーバッグ ブラック", "price": 120000, "brand": "GUCCI", "model": ""},
        {"title": "新品未開封 iPhone 12 64GB ホワイト SIMフリー", "price": 60000, "brand": "Apple", "model": "iPhone 12"},
        {"title": "SONY ワイヤレスノイズキャンセリングステレオヘッドセット WH-1000XM4 ブラック", "price": 25000, "brand": "SONY", "model": "WH-1000XM4"}
    ]
    
    success_count = 0
    total = len(test_items)
    
    print(f"Total items to test: {total}\n")
    
    for item_data in test_items:
        title = item_data["title"]
        print(f"\n--- Testing: {title} ---")
        
        # Query Optimizer のテスト
        queries = optimizer.generate_queries({
            "product_name": title,
            "brand": item_data["brand"],
            "model_number": item_data["model"]
        })
        print(f"Generated queries: {queries}")
        
        # eBay 検索とマッチングのテスト
        ebay_results = []
        used_query = ""
        for q in queries:
            print(f"  Searching eBay for: '{q}'")
            results = await client.search(q, limit=3)
            if results:
                ebay_results = results
                used_query = q
                print(f"  ✅ Found {len(results)} results for '{q}'")
                break
            else:
                print(f"  ❌ No results for '{q}'")
                
        if not ebay_results:
            print("  ❌ eBay search failed for all queries.")
            continue
            
        # マッチングテスト
        best_ebay, score = matcher.match_items(
            source_product={"product_name": title},
            ebay_search_results=ebay_results,
            source_price_jpy=item_data["price"]
        )
        
        if best_ebay and score >= 0.4:
            print(f"  🏆 MATCH SUCCESS (Score: {score:.2f}) -> {best_ebay.get('title')}")
            success_count += 1
        else:
            print(f"  ⚠️ MATCH FAILED (Score: {score:.2f}) -> Best was {best_ebay.get('title') if best_ebay else 'None'}")
            
    print("\n" + "="*40)
    print(f"TEST COMPLETE: {success_count}/{total} ({(success_count/total)*100:.1f}%) SUCCESS RATE")
    print("="*40)

if __name__ == "__main__":
    asyncio.run(test_phase_b_improvements())

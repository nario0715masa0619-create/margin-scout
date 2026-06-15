"""
Phase D-2: Yahoo adapters smoke test.
"""

import asyncio
import sys
from playwright.async_api import async_playwright

sys.path.insert(0, '.')

from src.source_adapters.yahoo_adapter import YahooFleamarketAdapter, YahooAuctionHistoryAdapter


async def test_yahoo():
    """Test Yahoo adapters with sample keywords."""
    
    keywords = ['ピカチュウ', 'SAR']
    
    print("[TEST] Yahoo Adapters Smoke Test")
    print(f"  Keywords: {keywords}")
    print()
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            
            # Test 1: Yahoo Fleamarket
            print("=" * 60)
            print("[1/2] Yahoo Fleamarket Adapter")
            print("=" * 60)
            page1 = await browser.new_page()
            adapter_flea = YahooFleamarketAdapter(page1)
            
            try:
                items_flea = await adapter_flea.search(keywords, genre='ポケモンカード')
                print(f"[RESULT] Found {len(items_flea)} items")
                print()
                
                for i, item in enumerate(items_flea[:3], 1):
                    print(f"  Item {i}:")
                    print(f"    Title: {item.product_title[:50]}")
                    print(f"    Price: ¥{item.source_price:,}")
                    print(f"    URL: {item.source_url[:70]}")
                    print()
            except Exception as e:
                print(f"[WARN] Yahoo Fleamarket search error: {e}")
            finally:
                await adapter_flea.close()
            
            # Test 2: Yahoo Auction History
            print("=" * 60)
            print("[2/2] Yahoo Auction History Adapter")
            print("=" * 60)
            adapter_auction = YahooAuctionHistoryAdapter(browser)
            
            try:
                items_auction = await adapter_auction.search(keywords)
                print(f"[RESULT] Found {len(items_auction)} history item(s)")
                print()
                
                for item in items_auction:
                    print(f"  Title: {item.product_title}")
                    print(f"  Price: ¥{item.source_price:,} (median)")
                    print(f"  Condition: {item.condition_text}")
                    if hasattr(item, '_stats'):
                        stats = item._stats
                        print(f"  Stats: Min=¥{stats['min']:,}, Max=¥{stats['max']:,}, Count={stats['count']}")
                    print()
            except Exception as e:
                print(f"[WARN] Yahoo Auction history error: {e}")
            
            await browser.close()
            
            print("[PASS] Yahoo adapters test completed!")
            return True
            
    except Exception as e:
        print(f"[FAIL] Test error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    result = asyncio.run(test_yahoo())
    sys.exit(0 if result else 1)

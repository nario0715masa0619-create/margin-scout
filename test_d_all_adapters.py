"""
Phase D Integration Test: All three adapters together.
"""

import asyncio
import sys
from playwright.async_api import async_playwright

sys.path.insert(0, '.')

from src.source_adapters.mercari_adapter import MercariAdapter
from src.source_adapters.yahoo_adapter import YahooFleamarketAdapter, YahooAuctionHistoryAdapter
from src.source_adapters.hardoff_adapter import HardoffAdapter


async def test_all_adapters():
    """Test all adapters with the same keywords."""
    
    keywords = ['ピカチュウ']
    
    print("[TEST] All Adapters Integration Test")
    print(f"  Keywords: {keywords}")
    print(f"  Genre: ポケモンカード")
    print()
    
    results_summary = {}
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            
            # Test 1: Mercari
            print("=" * 70)
            print("[1/4] Mercari Adapter")
            print("=" * 70)
            try:
                page1 = await browser.new_page()
                adapter1 = MercariAdapter(page1)
                items1 = await adapter1.search(keywords, genre='ポケモンカード')
                results_summary['Mercari'] = len(items1)
                print(f"✓ Found {len(items1)} items\n")
                await adapter1.close()
            except Exception as e:
                print(f"✗ Error: {e}\n")
                results_summary['Mercari'] = 'ERROR'
            
            # Test 2: Yahoo Fleamarket
            print("=" * 70)
            print("[2/4] Yahoo Fleamarket Adapter")
            print("=" * 70)
            try:
                page2 = await browser.new_page()
                adapter2 = YahooFleamarketAdapter(page2)
                items2 = await adapter2.search(keywords, genre='ポケモンカード')
                results_summary['YahooFlea'] = len(items2)
                print(f"✓ Found {len(items2)} items\n")
                await adapter2.close()
            except Exception as e:
                print(f"✗ Error: {e}\n")
                results_summary['YahooFlea'] = 'ERROR'
            
            # Test 3: Yahoo Auction History
            print("=" * 70)
            print("[3/4] Yahoo Auction History Adapter")
            print("=" * 70)
            try:
                adapter3 = YahooAuctionHistoryAdapter(browser)
                items3 = await adapter3.search(keywords)
                results_summary['YahooAuction'] = len(items3)
                if items3 and hasattr(items3[0], '_stats'):
                    stats = items3[0]._stats
                    print(f"✓ Found {len(items3)} history item(s)")
                    print(f"  Median: ¥{stats['median']:,} (n={stats['count']})\n")
                else:
                    print(f"✓ Found {len(items3)} item(s)\n")
            except Exception as e:
                print(f"✗ Error: {e}\n")
                results_summary['YahooAuction'] = 'ERROR'
            
            # Test 4: Hardoff
            print("=" * 70)
            print("[4/4] Hardoff Adapter")
            print("=" * 70)
            try:
                page4 = await browser.new_page()
                adapter4 = HardoffAdapter(page4)
                items4 = await adapter4.search(keywords, genre='')
                results_summary['Hardoff'] = len(items4)
                print(f"✓ Found {len(items4)} items\n")
                await adapter4.close()
            except Exception as e:
                print(f"✗ Error: {e}\n")
                results_summary['Hardoff'] = 'ERROR'
            
            await browser.close()
            
            # Summary
            print("=" * 70)
            print("SUMMARY")
            print("=" * 70)
            for adapter_name, result in results_summary.items():
                status = "✓" if isinstance(result, int) else "✗"
                print(f"  {status} {adapter_name}: {result}")
            
            print()
            print("[PASS] All adapter integration test completed!")
            return True
            
    except Exception as e:
        print(f"[FAIL] Test error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    result = asyncio.run(test_all_adapters())
    sys.exit(0 if result else 1)

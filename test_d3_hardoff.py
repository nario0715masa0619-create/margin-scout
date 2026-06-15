"""
Phase D-3: Hardoff adapter smoke test.
"""

import asyncio
import sys
from playwright.async_api import async_playwright

sys.path.insert(0, '.')

from src.source_adapters.hardoff_adapter import HardoffAdapter


async def test_hardoff():
    """Test Hardoff adapter with sample keywords."""
    
    keywords = ['ポケモン', 'カード']
    
    print("[TEST] Hardoff Adapter Smoke Test")
    print(f"  Keywords: {keywords}")
    print()
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            adapter = HardoffAdapter(page)
            
            # Search
            print("[EXEC] Starting search...")
            items = await adapter.search(keywords, genre='')
            
            print(f"[RESULT] Found {len(items)} items")
            print()
            
            for i, item in enumerate(items[:5], 1):
                print(f"  Item {i}:")
                print(f"    Title: {item.product_title[:60]}")
                print(f"    Price: ¥{item.source_price:,}")
                print(f"    URL: {item.source_url[:70]}")
                print()
            
            await adapter.close()
            await browser.close()
            
            print("[PASS] Hardoff adapter test passed!")
            return True
            
    except Exception as e:
        print(f"[FAIL] Test error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    result = asyncio.run(test_hardoff())
    sys.exit(0 if result else 1)

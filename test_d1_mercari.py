"""
Phase D-1: Mercari adapter smoke test.
"""

import asyncio
import sys
from playwright.async_api import async_playwright

# Add src to path
sys.path.insert(0, '.')

from src.source_adapters.mercari_adapter import MercariAdapter
from src.source_adapters.utils.keywords import extract_keywords


async def test_mercari():
    """Test Mercari adapter with sample keywords."""
    
    keywords = ['ピカチュウ', 'SAR']
    
    print("[TEST] Mercari Adapter Smoke Test")
    print(f"  Keywords: {keywords}")
    print()
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            adapter = MercariAdapter(page)
            
            # Search
            print("[EXEC] Starting search...")
            items = await adapter.search(keywords, genre='ポケモンカード')
            
            print(f"[RESULT] Found {len(items)} items")
            print()
            
            for i, item in enumerate(items[:3], 1):
                print(f"  Item {i}:")
                print(f"    Title: {item.product_title[:50]}")
                print(f"    Price: ¥{item.source_price:,}")
                print(f"    URL: {item.source_url}")
                print()
            
            await adapter.close()
            await browser.close()
            
            print("[PASS] Mercari adapter test passed!")
            return True
            
    except Exception as e:
        print(f"[FAIL] Test error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    result = asyncio.run(test_mercari())
    sys.exit(0 if result else 1)

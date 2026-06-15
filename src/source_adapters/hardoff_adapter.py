"""
Hardoff adapter - scrapes items from Hardoff netmall (netmall.hardoff.co.jp).
Reused from the original eBay Research Edge search_hardoff function.
"""

import re
import urllib.parse
import asyncio
from typing import List
from playwright.async_api import Page
from datetime import datetime

from src.source_adapters.base_adapter import BaseSourceAdapter, SourceItem
from src.source_adapters.config_adapters import (
    BROWSER_GOTO_TIMEOUT_MS,
    BROWSER_SELECTOR_TIMEOUT_MS,
    BROWSER_SHORT_WAIT_MS,
    EXCLUDED_KEYWORDS,
    MAX_ITEMS_PER_SOURCE,
)


class HardoffAdapter(BaseSourceAdapter):
    """Hardoff netmall scraper adapter."""
    
    def __init__(self, page: Page):
        super().__init__()
        self.page = page
        self.name = 'ハードオフ'
    
    async def search(self, keywords: List[str], genre: str = '') -> List[SourceItem]:
        """
        Search Hardoff netmall by keywords.
        
        Args:
            keywords: List of search keywords (preferably Japanese)
            genre: Product genre (added to query if provided)
        
        Returns:
            List[SourceItem]: Matched items
        """
        if not keywords:
            return []
        
        # Build query: genre + keywords (up to 5 words)
        if genre:
            words = [genre] + keywords
        else:
            words = keywords
        
        unique_words = []
        for w in words:
            if w not in unique_words:
                unique_words.append(w)
        
        query = ' '.join(unique_words[:5])
        
        try:
            url = f'https://netmall.hardoff.co.jp/search/?q={urllib.parse.quote(query)}'
            print(f"  [Hardoff] URL: {url}")
            
            # Navigate to URL
            try:
                await asyncio.wait_for(
                    self.page.goto(url, wait_until='domcontentloaded'),
                    timeout=BROWSER_GOTO_TIMEOUT_MS / 1000
                )
            except asyncio.TimeoutError:
                print(f"  [Hardoff] Goto timeout: {url}")
                return []
            
            # Wait a bit for dynamic content to load
            await self.page.wait_for_timeout(BROWSER_SHORT_WAIT_MS)
            
            # Find product items using multiple possible selectors
            items = await self.page.locator('div.item, .product-card, div:has(> a[href*="/product/"])').all()
            
            if not items:
                print(f"  [Hardoff] No items found (selector mismatch)")
                return []
            
            results = []
            
            for item in items[:MAX_ITEMS_PER_SOURCE]:
                try:
                    data = await item.evaluate("""el => {
                        const link = el.querySelector('a');
                        const text = el.innerText;
                        const img = el.querySelector('img');
                        
                        // Extract all numbers from text
                        const priceMatches = text.match(/[\\d,]+/g);
                        const price = priceMatches ? priceMatches[priceMatches.length - 1] : "0";
                        
                        return {
                            title: text.split('\\n')[0] || "Hardoff Item",
                            price: price,
                            href: link ? link.href : "",
                            img: img ? img.src : ""
                        }
                    }""")
                    
                    href = data.get('href', '')
                    title = data.get('title', '')
                    price_str = data.get('price', '0')
                    img = data.get('img', '')
                    
                    # Skip if no href
                    if not href:
                        continue
                    
                    # Extract price
                    try:
                        price = int(price_str.replace(',', ''))
                    except (ValueError, TypeError):
                        price = 0
                    
                    # Skip excluded items
                    if any(kw in title for kw in EXCLUDED_KEYWORDS):
                        continue
                    
                    # Skip very cheap items
                    if price < 100:
                        continue
                    
                    # Create SourceItem
                    source_item = SourceItem(
                        source_channel=self.name,
                        source_url=href,
                        source_price=price,
                        source_currency='JPY',
                        condition_text='unknown',
                        product_title=title,
                        product_image_url=img,
                        observed_at=datetime.now().isoformat()
                    )
                    results.append(source_item)
                    
                except Exception as e:
                    print(f"  [Hardoff] Item parse error: {e}")
                    continue
            
            print(f"  [Hardoff] Found {len(results)} items")
            return results
            
        except Exception as e:
            print(f"  [Hardoff] Search failed: {e}")
            return []
    
    async def close(self):
        """Close the page."""
        try:
            await self.page.close()
        except Exception as e:
            print(f"  [Hardoff] Close error: {e}")

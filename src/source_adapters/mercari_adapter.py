"""
Mercari adapter - scrapes items from Mercari (jp.mercari.com).
Reused from the original eBay Research Edge search_mercari function.
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


class MercariAdapter(BaseSourceAdapter):
    """Mercari scraper adapter."""
    
    def __init__(self, page: Page):
        super().__init__()
        self.page = page
        self.name = 'メルカリ'
    
    async def search(self, keywords: List[str], genre: str = '') -> List[SourceItem]:
        """
        Search Mercari by keywords.
        
        Args:
            keywords: List of search keywords (preferably Japanese)
            genre: Product genre (added to query if not manual)
        
        Returns:
            List[SourceItem]: Matched items
        """
        if not keywords:
            return []
        
        # Build query: genre + keywords
        words = ([genre] if genre else []) + keywords
        unique_words = []
        for w in words:
            if w not in unique_words:
                unique_words.append(w)
        
        # Limit to 4 words to avoid too-specific queries
        query = ' '.join(unique_words[:4])
        
        try:
            url = f'https://jp.mercari.com/search?keyword={urllib.parse.quote(query, safe="")}&status=on_sale'
            print(f"  [Mercari] URL: {url}")
            
            # Navigate to URL
            try:
                await asyncio.wait_for(
                    self.page.goto(url, wait_until='domcontentloaded'),
                    timeout=BROWSER_GOTO_TIMEOUT_MS / 1000
                )
            except asyncio.TimeoutError:
                print(f"  [Mercari] Goto timeout: {url}")
                return []
            
            # Wait for product links to load
            try:
                await asyncio.wait_for(
                    self.page.wait_for_selector('a[href^="/item/m"]'),
                    timeout=BROWSER_SELECTOR_TIMEOUT_MS / 1000
                )
            except asyncio.TimeoutError:
                print(f"  [Mercari] No items found (timeout)")
                return []
            
            # Extract items
            items = await self.page.locator('a[href^="/item/m"]').all()
            results = []
            
            for item in items[:MAX_ITEMS_PER_SOURCE]:
                try:
                    data = await item.evaluate("""el => {
                        const imgDiv = el.querySelector('div[aria-label]');
                        const img = el.querySelector('img');
                        let rawTitle = imgDiv ? imgDiv.getAttribute('aria-label') : (img ? img.alt : "");
                        let title = rawTitle.replace(/の(画像|サムネイル).*$/, "").replace(/¥\\s?[\\d,]+/, "").trim();
                        return {
                            title: title,
                            price: el.innerText,
                            href: el.href,
                            img: img ? img.src : "",
                        }
                    }""")
                    
                    # Skip excluded items
                    title = data.get('title', '')
                    price_text = data.get('price', '')
                    if any(kw in title or kw in price_text for kw in EXCLUDED_KEYWORDS):
                        continue
                    
                    # Extract price
                    match = re.search(r'¥\s*([\d,]+)', price_text)
                    if not match:
                        continue
                    
                    price = int(match.group(1).replace(',', ''))
                    if price < 100:  # Skip very cheap items
                        continue
                    
                    # Create SourceItem
                    source_item = SourceItem(
                        source_channel=self.name,
                        source_url=data.get('href', ''),
                        source_price=price,
                        source_currency='JPY',
                        condition_text='unknown',
                        product_title=title,
                        product_image_url=data.get('img', ''),
                        observed_at=datetime.now().isoformat()
                    )
                    results.append(source_item)
                    
                except Exception as e:
                    print(f"  [Mercari] Item parse error: {e}")
                    continue
            
            print(f"  [Mercari] Found {len(results)} items")
            return results
            
        except Exception as e:
            print(f"  [Mercari] Search failed: {e}")
            return []
    
    async def close(self):
        """Close the page."""
        try:
            await self.page.close()
        except Exception as e:
            print(f"  [Mercari] Close error: {e}")

"""
Yahoo adapter - scrapes items from Yahoo PayPay Fleamarket and auction history.
Reused from the original eBay Research Edge search_yahoo and fetch_yahoo_auction_history functions.
"""

import re
import urllib.parse
import asyncio
from typing import List, Optional, Dict
from playwright.async_api import Page, Browser
from datetime import datetime

from src.source_adapters.base_adapter import BaseSourceAdapter, SourceItem
from src.source_adapters.config_adapters import (
    BROWSER_GOTO_TIMEOUT_MS,
    BROWSER_SELECTOR_TIMEOUT_MS,
    BROWSER_SHORT_WAIT_MS,
    EXCLUDED_KEYWORDS,
    MAX_ITEMS_PER_SOURCE,
    API_REQUEST_TIMEOUT_SECONDS,
)


class YahooFleamarketAdapter(BaseSourceAdapter):
    """Yahoo PayPay Fleamarket scraper adapter."""
    
    def __init__(self, page: Page):
        super().__init__()
        self.page = page
        self.name = 'ヤフーフリマ'
    
    async def search(self, keywords: List[str], genre: str = '') -> List[SourceItem]:
        """
        Search Yahoo PayPay Fleamarket by keywords.
        
        Args:
            keywords: List of search keywords (preferably Japanese)
            genre: Product genre (added to query if provided)
        
        Returns:
            List[SourceItem]: Matched items
        """
        if not keywords:
            return []
        
        # Build query: genre + keywords (up to 6 words)
        words = ([genre] if genre else []) + keywords
        unique_words = []
        for w in words:
            if w not in unique_words:
                unique_words.append(w)
        
        query = ' '.join(unique_words[:6])
        
        try:
            url = f"https://paypayfleamarket.yahoo.co.jp/search/{urllib.parse.quote(query, safe='')}?open=1"
            print(f"  [YahooFlea] URL: {url}")
            
            # Navigate to URL
            try:
                await asyncio.wait_for(
                    self.page.goto(url, wait_until='domcontentloaded'),
                    timeout=BROWSER_GOTO_TIMEOUT_MS / 1000
                )
            except asyncio.TimeoutError:
                print(f"  [YahooFlea] Goto timeout: {url}")
                return []
            
            # Wait for product links
            try:
                await asyncio.wait_for(
                    self.page.wait_for_selector('a[href*="/item/"]'),
                    timeout=BROWSER_SELECTOR_TIMEOUT_MS / 1000
                )
            except asyncio.TimeoutError:
                print(f"  [YahooFlea] No items found (timeout)")
                return []
            
            # Extract items
            items = await self.page.locator('a[href*="/item/"]').all()
            results = []
            
            for item in items[:MAX_ITEMS_PER_SOURCE]:
                try:
                    data = await item.evaluate("""el => {
                        const img = el.querySelector('img');
                        return {
                            title: img ? img.alt : "ヤフーフリマ商品",
                            allText: el.innerText,
                            href: el.href,
                            img: img ? img.src : ""
                        }
                    }""")
                    
                    title = data.get('title', '')
                    all_text = data.get('allText', '')
                    
                    # Skip excluded items
                    if any(kw in title or kw in all_text for kw in EXCLUDED_KEYWORDS):
                        continue
                    
                    # Extract price (multiple regex patterns for robustness)
                    price_match = re.search(r'([\d,]+)\s*円', all_text)
                    if not price_match:
                        price_match = re.search(r'¥\s*([\d,]+)', all_text)
                    
                    if not price_match:
                        # Last resort: find any line with 円 and extract numbers
                        m = re.search(r'.*円', all_text)
                        if m:
                            price_val = int(re.sub(r'[^\d]', '', m.group(0)))
                        else:
                            continue
                    else:
                        price_val = int(price_match.group(1).replace(',', ''))
                    
                    if price_val < 100:  # Skip very cheap items
                        continue
                    
                    # Create SourceItem
                    source_item = SourceItem(
                        source_channel=self.name,
                        source_url=data.get('href', ''),
                        source_price=price_val,
                        source_currency='JPY',
                        condition_text='unknown',
                        product_title=title,
                        product_image_url=data.get('img', ''),
                        observed_at=datetime.now().isoformat()
                    )
                    results.append(source_item)
                    
                except Exception as e:
                    print(f"  [YahooFlea] Item parse error: {e}")
                    continue
            
            print(f"  [YahooFlea] Found {len(results)} items")
            return results
            
        except Exception as e:
            print(f"  [YahooFlea] Search failed: {e}")
            return []
    
    async def close(self):
        """Close the page."""
        try:
            await self.page.close()
        except Exception as e:
            print(f"  [YahooFlea] Close error: {e}")


class YahooAuctionHistoryAdapter(BaseSourceAdapter):
    """Yahoo Auctions closed sale history adapter."""
    
    def __init__(self, browser: Browser):
        super().__init__()
        self.browser = browser
        self.name = 'ヤフオク履歴'
    
    async def search(self, keywords: List[str], genre: str = '') -> List[SourceItem]:
        """
        Fetch Yahoo Auction closed sale history.
        
        Returns statistics (min, max, median) rather than individual items.
        
        Args:
            keywords: Search keywords (can be list or joined string)
            genre: Ignored for auction history
        
        Returns:
            List[SourceItem]: Single item with aggregated price stats in title/notes
        """
        if not keywords:
            return []
        
        if isinstance(keywords, list):
            search_query = ' '.join(keywords)
        else:
            search_query = keywords
        
        try:
            page = await self.browser.new_page()
            
            try:
                encoded_query = urllib.parse.quote(search_query, safe='')
                url = f'https://auctions.yahoo.co.jp/closedsearch/closedsearch?p={encoded_query}&va={encoded_query}&b=1&n=50'
                print(f"  [YahooAuction] URL: {url}")
                
                # Navigate and wait for content
                try:
                    await asyncio.wait_for(
                        page.goto(url, wait_until='domcontentloaded'),
                        timeout=(BROWSER_GOTO_TIMEOUT_MS + 5000) / 1000
                    )
                except asyncio.TimeoutError:
                    print(f"  [YahooAuction] Goto timeout")
                    await page.close()
                    return []
                
                await page.wait_for_timeout(BROWSER_SHORT_WAIT_MS)
                
                # Extract prices from fontWeightBold elements
                prices = await page.evaluate("""() => {
                    const elements = document.querySelectorAll('[class*="fontWeightBold"]');
                    return Array.from(elements)
                        .map(el => el.innerText.replace(/[^0-9]/g, ''))
                        .filter(v => v.length >= 2)
                        .map(v => parseInt(v));
                }""")
                
                await page.close()
                
                if not prices:
                    print(f"  [YahooAuction] No price data found")
                    return []
                
                # Calculate statistics
                prices.sort()
                n = len(prices)
                
                # Remove outliers (top and bottom 10%)
                if n > 10:
                    trimmed = prices[max(1, n // 10):max(n, n - n // 10)]
                else:
                    trimmed = prices
                
                median = trimmed[len(trimmed) // 2]
                min_price = min(prices)
                max_price = max(prices)
                
                print(f"  [YahooAuction] Found {n} closed sales")
                print(f"    Min: ¥{min_price:,}, Median: ¥{median:,}, Max: ¥{max_price:,}")
                
                # Return aggregated stats as a single SourceItem
                # (This is a special item that represents market history, not a product to buy)
                source_item = SourceItem(
                    source_channel=self.name,
                    source_url=url,
                    source_price=median,  # Use median as representative price
                    source_currency='JPY',
                    condition_text=f'closed_sales_n{n}',
                    product_title=f'落札相場 ({n}件)',
                    product_image_url='',
                    observed_at=datetime.now().isoformat()
                )
                
                # Store extended stats in notes (non-standard, for reference)
                source_item._stats = {
                    'min': min_price,
                    'max': max_price,
                    'median': median,
                    'count': n,
                    'url': url
                }
                
                return [source_item]
                
            except Exception as e:
                print(f"  [YahooAuction] Parse error: {e}")
                await page.close()
                return []
            
        except Exception as e:
            print(f"  [YahooAuction] Search failed: {e}")
            return []

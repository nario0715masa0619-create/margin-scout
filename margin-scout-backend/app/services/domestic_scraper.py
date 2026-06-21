"""
Domestic flea market scrapers (Mercari, Yahoo Fril, Rakuma)
Playwright (Browser Automation) 版
"""

import logging
import re
import urllib.parse
from typing import Dict, List

logger = logging.getLogger(__name__)


class MercariScraper:
    """メルカリ スクレイパー（Playwright）"""
    
    async def scrape(self, keyword: str, page) -> List[Dict]:
        """
        メルカリから商品を検索
        
        Args:
            keyword: 検索キーワード
            page: Playwright Page object
        
        Returns:
            商品リスト
        """
        try:
            # EREのロジックを踏襲してクエリを作成
            query = urllib.parse.quote(keyword, safe="")
            url = f"https://jp.mercari.com/search?keyword={query}&status=on_sale&order=NEWEST"
            
            logger.info(f"Navigating to Mercari: {url}")
            await page.goto(url, timeout=30000)
            
            # 商品要素がレンダリングされるまで待機（スケルトンから実際の商品カードに変わるまで）
            try:
                await page.wait_for_selector('a[href^="/item/m"]', timeout=10000)
            except Exception as e:
                logger.warning(f"Mercari: Timeout waiting for items for '{keyword}'. It might be 0 hits.")
            
            items_locator = await page.locator('a[href^="/item/m"]').all()
            items = []
            
            for it in items_locator[:15]:
                try:
                    d = await it.evaluate("""el => {
                        const imgDiv = el.querySelector('div[aria-label]');
                        const img = el.querySelector('img');
                        let rawTitle = imgDiv ? imgDiv.getAttribute('aria-label') : (img ? img.alt : "");
                        let title = rawTitle.replace(/の(画像|サムネイル).*$/, "").replace(/¥\s?[\d,]+/, "").trim();
                        
                        let priceText = el.innerText;
                        
                        return {
                            title: title,
                            price: priceText,
                            href: el.href,
                            img: img ? img.src : ""
                        }
                    }""")
                    
                    # 価格の抽出 (¥ 1,234 -> 1234)
                    price_val = 0
                    m = re.search(r'¥\s*([\d,]+)', d['price'])
                    if m:
                        price_val = int(m.group(1).replace(',', ''))
                    
                    if not d['title']:
                        continue
                        
                    if price_val > 0:
                        items.append({
                            'title': f"[MERCARI] {d['title']}",
                            'price': price_val,
                            'url': d['href'],
                            'image': d['img'],
                            'source': 'mercari'
                        })
                except Exception as e:
                    logger.debug(f"Failed to parse Mercari item: {e}")
                    continue
            
            logger.info(f'✓ Mercari: {len(items)} items found for "{keyword}"')
            return items
            
        except Exception as e:
            logger.error(f"Mercari scrape error: {e}")
            return []


class YahooFrilScraper:
    """ヤフーフリマ スクレイパー（Playwright）"""
    
    async def scrape(self, keyword: str, page) -> List[Dict]:
        """
        ヤフーフリマから商品を検索
        """
        try:
            query = urllib.parse.quote(keyword, safe="")
            url = f"https://paypayfleamarket.yahoo.co.jp/search/{query}?open=1"
            
            logger.info(f"Navigating to Yahoo Fril: {url}")
            await page.goto(url, timeout=30000)
            
            try:
                await page.wait_for_selector('a[href*="/item/"]', timeout=10000)
            except Exception:
                logger.warning(f"Yahoo Fril: Timeout waiting for items for '{keyword}'.")
            
            items_locator = await page.locator('a[href*="/item/"]').all()
            items = []
            
            for it in items_locator[:15]:
                try:
                    d = await it.evaluate("""el => {
                        const img = el.querySelector('img');
                        return {
                            title: img ? img.alt : "ヤフーフリマ商品",
                            allText: el.innerText,
                            href: el.href,
                            img: img ? img.src : ""
                        }
                    }""")
                    
                    price_val = 0
                    price_match = re.search(r'([\d,]+)\s*円', d['allText'])
                    if not price_match:
                        price_match = re.search(r'¥\s*([\d,]+)', d['allText'])
                    
                    if price_match:
                        price_val = int(price_match.group(1).replace(',', ''))
                    else:
                        m = re.search(r'.*円', d['allText'])
                        if m:
                            price_val = int(re.sub(r'[^\d]', '', m.group(0)))
                    
                    if price_val > 0:
                        items.append({
                            'title': f"[YAHOO FRIL] {d['title']}",
                            'price': price_val,
                            'url': d['href'],
                            'image': d['img'],
                            'source': 'yahoo_fril'
                        })
                except Exception as e:
                    logger.debug(f"Failed to parse Yahoo item: {e}")
                    continue
            
            logger.info(f'✓ Yahoo Fril: {len(items)} items found for "{keyword}"')
            return items
            
        except Exception as e:
            logger.error(f"Yahoo Fril scrape error: {e}")
            return []


class RakumaScraper:
    """ラクマ スクレイパー（Playwright）"""
    
    async def scrape(self, keyword: str, page) -> List[Dict]:
        """
        ラクマから商品を検索
        """
        try:
            query = urllib.parse.quote(keyword, safe="")
            url = f"https://item.rakuma.com/search?keyword={query}&sort=recently_updated"
            
            logger.info(f"Navigating to Rakuma: {url}")
            await page.goto(url, timeout=30000)
            
            # Rakuma はCloudflare検知後、商品要素が表示されるのを待つ
            try:
                await page.wait_for_selector('div.item-card', timeout=15000)
            except Exception:
                logger.warning(f"Rakuma: Timeout waiting for items for '{keyword}'. Possible Cloudflare block.")
            
            items_locator = await page.locator('div.item-card').all()
            items = []
            
            for it in items_locator[:15]:
                try:
                    d = await it.evaluate("""el => {
                        const linkElem = el.querySelector('a');
                        const titleElem = el.querySelector('a.item-title') || el.querySelector('h3');
                        const priceElem = el.querySelector('span.item-price') || el.querySelector('span.price');
                        const imgElem = el.querySelector('img');
                        
                        return {
                            href: linkElem ? linkElem.href : "",
                            title: titleElem ? titleElem.innerText.trim() : "",
                            priceText: priceElem ? priceElem.innerText.trim() : "0",
                            img: imgElem ? imgElem.src : ""
                        }
                    }""")
                    
                    price_val = 0
                    if d['priceText']:
                        price_val = float(re.sub(r'[¥,]', '', d['priceText']))
                        
                    if d['title'] and price_val > 0:
                        items.append({
                            'title': f"[RAKUMA] {d['title']}",
                            'price': price_val,
                            'url': d['href'],
                            'image': d['img'],
                            'source': 'rakuma'
                        })
                except Exception as e:
                    logger.debug(f"Failed to parse Rakuma item: {e}")
                    continue
            
            logger.info(f'✓ Rakuma: {len(items)} items found for "{keyword}"')
            return items
            
        except Exception as e:
            logger.error(f"Rakuma scrape error: {e}")
            return []


class DomesticScraperFactory:
    """国内フリマ スクレイパー ファクトリー"""
    
    @staticmethod
    def get_scraper(platform: str):
        if platform == 'mercari':
            return MercariScraper()
        elif platform == 'yahoo_fril':
            return YahooFrilScraper()
        elif platform == 'rakuma':
            return RakumaScraper()
        else:
            raise ValueError(f'Unknown platform: {platform}')

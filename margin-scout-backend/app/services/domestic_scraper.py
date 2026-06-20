"""
Domestic flea market scrapers (Mercari, Yahoo Fril, Rakuma)
"""

import logging
from typing import Dict, List
from bs4 import BeautifulSoup
import json
from app.services.scraping_clients import ScrapeDoClient, DiffbotClient

logger = logging.getLogger(__name__)


class MercariScraper:
    """メルカリ スクレイパー"""
    
    def __init__(self):
        self.client = ScrapeDoClient()
    
    async def scrape(self, keyword: str, conditions: Dict = None) -> List[Dict]:
        """
        メルカリから商品を検索
        
        Args:
            keyword: 検索キーワード
            conditions: フィルター条件（例：on_sale, price_range）
        
        Returns:
            商品リスト [{'title': str, 'price': float, 'url': str, 'source': 'mercari'}, ...]
        """
        conditions = conditions or {}
        search_url = f"https://jp.mercari.com/search?keyword={keyword}&order=NEWEST"
        
        try:
            result = await self.client.scrape(search_url, render_js=True)
            if result['status'] != 200:
                logger.error(f"Mercari scrape failed: {result}")
                return []
            
            html = result['content']
            soup = BeautifulSoup(html, 'html.parser')
            
            items = []
            # メルカリの商品カード要素を検索（product-card-anchor）
            cards = soup.find_all('a', class_='product-card-anchor')
            
            for card in cards:
                try:
                    title_elem = card.find('span', class_='product-name')
                    price_elem = card.find('span', class_='product-price')
                    
                    if not title_elem or not price_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    price_text = price_elem.get_text(strip=True)
                    price = float(price_text.replace('¥', '').replace(',', ''))
                    
                    item_url = card.get('href', '')
                    
                    items.append({
                        'title': title,
                        'price': price,
                        'url': f"https://jp.mercari.com{item_url}" if item_url.startswith('/') else item_url,
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
    """ヤフーフリマ スクレイパー"""
    
    def __init__(self):
        self.client = DiffbotClient()
    
    async def scrape(self, keyword: str, conditions: Dict = None) -> List[Dict]:
        """
        ヤフーフリマから商品を検索（Diffbot Knowledge Graph）
        
        Args:
            keyword: 検索キーワード
            conditions: フィルター条件
        
        Returns:
            商品リスト [{'title': str, 'price': float, 'url': str, 'source': 'yahoo_fril'}, ...]
        """
        conditions = conditions or {}
        search_url = f"https://fril.jp/search?keyword={keyword}&sort=recent"
        
        try:
            result = await self.client.extract(search_url)
            
            if 'error' in result:
                logger.error(f"Yahoo Fril scrape failed: {result['error']}")
                return []
            
            items = []
            objects = result.get('objects', [])
            
            for obj in objects:
                try:
                    title = obj.get('title', '')
                    price = obj.get('price', 0)
                    url = obj.get('pageUrl', '')
                    
                    if not title or not url:
                        continue
                    
                    # price が文字列の場合は数値に変換
                    if isinstance(price, str):
                        price = float(price.replace('¥', '').replace(',', ''))
                    
                    items.append({
                        'title': title,
                        'price': price,
                        'url': url,
                        'source': 'yahoo_fril'
                    })
                except Exception as e:
                    logger.debug(f"Failed to parse Yahoo Fril item: {e}")
                    continue
            
            logger.info(f'✓ Yahoo Fril: {len(items)} items found for "{keyword}"')
            return items
        
        except Exception as e:
            logger.error(f"Yahoo Fril scrape error: {e}")
            return []


class RakumaScraper:
    """ラクマ スクレイパー"""
    
    def __init__(self):
        self.client = ScrapeDoClient()
    
    async def scrape(self, keyword: str, conditions: Dict = None) -> List[Dict]:
        """
        ラクマから商品を検索
        
        Args:
            keyword: 検索キーワード
            conditions: フィルター条件
        
        Returns:
            商品リスト [{'title': str, 'price': float, 'url': str, 'source': 'rakuma'}, ...]
        """
        conditions = conditions or {}
        search_url = f"https://item.rakuma.com/search?keyword={keyword}&sort=recently_updated"
        
        try:
            result = await self.client.scrape(search_url, render_js=True)
            if result['status'] != 200:
                logger.error(f"Rakuma scrape failed: {result}")
                return []
            
            html = result['content']
            soup = BeautifulSoup(html, 'html.parser')
            
            items = []
            # ラクマの商品カード要素を検索
            cards = soup.find_all('div', class_='item-card')
            
            for card in cards:
                try:
                    title_elem = card.find('a', class_='item-title')
                    price_elem = card.find('span', class_='item-price')
                    
                    if not title_elem or not price_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    price_text = price_elem.get_text(strip=True)
                    price = float(price_text.replace('¥', '').replace(',', ''))
                    
                    item_url = title_elem.get('href', '')
                    
                    items.append({
                        'title': title,
                        'price': price,
                        'url': f"https://item.rakuma.com{item_url}" if item_url.startswith('/') else item_url,
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
        """
        Args:
            platform: 'mercari', 'yahoo_fril', 'rakuma'
        
        Returns:
            対応するスクレイパーインスタンス
        """
        if platform == 'mercari':
            return MercariScraper()
        elif platform == 'yahoo_fril':
            return YahooFrilScraper()
        elif platform == 'rakuma':
            return RakumaScraper()
        else:
            raise ValueError(f'Unknown platform: {platform}')

"""
Domestic flea market scrapers (Mercari, Yahoo Fril, Rakuma)
BeautifulSoup 直接解析版（API キー不要）
"""

import logging
import re
from typing import Dict, List
from bs4 import BeautifulSoup
import httpx

logger = logging.getLogger(__name__)


class MercariScraper:
    """メルカリ スクレイパー（BeautifulSoup 直接解析）"""
    
    async def scrape(self, keyword: str, conditions: Dict = None) -> List[Dict]:
        """
        メルカリから商品を検索
        
        Args:
            keyword: 検索キーワード
            conditions: フィルター条件
        
        Returns:
            商品リスト
        """
        conditions = conditions or {}
        search_url = f"https://jp.mercari.com/search?keyword={keyword}&order=NEWEST"
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # User-Agent を設定してブロック回避
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                resp = await client.get(search_url, headers=headers, follow_redirects=True)
                
                if resp.status_code != 200:
                    logger.error(f"Mercari HTTP error: {resp.status_code}")
                    return []
                
                html = resp.text
                soup = BeautifulSoup(html, 'html.parser')
                
                items = []
                # メルカリの商品カード要素を検索
                cards = soup.find_all('a', {'data-testid': 'product-card-anchor'})
                
                for card in cards:
                    try:
                        # 商品 URL
                        url = card.get('href', '')
                        if not url.startswith('http'):
                            url = f"https://jp.mercari.com{url}"
                        
                        # タイトル
                        title_elem = card.find('h2') or card.find('div', class_='product-name')
                        title = title_elem.get_text(strip=True) if title_elem else ''
                        
                        # 価格
                        price_elem = card.find('span', class_='product-price')
                        price_text = price_elem.get_text(strip=True) if price_elem else '0'
                        price = float(re.sub(r'[¥,]', '', price_text)) if price_text else 0
                        
                        if title and price > 0:
                            items.append({
                                'title': f'[MERCARI] {title}',
                                'price': price,
                                'url': url,
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
    """ヤフーフリマ スクレイパー（BeautifulSoup 直接解析）"""
    
    async def scrape(self, keyword: str, conditions: Dict = None) -> List[Dict]:
        """
        ヤフーフリマから商品を検索
        
        Args:
            keyword: 検索キーワード
            conditions: フィルター条件
        
        Returns:
            商品リスト
        """
        conditions = conditions or {}
        search_url = f"https://fril.jp/search?keyword={keyword}&sort=recent"
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                resp = await client.get(search_url, headers=headers, follow_redirects=True)
                
                if resp.status_code != 200:
                    logger.error(f"Yahoo Fril HTTP error: {resp.status_code}")
                    return []
                
                html = resp.text
                soup = BeautifulSoup(html, 'html.parser')
                
                items = []
                # ヤフーフリマの商品セルを検索
                cards = soup.find_all('a', class_='search-item-container')
                
                for card in cards:
                    try:
                        url = card.get('href', '')
                        if not url.startswith('http'):
                            url = f"https://fril.jp{url}"
                        
                        # タイトル
                        title_elem = card.find('h3') or card.find('div', class_='item-title')
                        title = title_elem.get_text(strip=True) if title_elem else ''
                        
                        # 価格
                        price_elem = card.find('span', class_='item-price')
                        price_text = price_elem.get_text(strip=True) if price_elem else '0'
                        price = float(re.sub(r'[¥,]', '', price_text)) if price_text else 0
                        
                        if title and price > 0:
                            items.append({
                                'title': f'[YAHOO FRIL] {title}',
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
    """ラクマ スクレイパー（BeautifulSoup 直接解析）"""
    
    async def scrape(self, keyword: str, conditions: Dict = None) -> List[Dict]:
        """
        ラクマから商品を検索
        
        Args:
            keyword: 検索キーワード
            conditions: フィルター条件
        
        Returns:
            商品リスト
        """
        conditions = conditions or {}
        search_url = f"https://item.rakuma.com/search?keyword={keyword}&sort=recently_updated"
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                resp = await client.get(search_url, headers=headers, follow_redirects=True)
                
                if resp.status_code != 200:
                    logger.error(f"Rakuma HTTP error: {resp.status_code}")
                    return []
                
                html = resp.text
                soup = BeautifulSoup(html, 'html.parser')
                
                items = []
                # ラクマの商品カード要素を検索
                cards = soup.find_all('div', class_='item-card')
                
                for card in cards:
                    try:
                        # リンク要素
                        link_elem = card.find('a')
                        url = link_elem.get('href', '') if link_elem else ''
                        if not url.startswith('http'):
                            url = f"https://item.rakuma.com{url}"
                        
                        # タイトル
                        title_elem = card.find('a', class_='item-title')
                        title = title_elem.get_text(strip=True) if title_elem else ''
                        
                        # 価格
                        price_elem = card.find('span', class_='item-price')
                        price_text = price_elem.get_text(strip=True) if price_elem else '0'
                        price = float(re.sub(r'[¥,]', '', price_text)) if price_text else 0
                        
                        if title and price > 0:
                            items.append({
                                'title': f'[RAKUMA] {title}',
                                'price': price,
                                'url': url,
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

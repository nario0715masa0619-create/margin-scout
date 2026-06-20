"""
Scraping integration module with httpx (async-compatible)
Supports: Scrape.do, Diffbot
"""

import httpx
import logging
from typing import Dict, Optional
from app.config import settings

logger = logging.getLogger(__name__)


class ScrapeDoClient:
    """Scrape.do API クライアント (httpx 非同期対応)"""
    
    def __init__(self):
        self.api_key = settings.SCRAPEDO_API_KEY
        self.base_url = "https://api.scrape.do"
    
    async def scrape(self, url: str, render_js: bool = True) -> Dict:
        """
        URL をスクレイピング
        
        Args:
            url: ターゲット URL
            render_js: JavaScript レンダリングを有効にするか
        
        Returns:
            {'status': 200, 'content': html_content} または {'status': error_code, 'error': msg}
        """
        params = {
            'token': self.api_key,
            'url': url,
            'render': 'true' if render_js else 'false',
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(self.base_url, params=params)
                if resp.status_code == 200:
                    logger.info(f'✓ Scrape.do: {url[:50]}... fetched ({len(resp.text)} bytes)')
                    return {'status': 200, 'content': resp.text}
                else:
                    logger.error(f'Scrape.do error: {resp.status_code}')
                    return {'status': resp.status_code, 'error': resp.text}
        except Exception as e:
            logger.error(f'Scrape.do request failed: {e}')
            return {'status': 0, 'error': str(e)}


class DiffbotClient:
    """Diffbot API クライアント (httpx 非同期対応)"""
    
    def __init__(self):
        self.api_token = settings.DIFFBOT_API_TOKEN
        self.base_url = "https://api.diffbot.com/v3/extract"
    
    async def extract(self, url: str) -> Dict:
        """
        ページから構造化データを抽出
        
        Args:
            url: ターゲット URL
        
        Returns:
            {'objects': [...], 'status': 'success'} または {'error': msg}
        """
        params = {'token': self.api_token, 'url': url}
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(self.base_url, params=params)
                data = resp.json()
                logger.info(f'✓ Diffbot: {url[:50]}... extracted')
                return data
        except Exception as e:
            logger.error(f'Diffbot request failed: {e}')
            return {'error': str(e)}


class ScrapingFactory:
    """スクレイピングクライアント ファクトリー"""
    
    @staticmethod
    def get_client(service: str):
        if service == 'scrapedo':
            return ScrapeDoClient()
        elif service == 'diffbot':
            return DiffbotClient()
        else:
            raise ValueError(f'Unknown service: {service}')

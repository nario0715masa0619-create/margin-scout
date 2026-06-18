import httpx
from typing import Dict, Any
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class BrowserlessClient:
    """Browserless.io API クライアント"""
    def __init__(self):
        self.api_key = settings.BROWSERLESS_API_KEY
        self.api_url = settings.BROWSERLESS_API_URL
        self.timeout = settings.BROWSERLESS_TIMEOUT_SEC
        self.headers = {
            "Content-Type": "application/json",
            "Cache-Control": "no-cache"
        }

    async def request(self, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Browserless API 呼び出し"""
        url = f"{self.api_url}/function?token={self.api_key}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    headers=self.headers,
                    json=payload
                )
                
                if response.status_code == 401:
                    logger.error("Browserless authentication failed (401)")
                    raise ValueError("Browserless API Key is invalid")
                elif response.status_code == 429:
                    logger.error("Browserless rate limit exceeded (429)")
                    raise ConnectionError("Browserless Rate Limit Exceeded")
                elif response.status_code >= 500:
                    logger.error(f"Browserless service down ({response.status_code})")
                    raise ConnectionError("Browserless Service Unavailable")
                
                response.raise_for_status()
                return response.json()
                
        except httpx.TimeoutException:
            logger.error("Browserless request timed out")
            raise TimeoutError("Browserless request timed out")
        except httpx.RequestError as e:
            logger.error(f"Browserless request error: {e}")
            raise ConnectionError(f"Browserless request error: {str(e)}")

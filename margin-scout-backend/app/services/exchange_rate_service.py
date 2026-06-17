import httpx
from functools import lru_cache
from datetime import datetime, timedelta

class ExchangeRateService:
    # キャッシュ: 1時間ごとに更新
    _cache_time = None
    _cache_rate = None
    CACHE_DURATION = timedelta(hours=1)
    
    @classmethod
    async def get_usd_to_jpy_rate(cls) -> float:
        now = datetime.now()
        
        # キャッシュが有効か確認
        if cls._cache_rate and cls._cache_time:
            if now - cls._cache_time < cls.CACHE_DURATION:
                return cls._cache_rate
        
        # 実際のレート取得（例: Open Exchange Rates または Fixer API）
        try:
            async with httpx.AsyncClient() as client:
                # 無料 API: exchangerate-api.com
                response = await client.get(
                    'https://api.exchangerate-api.com/v4/latest/USD',
                    timeout=5.0
                )
                data = response.json()
                rate = data['rates']['JPY']
                
                # キャッシュ更新
                cls._cache_rate = rate
                cls._cache_time = now
                return rate
        except Exception as e:
            # API 失敗時はデフォルト値（150.0）を返す
            return 150.0

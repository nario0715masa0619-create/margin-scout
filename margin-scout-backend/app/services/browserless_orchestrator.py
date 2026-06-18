from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from uuid import uuid4
import time
import logging

from app.models.research import UsageLog, SourceItem
from app.schemas.saved_searches import FilterSchema, SourceEnum
from app.services.browserless_client import BrowserlessClient
from app.config import settings

logger = logging.getLogger(__name__)

@dataclass
class CaptureResult:
    success: bool
    items: List[Dict[str, Any]]
    fallback_provider: str
    error: Optional[str]
    retry_count: int
    cost_estimate_jpy: float
    execution_time_ms: int

class FallbackProvider(ABC):
    @abstractmethod
    async def capture(self, filters: FilterSchema) -> CaptureResult:
        pass

    @abstractmethod
    async def supports_source(self, source: SourceEnum) -> bool:
        pass

    @abstractmethod
    async def get_max_retries(self) -> int:
        pass

class BaseProvider(FallbackProvider):
    def __init__(self, provider_name: str):
        self.provider_name = provider_name
        self.client = BrowserlessClient()

    async def get_max_retries(self) -> int:
        return settings.BROWSERLESS_MAX_RETRIES

    def _build_payload(self, filters: FilterSchema) -> Dict[str, Any]:
        payload = {
            "action": "search",
            "keywords": filters.keyword,
        }
        if filters.conditions:
            payload["conditions"] = [c.value for c in filters.conditions]
        if filters.price_range:
            payload["price_range"] = {}
            if filters.price_range.min is not None:
                payload["price_range"]["min"] = filters.price_range.min
            if filters.price_range.max is not None:
                payload["price_range"]["max"] = filters.price_range.max
        if filters.sort:
            payload["sort"] = filters.sort.value
        return payload

    async def _execute_with_retry(self, payload: Dict[str, Any]) -> CaptureResult:
        max_retries = await self.get_max_retries()
        retries = 0
        last_error = None
        start_time = time.time()
        
        while retries <= max_retries:
            try:
                response = await self.client.request(payload["action"], payload)
                items = response.get("items", [])
                
                execution_time_ms = int((time.time() - start_time) * 1000)
                # 仮のコスト計算
                cost_estimate = 0.5 * len(items)
                
                return CaptureResult(
                    success=True,
                    items=items,
                    fallback_provider=self.provider_name,
                    error=None,
                    retry_count=retries,
                    cost_estimate_jpy=cost_estimate,
                    execution_time_ms=execution_time_ms
                )
            except Exception as e:
                last_error = str(e)
                retries += 1
                if retries <= max_retries:
                    time.sleep(1) # simple backoff
        
        execution_time_ms = int((time.time() - start_time) * 1000)
        return CaptureResult(
            success=False,
            items=[],
            fallback_provider=self.provider_name,
            error=last_error,
            retry_count=retries - 1,
            cost_estimate_jpy=0.0,
            execution_time_ms=execution_time_ms
        )

class MercariProvider(BaseProvider):
    def __init__(self):
        super().__init__("browserless_mercari")

    async def capture(self, filters: FilterSchema) -> CaptureResult:
        payload = self._build_payload(filters)
        payload["target"] = "mercari"
        return await self._execute_with_retry(payload)

    async def supports_source(self, source: SourceEnum) -> bool:
        return source == SourceEnum.MERCARI

class YahooAuctionProvider(BaseProvider):
    def __init__(self):
        super().__init__("browserless_yahoo_auction")

    async def capture(self, filters: FilterSchema) -> CaptureResult:
        payload = self._build_payload(filters)
        payload["target"] = "yahoo_auction"
        return await self._execute_with_retry(payload)

    async def supports_source(self, source: SourceEnum) -> bool:
        return source == SourceEnum.YAHOO_AUCTION

class YahooFleaProvider(BaseProvider):
    def __init__(self):
        super().__init__("browserless_yahoo_flea")

    async def capture(self, filters: FilterSchema) -> CaptureResult:
        payload = self._build_payload(filters)
        payload["target"] = "yahoo_flea"
        return await self._execute_with_retry(payload)

    async def supports_source(self, source: SourceEnum) -> bool:
        return source == SourceEnum.YAHOO_FLEA

class BrowserlessOrchestrator:
    def __init__(self, db: Session, user_id: str):
        self.db = db
        self.user_id = user_id
        self.providers: List[FallbackProvider] = [
            MercariProvider(),
            YahooAuctionProvider(),
            YahooFleaProvider()
        ]

    async def execute_with_fallback(self, source: str, filters: FilterSchema, fallback_reason: str, user_id: str) -> CaptureResult:
        try:
            source_enum = SourceEnum(source)
        except ValueError:
            return CaptureResult(
                success=False,
                items=[],
                fallback_provider="none",
                error="Invalid source",
                retry_count=0,
                cost_estimate_jpy=0.0,
                execution_time_ms=0
            )

        selected_provider = None
        for provider in self.providers:
            if await provider.supports_source(source_enum):
                selected_provider = provider
                break
                
        if not selected_provider:
            return CaptureResult(
                success=False,
                items=[],
                fallback_provider="none",
                error="No provider available for this source",
                retry_count=0,
                cost_estimate_jpy=0.0,
                execution_time_ms=0
            )

        # 実行
        result = await selected_provider.capture(filters)

        # UsageLog 記録
        usage_log = UsageLog(
            id=uuid4(),
            user_id=self.user_id,
            source=fallback_reason,
            fallback_provider=result.fallback_provider,
            success=result.success,
            item_count=len(result.items),
            cost_estimate=result.cost_estimate_jpy
        )
        self.db.add(usage_log)
        self.db.commit()

        # SourceItem を保存する場合はここで登録するが、
        # 現状は呼び出し元 (Router) が ImportSession に紐づけて登録する設計
        
        return result

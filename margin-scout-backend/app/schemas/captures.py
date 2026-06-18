from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum

class SourceEnum(str, Enum):
    MERCARI = "mercari"
    YAHOO_AUCTION = "yahoo_auction"
    YAHOO_FLEA = "yahoo_flea"

class ConditionEnum(str, Enum):
    NEW = "new"
    ALMOST_NEW = "almost_new"
    GOOD = "good"
    FAIR = "fair"
    USED = "used"

class ImportTypeEnum(str, Enum):
    MANUAL = "manual"
    AUTO = "auto"
    MONITORING = "monitoring"

# Request スキーマ
class SourceItemRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    price_jpy: int = Field(..., ge=1)
    url: HttpUrl
    image_url: Optional[HttpUrl] = None
    seller_name: Optional[str] = None
    condition: Optional[ConditionEnum] = None
    category: Optional[str] = None
    fetched_at: datetime

class CapturesRequest(BaseModel):
    source: SourceEnum
    import_type: Optional[ImportTypeEnum] = ImportTypeEnum.MANUAL
    items: List[SourceItemRequest] = Field(..., min_length=1, max_length=100)

# Response スキーマ
class SourceItemResponse(BaseModel):
    id: str
    title: str
    price_jpy: int
    url: str
    status: str  # "matched", "unmatched", "error"

class CapturesResponse(BaseModel):
    import_session_id: str
    processed_count: int
    matched_count: int
    error_count: int
    results: List[SourceItemResponse]
    rate_limit_remaining: int

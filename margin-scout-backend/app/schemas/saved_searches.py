from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
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

class SortEnum(str, Enum):
    DATE_DESC = "date_desc"
    PROFIT_DESC = "profit_desc"
    MARGIN_DESC = "margin_desc"

class PriceRangeSchema(BaseModel):
    min: Optional[int] = Field(None, ge=1)
    max: Optional[int] = Field(None, ge=1)
    
    @validator('max')
    def max_gt_min(cls, v, values):
        if v and 'min' in values and values['min'] and v < values['min']:
            raise ValueError('max must be >= min')
        return v

class OptionsSchema(BaseModel):
    on_sale: Optional[bool] = None
    fixed_price: Optional[bool] = None
    auction: Optional[bool] = None
    
    class Config:
        extra = 'allow'  # 他の options も許可

class FilterSchema(BaseModel):
    """検索条件フィルタ"""
    keyword: str = Field(..., min_length=1, max_length=256)
    options: Optional[OptionsSchema] = None
    conditions: Optional[List[ConditionEnum]] = []
    price_range: Optional[PriceRangeSchema] = None
    sort: Optional[SortEnum] = SortEnum.DATE_DESC
    exclude_keywords: Optional[List[str]] = []

class SavedSearchCreateRequest(BaseModel):
    """保存検索作成リクエスト"""
    name: str = Field(..., min_length=1, max_length=256)
    source: SourceEnum
    filters: FilterSchema
    is_monitoring_enabled: bool = False
    monitoring_interval_hours: int = Field(24, ge=1, le=24*7)  # 1時間～7日

class SavedSearchUpdateRequest(BaseModel):
    """保存検索更新リクエスト"""
    name: Optional[str] = Field(None, min_length=1, max_length=256)
    filters: Optional[FilterSchema] = None
    is_monitoring_enabled: Optional[bool] = None
    monitoring_interval_hours: Optional[int] = Field(None, ge=1, le=24*7)

from uuid import UUID
class SavedSearchResponse(BaseModel):
    """保存検索レスポンス"""
    id: UUID
    name: str
    source: str
    filters: Dict[str, Any]
    is_monitoring_enabled: bool
    monitoring_interval_hours: int
    next_run_at: Optional[datetime]
    last_run_at: Optional[datetime]
    last_run_status: str
    last_run_error: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

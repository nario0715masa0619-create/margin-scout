from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.models.research_job import JobStatus

from enum import Enum

class SearchOptionEnum(str, Enum):
    on_sale = "on_sale"
    sold_out = "sold_out"
    fixed_price = "fixed_price"
    auction = "auction"

class ItemConditionEnum(str, Enum):
    new = "new"
    almost_new = "almost_new"
    no_scratches = "no_scratches"
    slight_scratches = "slight_scratches"
    scratched = "scratched"
    bad_condition = "bad_condition"

class JobConditions(BaseModel):
    keywords: List[str]
    sources: List[str]
    days_back: int
    min_sales: int
    selected_options: List[SearchOptionEnum] = Field(default_factory=list)
    selected_conditions: List[ItemConditionEnum] = Field(default_factory=list)

class JobRequest(BaseModel):
    title: Optional[str] = "Untitled Research"
    conditions: JobConditions = Field(..., description="検索条件（キーワード、価格帯など）")

class JobResponse(BaseModel):
    id: str
    user_id: str
    title: Optional[str]
    status: JobStatus
    progress: int
    total_items: int
    matched_items: int
    conditions: Optional[Dict[str, Any]]
    result_summary: Optional[Dict[str, Any]]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

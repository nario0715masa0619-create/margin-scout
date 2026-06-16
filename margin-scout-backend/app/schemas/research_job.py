from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.models.research_job import JobStatus

class JobRequest(BaseModel):
    title: Optional[str] = "Untitled Research"
    conditions: Dict[str, Any] = Field(..., description="検索条件（キーワード、価格帯など）")

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

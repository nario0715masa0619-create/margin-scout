"""
Chrome 拡張機能からのデータ受け入れ API
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.research_job import ResearchJob, JobStatus
from datetime import datetime

router = APIRouter(prefix="/api/extension", tags=["extension"])


class ItemData(BaseModel):
    title: str
    price: float
    url: str
    source: str


class ExtensionItemsRequest(BaseModel):
    items: List[ItemData]


@router.post("/research-jobs/{job_id}/items")
def receive_extension_items(job_id: str, request: ExtensionItemsRequest, db: Session = Depends(get_db)):
    """
    Chrome 拡張機能からスクレイプされたアイテムを受け取る
    """
    try:
        # ジョブを取得
        job = db.query(ResearchJob).filter(ResearchJob.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # 既存の mercari_items を取得し、拡張機能からの結果を結合する
        current_summary = job.result_summary or {}
        existing_mercari = current_summary.get("mercari_items", [])
            
        new_items = []
        for item in request.items:
            new_items.append({
                "title": item.title,
                "price": {"value": str(item.price), "currency": "JPY"},
                "itemId": item.url,
                "itemWebUrl": item.url,
                "image": {"imageUrl": "https://via.placeholder.com/150"},
                "source": item.source
            })
            
        all_mercari_items = existing_mercari + new_items
        
        # ジョブを更新
        current_summary["mercari_items"] = all_mercari_items
        job.result_summary = current_summary
        
        # JSONカラムの更新を検知させる
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(job, "result_summary")
        
        job.matched_items = (job.matched_items or 0) + len(request.items)
        job.progress = 90  # 拡張機能からのデータ受け取り中
        
        db.commit()
        
        return {
            "status": "success",
            "count": len(request.items),
            "job_id": job_id
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/research-jobs/{job_id}/complete")
def mark_job_complete(job_id: str, db: Session = Depends(get_db)):
    """
    拡張機能がスクレイピング完了を通知
    """
    try:
        job = db.query(ResearchJob).filter(ResearchJob.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        job.status = JobStatus.completed
        job.progress = 100
        # completed_at などのカラムが存在する場合はセットする
        
        db.commit()
        
        return {"status": "success", "job_id": job_id}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

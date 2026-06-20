from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.dependencies import get_current_user_id
from app.schemas.research_job import JobRequest, JobResponse
from app.services.research_job_service import ResearchJobService
from app.services.exchange_rate_service import ExchangeRateService
from app.tasks.scraper_task import run_research_job
from app.models.research_job import JobStatus

import logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("", response_model=List[JobResponse])
def get_jobs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user_id: str = Depends(get_current_user_id)):
    return ResearchJobService.get_user_jobs(db, user_id=current_user_id, skip=skip, limit=limit)

@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_job(req: JobRequest, db: Session = Depends(get_db), current_user_id: str = Depends(get_current_user_id)):
    try:
        logger.info(f"Creating job for user: {current_user_id}, keywords: {req.conditions.keywords}")
        job = ResearchJobService.create_job(db, user_id=current_user_id, req=req)
        logger.info(f"Job created: {job.id}, enqueueing task...")
        
        result = run_research_job.delay(str(job.id))
        logger.info(f"Task enqueued: {result.id}")
        
        return job
    except Exception as e:
        logger.error(f"Failed to create job: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: str, db: Session = Depends(get_db), current_user_id: str = Depends(get_current_user_id)):
    job = ResearchJobService.get_user_job(db, user_id=current_user_id, job_id=job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(job_id: str, db: Session = Depends(get_db), current_user_id: str = Depends(get_current_user_id)):
    success = ResearchJobService.delete_job(db, user_id=current_user_id, job_id=job_id)
    if not success:
        raise HTTPException(status_code=404, detail="Job not found")
    return None

@router.get("/{job_id}/results", response_model=dict)
async def get_research_results(
    job_id: str,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    job = ResearchJobService.get_user_job(db, user_id=current_user_id, job_id=job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != JobStatus.completed:
        raise HTTPException(status_code=400, detail="Job not completed")
    
    # ドル円レート取得
    usd_to_jpy = await ExchangeRateService.get_usd_to_jpy_rate()

    # DBから取得した本物のデータを整形
    saved_items = job.result_summary.get("items", []) if job.result_summary else []
    
    formatted_items = []
    for i, item in enumerate(saved_items):
        ebay_price_usd = item.get("price", 0.0)
        ebay_price_jpy = round(ebay_price_usd * usd_to_jpy)
        
        # 仕入れ側はまだモックなので仮計算
        source_price_jpy = 5000 + (i * 100)
        profit_jpy = ebay_price_jpy - source_price_jpy
        profit_margin = round((profit_jpy / ebay_price_jpy) * 100, 1) if ebay_price_jpy > 0 else 0
        
        formatted_items.append({
            "candidateId": item.get("item_id", f"item-{i}"),
            "productName": f"Source Product for {item.get('title', 'Unknown')[:20]}...",
            "sourceChannel": "mercari",
            "sourcePrice": source_price_jpy,
            "sourceUrl": f"https://mercari.jp/search?keyword={item.get('title', '')[:10]}",
            "ebayTitle": item.get("title", "Unknown"),
            "ebayPrice": ebay_price_usd,
            "ebayPriceJpy": ebay_price_jpy,
            "profitJpy": profit_jpy,
            "profitMarginPct": profit_margin,
            "matchScore": 0.95 - (i * 0.01),
            "status": "new",
            "image": item.get("image")
        })

    return {
        "items": formatted_items[offset:offset+limit],
        "total": len(formatted_items),
        "limit": limit,
        "offset": offset
    }

@router.get("/{job_id}/results/{candidate_id}", response_model=dict)
async def get_candidate_detail(
    job_id: str,
    candidate_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    job = ResearchJobService.get_user_job(db, user_id=current_user_id, job_id=job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    usd_to_jpy = await ExchangeRateService.get_usd_to_jpy_rate()
    
    saved_items = job.result_summary.get("items", []) if job.result_summary else []
    target_item = next((item for item in saved_items if item.get("item_id") == candidate_id), None)
    
    if not target_item:
        raise HTTPException(status_code=404, detail="Candidate not found")
        
    ebay_price_usd = target_item.get("price", 0.0)
    ebay_price_jpy = round(ebay_price_usd * usd_to_jpy)
    source_price_jpy = 5000
    profit_jpy = ebay_price_jpy - source_price_jpy
    profit_margin = round((profit_jpy / ebay_price_jpy) * 100, 1) if ebay_price_jpy > 0 else 0
    
    return {
        "candidateId": target_item.get("item_id"),
        "productName": f"Source Product for {target_item.get('title', 'Unknown')[:20]}...",
        "sourceChannel": "mercari",
        "sourcePrice": source_price_jpy,
        "sourceUrl": f"https://mercari.jp/search?keyword={target_item.get('title', '')[:10]}",
        "ebayTitle": target_item.get("title", "Unknown"),
        "ebayPrice": ebay_price_usd,
        "ebayPriceJpy": ebay_price_jpy,
        "profitJpy": profit_jpy,
        "profitMarginPct": profit_margin,
        "matchScore": 0.95,
        "status": "new",
        "image": target_item.get("image"),
        "description": "This is a real item fetched from eBay API."
    }

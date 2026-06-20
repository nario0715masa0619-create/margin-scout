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

    # モック: 10 件の固定データを返す
    mock_items = [
        {
            "candidateId": f"item-{i}",
            "productName": f"iPhone {i+1}",
            "sourceChannel": "mercari",
            "sourcePrice": 5000 + (i * 100),
            "sourceUrl": f"https://mercari.jp/items/{i}",
            "ebayTitle": f"Apple iPhone {i+1} Unlocked",
            "ebayPrice": 100.0 + (i * 10),
            "ebayPriceJpy": round((100.0 + (i * 10)) * usd_to_jpy),
            "profitJpy": 10000 + (i * 500),
            "profitMarginPct": 30.5 + i,
            "matchScore": 0.95 - (i * 0.01),
            "status": "new"
        }
        for i in range(10)
    ]
    
    return {
        "items": mock_items[offset:offset+limit],
        "total": 10,
        "limit": limit,
        "offset": offset
    }

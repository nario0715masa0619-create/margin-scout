import logging
import asyncio
from app.celery_app import celery_app
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.research_job import JobStatus
from app.repositories.research_job_repository import research_job_repo
from app.services.ebay_service import ebay_service

logger = logging.getLogger(__name__)

@celery_app.task(name="run_research_job")
def run_research_job(job_id: str):
    logger.info(f"Starting research job: {job_id}")
    db: Session = SessionLocal()
    
    try:
        job = research_job_repo.get(db, id=job_id)
        if not job:
            logger.error(f"Job not found: {job_id}")
            return
        
        job.status = JobStatus.running
        db.commit()
        
        keywords = ", ".join(job.conditions.get("keywords", []))
        logger.info(f"Searching eBay for: {keywords}")
        
        # eBay API 実装
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        ebay_items = loop.run_until_complete(ebay_service.search_items(keywords, limit=10))
        loop.close()
        
        job.status = JobStatus.completed
        job.progress = 100
        job.total_items = len(ebay_items)
        job.matched_items = len(ebay_items)
        db.commit()
        logger.info(f"Job completed: {len(ebay_items)} items")
        
    except Exception as e:
        logger.error(f"Job failed: {e}", exc_info=True)
        job.status = JobStatus.failed
        db.commit()
    finally:
        db.close()

import logging
import asyncio
from celery import shared_task
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.research_job import ResearchJob, JobStatus
from app.repositories.research_job_repository import research_job_repo
from app.services.ebay_service import ebay_service
from app.services.exchange_rate_service import ExchangeRateService

logger = logging.getLogger(__name__)

@shared_task(name="run_research_job")
def run_research_job(job_id: str):
    """Celery タスク：リサーチジョブを実行"""
    logger.info(f"Starting Celery scraping task for job: {job_id}")
    db: Session = SessionLocal()
    
    try:
        job = research_job_repo.get(db, id=job_id)
        if not job:
            logger.error(f"Job not found: {job_id}")
            return
        
        job.status = JobStatus.running
        db.commit()
        logger.info(f"Job status set to running: {job_id}")
        
        # キーワードを取得
        keywords = ", ".join(job.conditions.get("keywords", []))
        logger.info(f"Executing eBay search for keywords: {keywords}")
        
        # eBay API で実検索を実行
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        ebay_items = loop.run_until_complete(ebay_service.search_items(keywords, limit=10))
        loop.close()
        
        logger.info(f"Found {len(ebay_items)} items on eBay for: {keywords}")
        
        # ジョブ完了
        job.status = JobStatus.completed
        job.progress = 100
        job.total_items = len(ebay_items)
        job.matched_items = len(ebay_items)
        db.commit()
        
        logger.info(f"Job completed successfully: {job_id}, items: {len(ebay_items)}")
        
    except Exception as e:
        logger.error(f"Job failed: {job_id}. Error: {e}", exc_info=True)
        job.status = JobStatus.failed
        db.commit()
    finally:
        db.close()

import logging
from celery import shared_task
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.research_job import ResearchJob, JobStatus
from app.repositories.research_job_repository import research_job_repo

logger = logging.getLogger(__name__)

@shared_task(name="run_research_job")
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
        logger.info(f"Job status: running")
        
        # 今はモック版に戻す（eBay API の非同期処理はスキップ）
        import time
        time.sleep(2)
        
        job.status = JobStatus.completed
        job.progress = 100
        job.total_items = 10
        job.matched_items = 10
        db.commit()
        logger.info(f"Job completed")
        
    except Exception as e:
        logger.error(f"Job failed: {e}", exc_info=True)
        job.status = JobStatus.failed
        db.commit()
    finally:
        db.close()

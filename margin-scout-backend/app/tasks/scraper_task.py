import asyncio
import logging
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.repositories.research_job_repository import research_job_repo
from app.models.research_job import JobStatus

logger = logging.getLogger(__name__)

async def run_research_job(job_id: str):
    logger.info(f"Starting background scraping task for job: {job_id}")
    db: Session = SessionLocal()
    try:
        # 1. Update status to running
        job = research_job_repo.get(db, id=job_id)
        if not job:
            logger.error(f"Job not found: {job_id}")
            return
            
        job.status = JobStatus.running
        db.commit()

        # 2. Call scraper adapters
        # (Phase 1 mock logic)
        logger.info(f"Executing mock scraping for job: {job_id}")
        await asyncio.sleep(5)  # Simulate long-running scraping task

        # 3. Complete
        job.status = JobStatus.completed
        job.progress = 100
        job.total_items = 10  # Mock items found
        db.commit()
        logger.info(f"Job completed successfully: {job_id}")

    except Exception as e:
        logger.error(f"Job failed: {job_id}. Error: {e}")
        try:
            db.rollback()
            job = research_job_repo.get(db, id=job_id)
            if job:
                job.status = JobStatus.failed
                db.commit()
        except Exception as rollback_err:
            logger.error(f"Failed to rollback/update status to failed: {rollback_err}")
    finally:
        db.close()

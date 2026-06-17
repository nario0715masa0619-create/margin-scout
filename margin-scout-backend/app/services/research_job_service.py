from sqlalchemy.orm import Session
from app.repositories.research_job_repository import research_job_repo
from app.schemas.research_job import JobRequest
from app.models.research_job import JobStatus

class ResearchJobService:
    @staticmethod
    def get_user_jobs(db: Session, user_id: str, skip: int = 0, limit: int = 100):
        return research_job_repo.get_multi_by_user(db, user_id=user_id, skip=skip, limit=limit)

    @staticmethod
    def get_user_job(db: Session, user_id: str, job_id: str):
        return research_job_repo.get_by_user(db, user_id=user_id, job_id=job_id)

    @staticmethod
    def create_job(db: Session, user_id: str, req: JobRequest):
        obj_in = {
            "user_id": user_id,
            "title": req.title,
            "status": JobStatus.pending,
            "conditions": req.conditions.model_dump(),
            "progress": 0,
            "total_items": 0,
            "matched_items": 0
        }
        return research_job_repo.create(db, obj_in=obj_in)

    @staticmethod
    def delete_job(db: Session, user_id: str, job_id: str) -> bool:
        job = research_job_repo.get_by_user(db, user_id=user_id, job_id=job_id)
        if not job:
            return False
        research_job_repo.remove(db, id=job.id)
        return True

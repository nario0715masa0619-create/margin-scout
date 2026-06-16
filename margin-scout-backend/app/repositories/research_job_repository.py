from typing import Optional, List
from sqlalchemy.orm import Session
from app.repositories.base import BaseRepository
from app.models.research_job import ResearchJob

class ResearchJobRepository(BaseRepository[ResearchJob]):
    def __init__(self):
        super().__init__(ResearchJob)

    def get_by_user(self, db: Session, user_id: str, job_id: str) -> Optional[ResearchJob]:
        return db.query(self.model).filter(
            self.model.user_id == user_id,
            self.model.id == job_id
        ).first()

    def get_multi_by_user(self, db: Session, user_id: str, skip: int = 0, limit: int = 100) -> List[ResearchJob]:
        return db.query(self.model).filter(self.model.user_id == user_id)\
                 .order_by(self.model.created_at.desc())\
                 .offset(skip).limit(limit).all()

research_job_repo = ResearchJobRepository()

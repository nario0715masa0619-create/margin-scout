from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.dependencies import get_current_user_id
from app.schemas.research_job import JobRequest, JobResponse
from app.services.research_job_service import ResearchJobService
from app.tasks.scraper_task import run_research_job

router = APIRouter()

@router.get("/", response_model=List[JobResponse])
def get_jobs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user_id: str = Depends(get_current_user_id)):
    return ResearchJobService.get_user_jobs(db, user_id=current_user_id, skip=skip, limit=limit)

@router.post("/", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_job(req: JobRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db), current_user_id: str = Depends(get_current_user_id)):
    job = ResearchJobService.create_job(db, user_id=current_user_id, req=req)
    background_tasks.add_task(run_research_job, job.id)
    return job

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

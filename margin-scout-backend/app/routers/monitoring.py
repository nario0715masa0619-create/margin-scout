from fastapi import APIRouter, Depends
from app.auth.dependencies import get_current_user
from app.tasks.monitoring_tasks import dispatch_due_monitoring_jobs
from app.models.user import User

router = APIRouter(prefix="/api/v1/monitoring", tags=["monitoring"])

@router.post("/dispatch")
async def trigger_dispatch(current_user: User = Depends(get_current_user)):
    """
    手動で dispatch_due_monitoring_jobs をトリガー (Admin/Debug用)
    """
    task = dispatch_due_monitoring_jobs.delay()
    return {"task_id": str(task.id), "status": "dispatched"}

@router.get("/task-status/{task_id}")
async def get_task_status(task_id: str, current_user: User = Depends(get_current_user)):
    """
    Celery タスク実行状態を確認
    """
    from app.celery_app import celery_app
    
    result = celery_app.AsyncResult(task_id)
    # result.result might not be JSON serializable if it's an Exception, 
    # so we stringify it if it's an exception, otherwise return it
    task_result = result.result
    if isinstance(task_result, Exception):
        task_result = str(task_result)
        
    return {"task_id": task_id, "state": result.state, "result": task_result}

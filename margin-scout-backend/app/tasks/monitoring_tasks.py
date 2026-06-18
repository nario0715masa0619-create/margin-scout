from app.celery_app import celery_app
from celery.result import AsyncResult

@celery_app.task(name="app.tasks.monitoring_tasks.dispatch_due_monitoring_jobs")
def dispatch_due_monitoring_jobs():
    """
    今のUTC時刻を基準に、next_run_at <= now() の SavedSearch を抽出し、
    各々に対して execute_saved_search_job をキューに登録。
    """
    from app.db.database import SessionLocal
    from app.models.research import SavedSearch
    from datetime import datetime, timezone
    
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        due_searches = db.query(SavedSearch).filter(
            SavedSearch.is_monitoring_enabled == True,
            SavedSearch.next_run_at <= now,
        ).all()
        
        task_count = 0
        for search in due_searches:
            execute_saved_search_job.delay(str(search.id))
            task_count += 1
        
        return {"dispatched": task_count, "timestamp": now.isoformat()}
    finally:
        db.close()

# wait for orchestrator coroutine helper since celery tasks are sync
import asyncio

def _run_async(coro):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

@celery_app.task(
    name="app.tasks.monitoring_tasks.execute_saved_search_job",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
def execute_saved_search_job(self, search_id: str):
    """
    指定の SavedSearch を実行し、Browserless Orchestrator を呼び出す。
    成功時は next_run_at を更新。
    """
    from app.db.database import SessionLocal
    from app.models.research import SavedSearch, ImportSession
    from app.services.browserless_orchestrator import BrowserlessOrchestrator
    from app.schemas.saved_searches import FilterSchema
    from datetime import datetime, timedelta, timezone
    from uuid import UUID
    
    db = SessionLocal()
    try:
        search = db.query(SavedSearch).filter(SavedSearch.id == UUID(search_id)).first()
        if not search:
            return {"error": "SavedSearch not found", "search_id": search_id}
        
        # Orchestrator 実行
        orchestrator = BrowserlessOrchestrator(db, search.user_id)
        
        # fallback_reason="monitoring_auto_run"
        result = _run_async(orchestrator.execute_with_fallback(
            source=search.source,
            filters=FilterSchema(**search.filters),
            fallback_reason="monitoring_auto_run",
            user_id=search.user_id,
        ))
        
        # ImportSession 作成
        if result.success and result.items:
            session = ImportSession(
                user_id=search.user_id,
                source=search.source,
                item_count=len(result.items),
                saved_search_id=search.id,
                import_type="monitoring",
                completed_at=datetime.now(timezone.utc)
            )
            db.add(session)
            db.commit()
        
        # next_run_at を更新
        now_utc = datetime.now(timezone.utc)
        search.last_run_at = now_utc
        search.last_run_status = "success" if result.success else "failed"
        search.last_run_error = result.error
        search.next_run_at = now_utc + timedelta(hours=search.monitoring_interval_hours)
        db.commit()
        
        return {
            "success": result.success,
            "items_count": len(result.items),
            "next_run_at": search.next_run_at.isoformat(),
        }
    
    except Exception as exc:
        search.last_run_status = "failed"
        search.last_run_error = str(exc)
        db.commit()
        
        # Retry logic
        raise self.retry(exc=exc)
    finally:
        db.close()

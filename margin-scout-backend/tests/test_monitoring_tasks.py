import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from uuid import uuid4
from datetime import datetime, timedelta, timezone

from app.tasks.monitoring_tasks import dispatch_due_monitoring_jobs, execute_saved_search_job
from app.models.research import SavedSearch, ImportSession
from app.services.browserless_orchestrator import CaptureResult

from tests.test_saved_searches_api import test_db, test_user_id, test_user, test_token, client

@pytest.fixture
def mock_db_session(test_db):
    from sqlalchemy.orm import sessionmaker
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db.get_bind())
    with patch("app.db.database.SessionLocal", TestingSessionLocal):
        yield test_db

@pytest.fixture
def due_search(test_db, test_user_id):
    search = SavedSearch(
        id=uuid4(),
        user_id=test_user_id,
        name="Due Search",
        source="mercari",
        filters={"keyword": "test"},
        is_monitoring_enabled=True,
        monitoring_interval_hours=24,
        next_run_at=datetime.now(timezone.utc) - timedelta(hours=1)
    )
    test_db.add(search)
    test_db.commit()
    return search

@pytest.fixture
def future_search(test_db, test_user_id):
    search = SavedSearch(
        id=uuid4(),
        user_id=test_user_id,
        name="Future Search",
        source="mercari",
        filters={"keyword": "test"},
        is_monitoring_enabled=True,
        monitoring_interval_hours=24,
        next_run_at=datetime.now(timezone.utc) + timedelta(hours=1)
    )
    test_db.add(search)
    test_db.commit()
    return search

def test_dispatch_due_monitoring_jobs(mock_db_session, due_search, future_search):
    """1. SavedSearch が is_monitoring_enabled=True and next_run_at <= now() の場合、dispatch"""
    """2. dispatch タスク実行で execute_saved_search_job.delay() が呼ばれる"""
    with patch("app.tasks.monitoring_tasks.execute_saved_search_job.delay") as mock_delay:
        result = dispatch_due_monitoring_jobs()
        assert result["dispatched"] == 1
        mock_delay.assert_called_once_with(str(due_search.id))

def test_executor_success(mock_db_session, due_search):
    """3. executor が Browserless Orchestrator を呼び出す"""
    """4. 成功時に ImportSession が作成され、next_run_at が更新される"""
    with patch("app.services.browserless_orchestrator.BrowserlessOrchestrator") as mock_orchestrator_class:
        mock_orchestrator = MagicMock()
        mock_orchestrator.execute_with_fallback = AsyncMock(return_value=CaptureResult(
            success=True,
            items=[{"id": "test"}],
            fallback_provider="test",
            error=None,
            retry_count=0,
            cost_estimate_jpy=0.0,
            execution_time_ms=100
        ))
        mock_orchestrator_class.return_value = mock_orchestrator
        
        # Call the task body directly (as a normal function for testing)
        # Note: self is passed as None since we don't need retry here
        result = execute_saved_search_job(str(due_search.id))
        
        assert result["success"] is True
        assert result["items_count"] == 1
        
        # Verify ImportSession was created
        session = mock_db_session.query(ImportSession).filter_by(saved_search_id=due_search.id).first()
        assert session is not None
        assert session.completed_at is not None
        assert session.import_type == "monitoring"
        
        # Verify next_run_at is updated
        mock_db_session.expire_all()
        updated_search = mock_db_session.query(SavedSearch).filter_by(id=due_search.id).first()
        assert updated_search.last_run_status == "success"
        assert updated_search.next_run_at > datetime.utcnow()

def test_executor_failure(mock_db_session, due_search):
    """5. 失敗時に last_run_status と last_run_error が記録される"""
    with patch("app.services.browserless_orchestrator.BrowserlessOrchestrator") as mock_orchestrator_class:
        mock_orchestrator = MagicMock()
        mock_orchestrator.execute_with_fallback = AsyncMock(return_value=CaptureResult(
            success=False,
            items=[],
            fallback_provider="test",
            error="Scrape failed",
            retry_count=0,
            cost_estimate_jpy=0.0,
            execution_time_ms=100
        ))
        mock_orchestrator_class.return_value = mock_orchestrator
        
        result = execute_saved_search_job(str(due_search.id))
        
        assert result["success"] is False
        
        # Verify ImportSession was NOT created
        session = mock_db_session.query(ImportSession).filter_by(saved_search_id=due_search.id).first()
        assert session is None
        
        mock_db_session.expire_all()
        updated_search = mock_db_session.query(SavedSearch).filter_by(id=due_search.id).first()
        assert updated_search.last_run_status == "failed"
        assert updated_search.last_run_error == "Scrape failed"

def test_executor_exception_retry(mock_db_session, due_search):
    """6. retry ロジックがエラー時に動作"""
    with patch("app.services.browserless_orchestrator.BrowserlessOrchestrator") as mock_orchestrator_class:
        mock_orchestrator = MagicMock()
        mock_orchestrator.execute_with_fallback.side_effect = Exception("Unexpected network error")
        mock_orchestrator_class.return_value = mock_orchestrator
        
        with patch.object(execute_saved_search_job, "retry", return_value=Exception("Retry Triggered")) as mock_retry:
            with pytest.raises(Exception, match="Retry Triggered"):
                execute_saved_search_job(str(due_search.id))
                
            mock_retry.assert_called_once()
        
        mock_db_session.expire_all()
        updated_search = mock_db_session.query(SavedSearch).filter_by(id=due_search.id).first()
        assert updated_search.last_run_status == "failed"
        assert updated_search.last_run_error == "Unexpected network error"

def test_manual_trigger_endpoint(client, test_token):
    """7. Manual trigger エンドポイント /monitoring/dispatch が 200 を返す"""
    with patch("app.tasks.monitoring_tasks.dispatch_due_monitoring_jobs.delay") as mock_delay:
        mock_task = MagicMock()
        mock_task.id = "test-task-id"
        mock_delay.return_value = mock_task
        
        response = client.post(
            "/api/v1/monitoring/dispatch",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "test-task-id"
        assert data["status"] == "dispatched"
        mock_delay.assert_called_once()

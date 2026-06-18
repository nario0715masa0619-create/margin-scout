import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from uuid import uuid4
import json
from datetime import datetime

from app.main import app
from app.db.base import Base
from app.models.research import SavedSearch
from app.models.user import User
from app.db.database import get_db
from app.auth.dependencies import get_current_user

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

from sqlalchemy.pool import StaticPool

@pytest.fixture(scope="function")
def test_db():
    engine = create_engine(
        SQLALCHEMY_TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    db = TestingSessionLocal()
    yield db
    db.close()
    app.dependency_overrides.clear()

@pytest.fixture
def test_user_id():
    return str(uuid4())

@pytest.fixture
def test_user(test_db, test_user_id):
    user = User(
        id=test_user_id,
        email="test@example.com",
        username="testuser",
        hashed_password="fakehashedpassword",
        is_active=True
    )
    test_db.add(user)
    test_db.commit()
    return user

@pytest.fixture
def test_token(test_user, test_user_id):
    import jwt
    from app.config import settings
    payload = {"sub": test_user_id}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

@pytest.fixture
def client():
    return TestClient(app)

def test_create_saved_search(client, test_db, test_token):
    """POST /api/v1/saved-searches: 保存検索作成"""
    payload = {
        "name": "iPhone 14 Search",
        "source": "mercari",
        "filters": {
            "keyword": "iPhone 14",
            "options": {"on_sale": True},
            "conditions": ["new", "almost_new"],
            "price_range": {"min": 50000, "max": 150000}
        },
        "is_monitoring_enabled": True,
        "monitoring_interval_hours": 24
    }
    
    response = client.post(
        "/api/v1/saved-searches",
        json=payload,
        headers={"Authorization": f"Bearer {test_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "iPhone 14 Search"
    assert data["source"] == "mercari"
    assert data["is_monitoring_enabled"] is True
    assert data["next_run_at"] is not None

def test_list_saved_searches(client, test_db, test_token):
    """GET /api/v1/saved-searches: 保存検索一覧"""
    response = client.get(
        "/api/v1/saved-searches",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "searches" in data
    assert "total" in data
    assert "limit" in data
    assert "offset" in data

def test_get_saved_search(client, test_db, test_token):
    """GET /api/v1/saved-searches/{id}: 保存検索詳細"""
    # まず作成
    create_payload = {
        "name": "Test Search",
        "source": "mercari",
        "filters": {"keyword": "iPhone"},
        "is_monitoring_enabled": False
    }
    create_response = client.post(
        "/api/v1/saved-searches",
        json=create_payload,
        headers={"Authorization": f"Bearer {test_token}"}
    )
    search_id = create_response.json()["id"]
    
    # 詳細取得
    response = client.get(
        f"/api/v1/saved-searches/{search_id}",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == search_id
    assert data["name"] == "Test Search"

def test_get_saved_search_not_found(client, test_db, test_token):
    """GET /api/v1/saved-searches/{id}: 存在しないID"""
    response = client.get(
        f"/api/v1/saved-searches/{uuid4()}",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    
    assert response.status_code == 404

def test_update_saved_search(client, test_db, test_token):
    """PUT /api/v1/saved-searches/{id}: 保存検索更新"""
    # まず作成
    create_payload = {
        "name": "Original Name",
        "source": "mercari",
        "filters": {"keyword": "iPhone"},
        "is_monitoring_enabled": False
    }
    create_response = client.post(
        "/api/v1/saved-searches",
        json=create_payload,
        headers={"Authorization": f"Bearer {test_token}"}
    )
    search_id = create_response.json()["id"]
    
    # 更新
    update_payload = {
        "name": "Updated Name",
        "is_monitoring_enabled": True,
        "monitoring_interval_hours": 12
    }
    update_response = client.put(
        f"/api/v1/saved-searches/{search_id}",
        json=update_payload,
        headers={"Authorization": f"Bearer {test_token}"}
    )
    
    assert update_response.status_code == 200
    data = update_response.json()
    assert data["name"] == "Updated Name"
    assert data["is_monitoring_enabled"] is True
    assert data["monitoring_interval_hours"] == 12

def test_delete_saved_search(client, test_db, test_token):
    """DELETE /api/v1/saved-searches/{id}: 保存検索削除"""
    # まず作成
    create_payload = {
        "name": "To Delete",
        "source": "mercari",
        "filters": {"keyword": "iPhone"},
    }
    create_response = client.post(
        "/api/v1/saved-searches",
        json=create_payload,
        headers={"Authorization": f"Bearer {test_token}"}
    )
    search_id = create_response.json()["id"]
    
    # 削除
    delete_response = client.delete(
        f"/api/v1/saved-searches/{search_id}",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    
    assert delete_response.status_code == 200
    assert delete_response.json()["status"] == "deleted"
    
    # 削除後は 404
    get_response = client.get(
        f"/api/v1/saved-searches/{search_id}",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert get_response.status_code == 404

def test_rerun_saved_search(client, test_db, test_token):
    """POST /api/v1/saved-searches/{id}/rerun: 手動再実行"""
    # まず作成
    create_payload = {
        "name": "Rerun Test",
        "source": "mercari",
        "filters": {"keyword": "iPhone"},
    }
    create_response = client.post(
        "/api/v1/saved-searches",
        json=create_payload,
        headers={"Authorization": f"Bearer {test_token}"}
    )
    search_id = create_response.json()["id"]
    
    # 再実行
    rerun_response = client.post(
        f"/api/v1/saved-searches/{search_id}/rerun",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    
    assert rerun_response.status_code == 200
    data = rerun_response.json()
    assert data["status"] == "queued"

def test_disable_monitoring(client, test_db, test_token):
    """POST /api/v1/saved-searches/{id}/disable-monitoring: 監視停止"""
    # まず作成（monitoring 有効）
    create_payload = {
        "name": "Monitoring Test",
        "source": "mercari",
        "filters": {"keyword": "iPhone"},
        "is_monitoring_enabled": True,
        "monitoring_interval_hours": 24
    }
    create_response = client.post(
        "/api/v1/saved-searches",
        json=create_payload,
        headers={"Authorization": f"Bearer {test_token}"}
    )
    search_id = create_response.json()["id"]
    
    # 監視停止
    disable_response = client.post(
        f"/api/v1/saved-searches/{search_id}/disable-monitoring",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    
    assert disable_response.status_code == 200
    data = disable_response.json()
    assert data["is_monitoring_enabled"] is False
    assert data["next_run_at"] is None

def test_create_saved_search_unauthorized():
    """POST /api/v1/saved-searches: 認証なし"""
    payload = {
        "name": "Test",
        "source": "mercari",
        "filters": {"keyword": "iPhone"}
    }
    
    response = TestClient(app).post(
        "/api/v1/saved-searches",
        json=payload
    )
    
    assert response.status_code == 401

def test_create_saved_search_invalid_payload(client, test_db, test_token):
    """POST /api/v1/saved-searches: ペイロード検証失敗"""
    payload = {
        "name": "",  # 空文字列 ← 検証失敗
        "source": "mercari",
        "filters": {"keyword": "iPhone"}
    }
    
    response = client.post(
        "/api/v1/saved-searches",
        json=payload,
        headers={"Authorization": f"Bearer {test_token}"}
    )
    
    assert response.status_code == 422

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import json
from datetime import datetime

from app.main import app
from app.db.base import Base
from app.db.database import get_db
from app.auth.dependencies import get_current_user

# Ensure models are loaded
from app.models.research import ImportSession, SourceItem, EbayMatch, ProfitSnapshot
from app.models.user import User

# テスト用インメモリ DB
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

from sqlalchemy.pool import StaticPool

@pytest.fixture(scope="function")
def test_db():
    engine = create_engine(
        SQLALCHEMY_TEST_DATABASE_URL, 
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)
    
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    # We must mock get_current_user if we want the actual db user check to pass, OR we seed the user
    # Because router checks: user = db.query(User).filter(User.id == current_user_id).first()
    db = TestingSessionLocal()
    test_user = User(id="test-user-id-12345", email="test@example.com", is_active=True, hashed_password="dummy")
    db.add(test_user)
    db.commit()
    db.close()

    yield
    app.dependency_overrides.clear()

@pytest.fixture
def test_user_id():
    return "test-user-id-12345"

@pytest.fixture
def test_token(test_user_id):
    """JWT テストトークンを生成"""
    import jwt
    from datetime import datetime, timezone
    from app.config import settings
    payload = {"sub": test_user_id, "exp": datetime.now(timezone.utc).timestamp() + 3600}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

@pytest.fixture
def client():
    return TestClient(app)

def test_create_capture_success(client, test_db, test_token, test_user_id):
    """正常系: Extension からのデータ受け取り・保存"""
    payload = {
        "source": "mercari",
        "import_type": "manual",
        "items": [
            {
                "title": "iPhone 14 Pro",
                "price_jpy": 95000,
                "url": "https://mercari.jp/item/m123",
                "seller_name": "User123",
                "condition": "new",
                "fetched_at": datetime.utcnow().isoformat()
            }
        ]
    }
    
    response = client.post(
        "/api/v1/captures",
        json=payload,
        headers={"Authorization": f"Bearer {test_token}"}
    )
    
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["processed_count"] >= 1
    assert "import_session_id" in data

def test_create_capture_no_auth(client, test_db):
    """エラー系: 認証なし"""
    payload = {
        "source": "mercari",
        "items": [{"title": "iPhone", "price_jpy": 50000, "url": "https://mercari.jp/item/m123", "fetched_at": datetime.utcnow().isoformat()}]
    }
    
    response = client.post("/api/v1/captures", json=payload)
    assert response.status_code in (401, 403)  # Forbidden or Unauthorized

def test_create_capture_invalid_payload(client, test_db, test_token):
    """エラー系: ペイロード検証失敗"""
    payload = {
        "source": "mercari",
        "items": [{"title": "iPhone", "price_jpy": -100, "url": "https://mercari.jp", "fetched_at": datetime.utcnow().isoformat()}]  # 負の価格
    }
    
    response = client.post(
        "/api/v1/captures",
        json=payload,
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 422  # Validation error

def get_db_session():
    # Helper to get db session for tests
    return next(app.dependency_overrides[get_db]())

@pytest.fixture
def other_user_id():
    return "other-user-id-99999"

@pytest.fixture(autouse=True)
def setup_other_user(test_db, other_user_id):
    db = get_db_session()
    user = User(id=other_user_id, email="other@example.com", is_active=True, hashed_password="dummy")
    db.add(user)
    db.commit()
    db.close()

from uuid import uuid4

def create_test_capture(db, user_id):
    capture = ImportSession(
        id=uuid4(),
        user_id=user_id,
        source="mercari",
        import_type="manual",
        item_count=1
    )
    db.add(capture)
    db.commit()
    return capture

def create_test_source_item(db, user_id):
    capture = create_test_capture(db, user_id)
    item = SourceItem(
        id=uuid4(),
        import_session_id=capture.id,
        source="mercari",
        title="Test Item",
        price_jpy=10000,
        url="https://mercari.jp/item/m1",
        fetched_at=datetime.utcnow()
    )
    db.add(item)
    db.commit()
    return item

def test_list_captures_success(client, test_db, test_token, test_user_id):
    """GET /api/v1/captures: 正常系"""
    response = client.get(
        "/api/v1/captures",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 200
    assert "sessions" in response.json()
    assert "total" in response.json()

def test_list_captures_unauthorized(client):
    """GET /api/v1/captures: 認証なし"""
    response = client.get("/api/v1/captures")
    assert response.status_code == 401

def test_list_captures_pagination(client, test_db, test_token):
    """GET /api/v1/captures: ページング確認"""
    response = client.get(
        "/api/v1/captures?limit=5&offset=0",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 200
    assert response.json()["limit"] == 5

def test_list_captures_limit_exceeded(client, test_db, test_token):
    """GET /api/v1/captures: limit > 100 で 422"""
    response = client.get(
        "/api/v1/captures?limit=101",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 422

def test_get_capture_detail_success(client, test_db, test_token, test_user_id):
    """GET /api/v1/captures/{capture_id}: 正常系"""
    db = get_db_session()
    capture = create_test_capture(db, test_user_id)
    db.close()
    
    response = client.get(
        f"/api/v1/captures/{capture.id}",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 200
    assert response.json()["id"] == str(capture.id)

def test_get_capture_detail_other_user(client, test_db, test_token, other_user_id):
    """GET /api/v1/captures/{capture_id}: 他ユーザーの capture は 404"""
    db = get_db_session()
    capture = create_test_capture(db, other_user_id)
    db.close()
    
    response = client.get(
        f"/api/v1/captures/{capture.id}",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 404

def test_get_capture_items_success(client, test_db, test_token, test_user_id):
    """GET /api/v1/captures/{capture_id}/items: 正常系"""
    db = get_db_session()
    capture = create_test_capture(db, test_user_id)
    db.close()
    
    response = client.get(
        f"/api/v1/captures/{capture.id}/items",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 200
    assert "items" in response.json()

def test_export_capture_csv_success(client, test_db, test_token, test_user_id):
    """POST /api/v1/captures/{capture_id}/export/csv: 正常系"""
    db = get_db_session()
    capture = create_test_capture(db, test_user_id)
    db.close()
    
    response = client.post(
        f"/api/v1/captures/{capture.id}/export/csv",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8" or response.headers["content-type"] == "text/csv"

def test_export_capture_csv_other_user(client, test_db, test_token, other_user_id):
    """POST /api/v1/captures/{capture_id}/export/csv: 他ユーザーの capture は 404"""
    db = get_db_session()
    capture = create_test_capture(db, other_user_id)
    db.close()
    
    response = client.post(
        f"/api/v1/captures/{capture.id}/export/csv",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 404

def test_list_saved_items_success(client, test_db, test_token, test_user_id):
    """GET /api/v1/saved-items: 正常系"""
    response = client.get(
        "/api/v1/saved-items",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 200
    assert "items" in response.json()

def test_list_saved_items_empty(client, test_db, test_token):
    """GET /api/v1/saved-items: 空状態"""
    response = client.get(
        "/api/v1/saved-items",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 200
    assert response.json()["items"] == []

def test_get_saved_item_success(client, test_db, test_token, test_user_id):
    """GET /api/v1/saved-items/{item_id}: 正常系"""
    db = get_db_session()
    item = create_test_source_item(db, test_user_id)
    db.close()
    
    response = client.get(
        f"/api/v1/saved-items/{item.id}",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 200

def test_get_saved_item_other_user(client, test_db, test_token, other_user_id):
    """GET /api/v1/saved-items/{item_id}: 他ユーザーのアイテムは 404"""
    db = get_db_session()
    item = create_test_source_item(db, other_user_id)
    db.close()
    
    response = client.get(
        f"/api/v1/saved-items/{item.id}",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 404

def test_export_saved_items_csv_success(client, test_db, test_token, test_user_id):
    """POST /api/v1/saved-items/export/csv: 正常系"""
    db = get_db_session()
    item1 = create_test_source_item(db, test_user_id)
    item2 = create_test_source_item(db, test_user_id)
    db.close()
    
    response = client.post(
        "/api/v1/saved-items/export/csv",
        json={"item_ids": [str(item1.id), str(item2.id)]},
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8" or response.headers["content-type"] == "text/csv"

def test_export_saved_items_csv_mixed_users(client, test_db, test_token, test_user_id, other_user_id):
    """POST /api/v1/saved-items/export/csv: 他ユーザーのアイテム混在で 400"""
    db = get_db_session()
    item1 = create_test_source_item(db, test_user_id)
    item2 = create_test_source_item(db, other_user_id)
    db.close()
    
    response = client.post(
        "/api/v1/saved-items/export/csv",
        json={"item_ids": [str(item1.id), str(item2.id)]},
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 400

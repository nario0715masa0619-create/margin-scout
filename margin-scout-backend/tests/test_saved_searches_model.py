import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.research import SavedSearch, UsageLog
from app.schemas.saved_searches import FilterSchema, SavedSearchCreateRequest

@pytest.fixture
def test_db():
    """テスト用 in-memory DB"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = TestingSessionLocal()
    yield db
    db.close()

def test_saved_search_creation(test_db):
    """SavedSearch 作成テスト"""
    user_id = str(uuid4())
    
    filters = {
        "keyword": "iPhone 14",
        "options": {"on_sale": True},
        "conditions": ["new", "almost_new"],
        "price_range": {"min": 50000, "max": 150000},
    }
    
    saved_search = SavedSearch(
        id=uuid4(),
        user_id=user_id,
        name="My Search",
        source="mercari",
        filters=filters,
        is_monitoring_enabled=True,
        monitoring_interval_hours=24,
        next_run_at=datetime.utcnow() + timedelta(hours=24)
    )
    
    test_db.add(saved_search)
    test_db.commit()
    
    retrieved = test_db.query(SavedSearch).filter_by(user_id=user_id).first()
    assert retrieved is not None
    assert retrieved.name == "My Search"
    assert retrieved.filters["keyword"] == "iPhone 14"
    assert retrieved.is_monitoring_enabled is True

def test_saved_search_next_run_at_index(test_db):
    """next_run_at インデックスが機能することを確認"""
    user_id = str(uuid4())
    
    now = datetime.utcnow()
    for i in range(5):
        saved_search = SavedSearch(
            id=uuid4(),
            user_id=user_id,
            name=f"Search {i}",
            source="mercari",
            filters={"keyword": f"item {i}"},
            is_monitoring_enabled=True,
            next_run_at=now + timedelta(hours=i)
        )
        test_db.add(saved_search)
    
    test_db.commit()
    
    # next_run_at <= now の検索
    due_searches = test_db.query(SavedSearch).filter(
        SavedSearch.next_run_at <= now + timedelta(hours=2),
        SavedSearch.is_monitoring_enabled == True
    ).all()
    
    assert len(due_searches) == 3  # hours=0, 1, 2

def test_usage_log_creation(test_db):
    """UsageLog 作成テスト"""
    user_id = str(uuid4())
    
    log = UsageLog(
        id=uuid4(),
        user_id=user_id,
        source="extension",
        fallback_provider=None,
        success=True,
        item_count=8,
        cost_estimate=0.0
    )
    
    test_db.add(log)
    test_db.commit()
    
    retrieved = test_db.query(UsageLog).filter_by(user_id=user_id).first()
    assert retrieved is not None
    assert retrieved.source == "extension"
    assert retrieved.item_count == 8

def test_pydantic_filter_schema_validation():
    """FilterSchema バリデーション"""
    # 正常系
    valid_filter = FilterSchema(
        keyword="iPhone",
        conditions=["new", "almost_new"],
        price_range={"min": 50000, "max": 150000}
    )
    assert valid_filter.keyword == "iPhone"
    
    # エラー系: keyword なし
    with pytest.raises(ValueError):
        FilterSchema()
    
    # エラー系: price_range max < min
    with pytest.raises(ValueError):
        FilterSchema(
            keyword="iPhone",
            price_range={"min": 150000, "max": 50000}
        )

def test_pydantic_saved_search_create_request():
    """SavedSearchCreateRequest バリデーション"""
    valid_req = SavedSearchCreateRequest(
        name="My Search",
        source="mercari",
        filters=FilterSchema(keyword="iPhone"),
        is_monitoring_enabled=True,
        monitoring_interval_hours=24
    )
    assert valid_req.name == "My Search"
    
    # エラー系: monitoring_interval_hours > 168
    with pytest.raises(ValueError):
        SavedSearchCreateRequest(
            name="My Search",
            source="mercari",
            filters=FilterSchema(keyword="iPhone"),
            monitoring_interval_hours=200  # 超過
        )

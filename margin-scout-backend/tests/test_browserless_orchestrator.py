import pytest
from unittest.mock import patch, MagicMock
import httpx
from uuid import uuid4

from app.services.browserless_orchestrator import (
    BrowserlessOrchestrator, 
    MercariProvider, 
    YahooAuctionProvider,
    CaptureResult
)
from app.schemas.saved_searches import FilterSchema, SourceEnum
from app.models.research import UsageLog, SavedSearch

from tests.test_saved_searches_api import test_db, test_user_id, test_user, test_token, client

@pytest.fixture
def mock_httpx_post():
    with patch("httpx.AsyncClient.post") as mock_post:
        yield mock_post

@pytest.fixture
def mock_filters():
    return FilterSchema(keyword="iPhone 14", conditions=["new"])

@pytest.mark.asyncio
async def test_mercari_provider_success(mock_httpx_post, mock_filters):
    """1. MercariProvider が filter を受け取り CaptureResult を返す"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"items": [{"id": "m1", "price": 1000}]}
    mock_httpx_post.return_value = mock_response

    provider = MercariProvider()
    result = await provider.capture(mock_filters)
    
    assert result.success is True
    assert len(result.items) == 1
    assert result.fallback_provider == "browserless_mercari"
    assert result.retry_count == 0

@pytest.mark.asyncio
async def test_yahoo_auction_provider_supports():
    """2. YahooAuctionProvider が対応ソースを認識"""
    provider = YahooAuctionProvider()
    assert await provider.supports_source(SourceEnum.YAHOO_AUCTION) is True
    assert await provider.supports_source(SourceEnum.MERCARI) is False

@pytest.mark.asyncio
async def test_orchestrator_invalid_source(test_db):
    """3. 不正な source に対して適切にハンドリング（Orchestratorが処理）"""
    orchestrator = BrowserlessOrchestrator(db=test_db, user_id=str(uuid4()))
    result = await orchestrator.execute_with_fallback(
        source="invalid_source",
        filters=FilterSchema(keyword="test"),
        fallback_reason="manual_rerun",
        user_id=str(uuid4())
    )
    assert result.success is False
    assert result.error == "Invalid source"

@pytest.mark.asyncio
async def test_browserless_timeout_retry(mock_httpx_post, mock_filters):
    """4. Browserless タイムアウト → retry ロジック"""
    # 1回目タイムアウト、2回目成功とする
    mock_httpx_post.side_effect = [
        httpx.TimeoutException("Timeout"),
        MagicMock(status_code=200, json=lambda: {"items": [{"id": "m1"}]})
    ]

    # patch time.sleep to run fast
    with patch("time.sleep"):
        provider = MercariProvider()
        result = await provider.capture(mock_filters)
        
    assert result.success is True
    assert result.retry_count == 1
    assert mock_httpx_post.call_count == 2

@pytest.mark.asyncio
async def test_browserless_rate_limit(mock_httpx_post, test_db, test_user_id, mock_filters):
    """5. Rate limit 429 → UsageLog に記録されるか"""
    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_httpx_post.return_value = mock_response

    orchestrator = BrowserlessOrchestrator(db=test_db, user_id=test_user_id)
    
    with patch("time.sleep"):
        result = await orchestrator.execute_with_fallback(
            source=SourceEnum.MERCARI.value,
            filters=mock_filters,
            fallback_reason="test",
            user_id=test_user_id
        )

    assert result.success is False
    assert result.retry_count > 0  # Should retry and eventually fail
    
    # Check UsageLog
    log = test_db.query(UsageLog).filter_by(user_id=test_user_id).order_by(UsageLog.created_at.desc()).first()
    assert log is not None
    assert log.success is False

@pytest.mark.asyncio
async def test_orchestrator_success_usage_log(mock_httpx_post, test_db, test_user_id, mock_filters):
    """6. 成功時 UsageLog が DB に保存される"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"items": [{"id": "m1"}, {"id": "m2"}]}
    mock_httpx_post.return_value = mock_response

    orchestrator = BrowserlessOrchestrator(db=test_db, user_id=test_user_id)
    result = await orchestrator.execute_with_fallback(
        source=SourceEnum.MERCARI.value,
        filters=mock_filters,
        fallback_reason="manual_rerun",
        user_id=test_user_id
    )

    assert result.success is True
    
    log = test_db.query(UsageLog).filter_by(user_id=test_user_id).order_by(UsageLog.created_at.desc()).first()
    assert log is not None
    assert log.success is True
    assert log.item_count == 2

@pytest.mark.asyncio
async def test_usage_log_cost_estimate(mock_httpx_post, test_db, test_user_id, mock_filters):
    """7. UsageLog の cost_estimate が正確 (0.5 * len(items))"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"items": [{} for _ in range(10)]}
    mock_httpx_post.return_value = mock_response

    orchestrator = BrowserlessOrchestrator(db=test_db, user_id=test_user_id)
    result = await orchestrator.execute_with_fallback(
        source=SourceEnum.MERCARI.value,
        filters=mock_filters,
        fallback_reason="cost_test",
        user_id=test_user_id
    )

    assert result.success is True
    assert result.cost_estimate_jpy == 5.0 # 0.5 * 10
    
    log = test_db.query(UsageLog).filter_by(user_id=test_user_id).order_by(UsageLog.created_at.desc()).first()
    assert log.cost_estimate == 5.0

def test_rerun_unauthorized(client):
    """8. 認証なしで Orchestrator(rerun API) を呼ぶと 401"""
    search_id = str(uuid4())
    response = client.post(f"/api/v1/saved-searches/{search_id}/rerun")
    assert response.status_code == 401

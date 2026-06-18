from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import uuid4, UUID
from datetime import datetime, timedelta
from typing import List, Optional

from app.models.research import SavedSearch, ImportSession
from app.models.user import User
from app.schemas.saved_searches import (
    SavedSearchCreateRequest,
    SavedSearchUpdateRequest,
    SavedSearchResponse,
)
from app.auth.dependencies import get_current_user
from app.db.database import get_db

router = APIRouter(prefix="/api/v1", tags=["saved-searches"])


@router.post("/saved-searches", response_model=SavedSearchResponse)
async def create_saved_search(
    payload: SavedSearchCreateRequest,
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    保存検索を作成
    
    Args:
        payload: SavedSearchCreateRequest（name, source, filters, is_monitoring_enabled等）
        current_user_id: JWT から抽出した user_id
        db: Database session
    
    Returns:
        SavedSearchResponse: 作成された保存検索
    
    Errors:
        401: 認証失敗
        400: ペイロード検証失敗
    """
    # ユーザー存在確認
    user = db.query(User).filter(User.id == current_user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # next_run_at を計算
    next_run_at = None
    if payload.is_monitoring_enabled:
        next_run_at = datetime.utcnow() + timedelta(hours=payload.monitoring_interval_hours)
    
    # SavedSearch 作成
    saved_search = SavedSearch(
        id=uuid4(),
        user_id=current_user_id,
        name=payload.name,
        source=payload.source.value,
        filters=payload.filters.model_dump() if hasattr(payload.filters, "model_dump") else payload.filters.dict(),
        is_monitoring_enabled=payload.is_monitoring_enabled,
        monitoring_interval_hours=payload.monitoring_interval_hours,
        next_run_at=next_run_at,
        last_run_status="pending"
    )
    
    db.add(saved_search)
    db.commit()
    db.refresh(saved_search)
    
    if hasattr(SavedSearchResponse, "model_validate"):
        return SavedSearchResponse.model_validate(saved_search)
    return SavedSearchResponse.from_orm(saved_search)


@router.get("/saved-searches", response_model=dict)
async def list_saved_searches(
    current_user_id: str = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """
    保存検索一覧取得（ページング対応）
    
    Args:
        current_user_id: JWT から抽出した user_id
        limit: ページサイズ（1-100）
        offset: オフセット
        db: Database session
    
    Returns:
        { "searches": [...], "total": N, "limit": ..., "offset": ... }
    
    Errors:
        401: 認証失敗
    """
    searches = db.query(SavedSearch).filter(
        SavedSearch.user_id == current_user_id
    ).order_by(SavedSearch.created_at.desc()).limit(limit).offset(offset).all()
    
    total = db.query(SavedSearch).filter(
        SavedSearch.user_id == current_user_id
    ).count()
    
    def to_dict(s):
        if hasattr(SavedSearchResponse, "model_validate"):
            return SavedSearchResponse.model_validate(s).model_dump()
        return SavedSearchResponse.from_orm(s).dict()
    
    return {
        "searches": [to_dict(s) for s in searches],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/saved-searches/{search_id}", response_model=SavedSearchResponse)
async def get_saved_search(
    search_id: UUID,
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    保存検索詳細取得
    
    Args:
        search_id: SavedSearch ID
        current_user_id: JWT から抽出した user_id
        db: Database session
    
    Returns:
        SavedSearchResponse: 保存検索詳細
    
    Errors:
        404: リソースなし / 他ユーザーのリソース
    """
    search = db.query(SavedSearch).filter(
        SavedSearch.id == search_id,
        SavedSearch.user_id == current_user_id
    ).first()
    
    if not search:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved search not found"
        )
    
    if hasattr(SavedSearchResponse, "model_validate"):
        return SavedSearchResponse.model_validate(search)
    return SavedSearchResponse.from_orm(search)


@router.put("/saved-searches/{search_id}", response_model=SavedSearchResponse)
async def update_saved_search(
    search_id: UUID,
    payload: SavedSearchUpdateRequest,
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    保存検索を更新
    
    Args:
        search_id: SavedSearch ID
        payload: SavedSearchUpdateRequest（name, filters, is_monitoring_enabled等）
        current_user_id: JWT から抽出した user_id
        db: Database session
    
    Returns:
        SavedSearchResponse: 更新された保存検索
    
    Errors:
        404: リソースなし / 他ユーザーのリソース
    """
    search = db.query(SavedSearch).filter(
        SavedSearch.id == search_id,
        SavedSearch.user_id == current_user_id
    ).first()
    
    if not search:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved search not found"
        )
    
    # 更新可能フィールド
    if payload.name is not None:
        search.name = payload.name
    if payload.filters is not None:
        search.filters = payload.filters.model_dump() if hasattr(payload.filters, "model_dump") else payload.filters.dict()
    if payload.is_monitoring_enabled is not None:
        search.is_monitoring_enabled = payload.is_monitoring_enabled
    if payload.monitoring_interval_hours is not None:
        search.monitoring_interval_hours = payload.monitoring_interval_hours
    
    # monitoring 有効化時に next_run_at を設定
    if payload.is_monitoring_enabled and search.next_run_at is None:
        search.next_run_at = datetime.utcnow() + timedelta(hours=search.monitoring_interval_hours)
    
    search.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(search)
    
    if hasattr(SavedSearchResponse, "model_validate"):
        return SavedSearchResponse.model_validate(search)
    return SavedSearchResponse.from_orm(search)


@router.delete("/saved-searches/{search_id}")
async def delete_saved_search(
    search_id: UUID,
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    保存検索を削除
    
    Args:
        search_id: SavedSearch ID
        current_user_id: JWT から抽出した user_id
        db: Database session
    
    Returns:
        { "status": "deleted" }
    
    Errors:
        404: リソースなし / 他ユーザーのリソース
    """
    search = db.query(SavedSearch).filter(
        SavedSearch.id == search_id,
        SavedSearch.user_id == current_user_id
    ).first()
    
    if not search:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved search not found"
        )
    
    db.delete(search)
    db.commit()
    
    return { "status": "deleted" }


@router.post("/saved-searches/{search_id}/rerun")
async def rerun_saved_search(
    search_id: UUID,
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    保存検索を手動で即座に再実行（Browserless フォールバック）
    
    Args:
        search_id: SavedSearch ID
        current_user_id: JWT から抽出した user_id
        db: Database session
    
    Returns:
        { "status": "queued", "message": "..." }
    
    Errors:
        404: リソースなし / 他ユーザーのリソース
        429: Rate limit 超過
    """
    search = db.query(SavedSearch).filter(
        SavedSearch.id == search_id,
        SavedSearch.user_id == current_user_id
    ).first()
    
    if not search:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved search not found"
        )
    
    # Orchestrator 実行
    from app.services.browserless_orchestrator import BrowserlessOrchestrator
    from app.schemas.saved_searches import FilterSchema
    
    orchestrator = BrowserlessOrchestrator(db, current_user_id)
    result = await orchestrator.execute_with_fallback(
        source=search.source,
        filters=FilterSchema(**search.filters),
        fallback_reason="manual_rerun",
        user_id=current_user_id
    )
    
    # 実際には Celery へディスパッチするか即時実行するかになるが、ここでは result を返すか queued ステータスを返す。
    # 指示では即時実行して result.success などを返す形にも見えるし、Celery の TODO もある。
    # 5. Orchestrator integration の指示では `return {"success": result.success, "items_count": len(result.items), ...}` とある。
    return {
        "success": result.success,
        "items_count": len(result.items),
        "fallback_provider": result.fallback_provider,
        "cost_estimate_jpy": result.cost_estimate_jpy,
        "execution_time_ms": result.execution_time_ms,
        "message": f"Rerun completed for saved search '{search.name}'" if result.success else f"Rerun failed: {result.error}"
    }


@router.post("/saved-searches/{search_id}/disable-monitoring")
async def disable_monitoring(
    search_id: UUID,
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    保存検索の監視を一時停止
    
    Args:
        search_id: SavedSearch ID
        current_user_id: JWT から抽出した user_id
        db: Database session
    
    Returns:
        SavedSearchResponse: 更新された保存検索
    
    Errors:
        404: リソースなし / 他ユーザーのリソース
    """
    search = db.query(SavedSearch).filter(
        SavedSearch.id == search_id,
        SavedSearch.user_id == current_user_id
    ).first()
    
    if not search:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved search not found"
        )
    
    search.is_monitoring_enabled = False
    search.next_run_at = None
    search.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(search)
    
    if hasattr(SavedSearchResponse, "model_validate"):
        return SavedSearchResponse.model_validate(search)
    return SavedSearchResponse.from_orm(search)

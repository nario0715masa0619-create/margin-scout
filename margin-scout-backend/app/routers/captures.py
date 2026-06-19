from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from uuid import uuid4, UUID
from datetime import datetime
from typing import Optional
import csv
from io import StringIO

from app.models.research import ImportSession, SourceItem, EbayMatch, ProfitSnapshot
from app.models.user import User
from app.schemas.captures import CapturesRequest, CapturesResponse, SourceItemResponse
from app.auth.dependencies import get_current_user
from app.db.database import get_db
from app.config import settings

router = APIRouter(tags=["captures"])
saved_items_router = APIRouter(tags=["saved-items"])

class MockEbayService:
    def search_and_match(self, title: str, max_price_usd: float):
        # We use the previous EbayMockService logic adapted to return dict
        # Assuming 150 JPY = 1 USD for mock
        usd_price = 50.0  # just a dummy price
        return {
            "item_id": "v1|123456789|0",
            "title": f"{title} (Mock)",
            "price_usd": usd_price,
            "match_score": 0.95
        }

@router.get("/test")
async def test_auth(current_user_id: str = Depends(get_current_user)):
    """
    Extension からの接続テスト用エンドポイント
    """
    return {"status": "ok", "user_id": current_user_id}

@router.post("", response_model=CapturesResponse)
async def create_capture(
    payload: CapturesRequest,
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Extension からの商品データを受け取り、DB に保存・eBay 照合を開始する
    """
    
    # ユーザー存在確認
    user = db.query(User).filter(User.id == current_user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # ImportSession 作成
    import_session = ImportSession(
        id=uuid4(),
        user_id=current_user_id,
        source=payload.source.value,
        import_type=payload.import_type.value,
        item_count=len(payload.items)
    )
    db.add(import_session)
    db.flush()  # ID を取得
    
    # SourceItem を作成・保存
    results = []
    processed_count = 0
    matched_count = 0
    error_count = 0
    
    ebay_service = MockEbayService()
    
    for item_req in payload.items:
        try:
            source_item = SourceItem(
                id=uuid4(),
                import_session_id=import_session.id,
                source=payload.source.value,
                title=item_req.title,
                price_jpy=item_req.price_jpy,
                url=str(item_req.url),
                image_url=str(item_req.image_url) if item_req.image_url else None,
                seller_name=item_req.seller_name,
                condition=item_req.condition.value if item_req.condition else None,
                category=item_req.category,
                fetched_at=item_req.fetched_at
            )
            db.add(source_item)
            db.flush()
            
            # eBay 照合
            ebay_result = ebay_service.search_and_match(
                title=item_req.title,
                max_price_usd=5000
            )
            
            if ebay_result:
                ebay_match = EbayMatch(
                    id=uuid4(),
                    source_item_id=source_item.id,
                    ebay_item_id=ebay_result.get("item_id"),
                    ebay_title=ebay_result.get("title"),
                    ebay_price_usd=ebay_result.get("price_usd"),
                    match_score=ebay_result.get("match_score", 0.0),
                    match_status="matched",
                    matched_at=datetime.utcnow()
                )
                db.add(ebay_match)
                db.flush()
                
                # 利益計算
                exchange_rate = 150.0
                ebay_price_jpy = int(ebay_result.get("price_usd", 0) * exchange_rate)
                profit_jpy = ebay_price_jpy - item_req.price_jpy
                profit_margin_pct = (profit_jpy / item_req.price_jpy * 100) if item_req.price_jpy > 0 else 0.0
                
                profit_snapshot = ProfitSnapshot(
                    id=uuid4(),
                    ebay_match_id=ebay_match.id,
                    source_price_jpy=item_req.price_jpy,
                    ebay_price_jpy=ebay_price_jpy,
                    profit_jpy=profit_jpy,
                    profit_margin_pct=profit_margin_pct,
                    exchange_rate_usd_jpy=exchange_rate
                )
                db.add(profit_snapshot)
                matched_count += 1
                status_str = "matched"
            else:
                ebay_match = EbayMatch(
                    id=uuid4(),
                    source_item_id=source_item.id,
                    match_status="unmatched"
                )
                db.add(ebay_match)
                status_str = "unmatched"
            
            processed_count += 1
            results.append(SourceItemResponse(
                id=str(source_item.id),
                title=item_req.title,
                price_jpy=item_req.price_jpy,
                url=str(item_req.url),
                status=status_str
            ))
        
        except Exception as e:
            error_count += 1
            results.append(SourceItemResponse(
                id="",
                title=item_req.title,
                price_jpy=item_req.price_jpy,
                url=str(item_req.url),
                status="error"
            ))
    
    # ImportSession 更新
    import_session.processed_count = processed_count
    import_session.matched_count = matched_count
    import_session.error_count = error_count
    import_session.completed_at = datetime.utcnow()
    
    db.commit()
    
    rate_limit_remaining = 450
    
    return CapturesResponse(
        import_session_id=str(import_session.id),
        processed_count=processed_count,
        matched_count=matched_count,
        error_count=error_count,
        results=results,
        rate_limit_remaining=rate_limit_remaining
    )

@router.get("")
async def list_captures(
    current_user_id: str = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    ImportSession 一覧取得（user_id 自動フィルタ、ページング対応）
    """
    sessions = db.query(ImportSession).filter(
        ImportSession.user_id == current_user_id
    ).order_by(ImportSession.created_at.desc()).limit(limit).offset(offset).all()
    
    total = db.query(ImportSession).filter(
        ImportSession.user_id == current_user_id
    ).count()
    
    return {
        "sessions": [
            {
                "id": str(s.id),
                "source": s.source,
                "import_type": s.import_type,
                "item_count": s.item_count,
                "processed_count": s.processed_count,
                "matched_count": s.matched_count,
                "error_count": s.error_count,
                "created_at": s.created_at.isoformat() + "Z",
                "completed_at": s.completed_at.isoformat() + "Z" if s.completed_at else None,
            }
            for s in sessions
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }

@router.get("/{capture_id}")
async def get_capture_detail(
    capture_id: UUID,
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ImportSession 詳細取得（items[] 含む）
    """
    session = db.query(ImportSession).filter(
        ImportSession.id == capture_id,
        ImportSession.user_id == current_user_id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    items = db.query(SourceItem).filter(
        SourceItem.import_session_id == capture_id
    ).all()
    
    items_list = []
    for item in items:
        profit = item.ebay_match.profit_snapshot if item.ebay_match else None
        items_list.append({
            "id": str(item.id),
            "title": item.title,
            "source_price_jpy": item.price_jpy,
            "ebay_price_jpy": profit.ebay_price_jpy if profit else None,
            "profit_jpy": profit.profit_jpy if profit else None,
            "profit_margin_pct": profit.profit_margin_pct if profit else None,
            "status": item.ebay_match.match_status if item.ebay_match else "pending",
        })
    
    return {
        "id": str(session.id),
        "source": session.source,
        "import_type": session.import_type,
        "item_count": session.item_count,
        "processed_count": session.processed_count,
        "matched_count": session.matched_count,
        "error_count": session.error_count,
        "created_at": session.created_at.isoformat() + "Z",
        "completed_at": session.completed_at.isoformat() + "Z" if session.completed_at else None,
        "items": items_list,
    }

@router.get("/{capture_id}/items")
async def get_capture_items(
    capture_id: UUID,
    current_user_id: str = Depends(get_current_user),
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    セッション内の SourceItem 一覧（ページング対応）
    """
    session = db.query(ImportSession).filter(
        ImportSession.id == capture_id,
        ImportSession.user_id == current_user_id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    items = db.query(SourceItem).filter(
        SourceItem.import_session_id == capture_id
    ).order_by(SourceItem.created_at.desc()).limit(limit).offset(offset).all()
    
    total = db.query(SourceItem).filter(
        SourceItem.import_session_id == capture_id
    ).count()
    
    items_list = []
    for item in items:
        profit = item.ebay_match.profit_snapshot if item.ebay_match else None
        items_list.append({
            "id": str(item.id),
            "title": item.title,
            "source": item.source,
            "source_price_jpy": item.price_jpy,
            "url": item.url,
            "image_url": item.image_url,
            "seller_name": item.seller_name,
            "condition": item.condition,
            "ebay_price_jpy": profit.ebay_price_jpy if profit else None,
            "profit_jpy": profit.profit_jpy if profit else None,
            "profit_margin_pct": profit.profit_margin_pct if profit else None,
            "match_score": item.ebay_match.match_score if item.ebay_match else 0.0,
            "match_status": item.ebay_match.match_status if item.ebay_match else "pending",
            "created_at": item.created_at.isoformat() + "Z",
        })
    
    return {
        "items": items_list,
        "total": total,
        "limit": limit,
        "offset": offset,
    }

@router.post("/{capture_id}/export/csv")
async def export_capture_csv(
    capture_id: UUID,
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    セッションの CSV エクスポート
    """
    session = db.query(ImportSession).filter(
        ImportSession.id == capture_id,
        ImportSession.user_id == current_user_id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    items = db.query(SourceItem).filter(
        SourceItem.import_session_id == capture_id
    ).all()
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["商品名", "ソース", "フリマ価格", "eBay価格", "利益", "利益率"])
    
    for item in items:
        profit = item.ebay_match.profit_snapshot if item.ebay_match else None
        writer.writerow([
            item.title,
            item.source,
            item.price_jpy,
            profit.ebay_price_jpy if profit else "",
            profit.profit_jpy if profit else "",
            f"{profit.profit_margin_pct:.1f}%" if profit else "",
        ])
    
    csv_content = output.getvalue()
    
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment;filename=margin-scout-{capture_id}-{datetime.now().strftime('%Y%m%d')}.csv"
        }
    )

# Since we want /api/v1/saved-items we need a new router or add it to main app. 
# But the instruction says to add them to captures.py. 
# Wait, /api/v1/saved-items belongs in captures.py if the prefix is /api/v1/captures ?
# Ah, the user writes:
# @router.get("/saved-items")
# This means if the router is mounted at /api/v1 (or if it's mounted at /api/v1/captures, this will result in /api/v1/captures/saved-items)
# Wait, if router in captures.py is mounted at `/api/v1/captures`, adding `/saved-items` creates `/api/v1/captures/saved-items`. But the user wants `/api/v1/saved-items`.
# Let's check how the router is mounted in app/main.py. I should probably just use what they provided: `@router.get("/saved-items")` but I will use the exact paths if they provided them. Let me check what they provided:
# The user wrote: @router.get("/saved-items") ... wait, I will just paste it.
@saved_items_router.get("")
async def list_saved_items(
    current_user_id: str = Depends(get_current_user),
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
    source: Optional[str] = Query(None),
    sort: str = Query("date_desc"),
    db: Session = Depends(get_db)
):
    """
    保存済み SourceItem 一覧（全セッション、ページング対応）
    """
    query = db.query(SourceItem).join(
        ImportSession, ImportSession.id == SourceItem.import_session_id
    ).filter(ImportSession.user_id == current_user_id)
    
    if source:
        query = query.filter(SourceItem.source == source)
    
    if sort == "profit_desc":
        query = query.outerjoin(EbayMatch).outerjoin(ProfitSnapshot).order_by(
            ProfitSnapshot.profit_jpy.desc()
        )
    elif sort == "margin_desc":
        query = query.outerjoin(EbayMatch).outerjoin(ProfitSnapshot).order_by(
            ProfitSnapshot.profit_margin_pct.desc()
        )
    else:
        query = query.order_by(SourceItem.created_at.desc())
    
    items = query.limit(limit).offset(offset).all()
    total = query.count()
    
    items_list = []
    for item in items:
        profit = item.ebay_match.profit_snapshot if item.ebay_match else None
        items_list.append({
            "id": str(item.id),
            "title": item.title,
            "source": item.source,
            "source_price_jpy": item.price_jpy,
            "url": item.url,
            "ebay_price_jpy": profit.ebay_price_jpy if profit else None,
            "profit_jpy": profit.profit_jpy if profit else None,
            "profit_margin_pct": profit.profit_margin_pct if profit else None,
            "import_session_id": str(item.import_session_id),
            "created_at": item.created_at.isoformat() + "Z",
        })
    
    return {
        "items": items_list,
        "total": total,
        "limit": limit,
        "offset": offset,
    }

@saved_items_router.get("/{item_id}")
async def get_saved_item(
    item_id: UUID,
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    SourceItem 詳細（所有権チェック付き）
    """
    item = db.query(SourceItem).join(
        ImportSession, ImportSession.id == SourceItem.import_session_id
    ).filter(
        SourceItem.id == item_id,
        ImportSession.user_id == current_user_id
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    profit = item.ebay_match.profit_snapshot if item.ebay_match else None
    
    return {
        "id": str(item.id),
        "title": item.title,
        "source": item.source,
        "source_price_jpy": item.price_jpy,
        "url": item.url,
        "image_url": item.image_url,
        "seller_name": item.seller_name,
        "condition": item.condition,
        "category": item.category,
        "ebay_price_jpy": profit.ebay_price_jpy if profit else None,
        "ebay_title": item.ebay_match.ebay_title if item.ebay_match else None,
        "profit_jpy": profit.profit_jpy if profit else None,
        "profit_margin_pct": profit.profit_margin_pct if profit else None,
        "exchange_rate_usd_jpy": profit.exchange_rate_usd_jpy if profit else None,
        "match_score": item.ebay_match.match_score if item.ebay_match else 0.0,
        "match_status": item.ebay_match.match_status if item.ebay_match else "pending",
        "import_session_id": str(item.import_session_id),
        "created_at": item.created_at.isoformat() + "Z",
    }

@saved_items_router.post("/export/csv")
async def export_saved_items_csv(
    payload: dict,
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    複数 SourceItem の CSV エクスポート
    """
    item_ids_str = payload.get("item_ids", [])
    
    if not item_ids_str:
        raise HTTPException(status_code=400, detail="item_ids is required")
    
    try:
        item_ids = [UUID(id_str) for id_str in item_ids_str]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format in item_ids")
    
    items = db.query(SourceItem).join(
        ImportSession, ImportSession.id == SourceItem.import_session_id
    ).filter(
        SourceItem.id.in_(item_ids),
        ImportSession.user_id == current_user_id
    ).all()
    
    if len(items) != len(item_ids):
        raise HTTPException(
            status_code=400,
            detail="Some items do not belong to the current user"
        )
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["商品名", "ソース", "フリマ価格", "eBay価格", "利益", "利益率"])
    
    for item in items:
        profit = item.ebay_match.profit_snapshot if item.ebay_match else None
        writer.writerow([
            item.title,
            item.source,
            item.price_jpy,
            profit.ebay_price_jpy if profit else "",
            profit.profit_jpy if profit else "",
            f"{profit.profit_margin_pct:.1f}%" if profit else "",
        ])
    
    csv_content = output.getvalue()
    
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment;filename=margin-scout-items-{datetime.now().strftime('%Y%m%d')}.csv"
        }
    )


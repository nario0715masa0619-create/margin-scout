from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Uuid, JSON, Index, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from uuid import uuid4
from typing import Optional, Dict, Any
from app.db.base import Base

class SavedSearch(Base):
    """保存検索・監視ジョブの定義"""
    __tablename__ = "saved_searches"
    
    id = Column(Uuid, primary_key=True, default=uuid4)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(256), nullable=False)
    source = Column(String(50), nullable=False)  # "mercari", "yahoo_auction", "yahoo_flea"
    
    # JSON で keyword, options, conditions, price_range, sort を管理
    filters = Column(JSON, nullable=False)
    
    # 監視設定
    is_monitoring_enabled = Column(Boolean, default=False)
    monitoring_interval_hours = Column(Integer, default=24)  # 24 = 1日
    
    # 実行状況
    next_run_at = Column(DateTime, nullable=True, index=True)
    last_run_at = Column(DateTime, nullable=True)
    last_run_status = Column(String(50), default="pending")  # "pending", "success", "failed"
    last_run_error = Column(String(512), nullable=True)
    
    # メタデータ
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # リレーション
    import_sessions = relationship("ImportSession", back_populates="saved_search")
    
    # インデックス
    __table_args__ = (
        Index('ix_saved_searches_user_monitoring', 'user_id', 'is_monitoring_enabled'),
        Index('ix_saved_searches_next_run', 'next_run_at'),
    )

class UsageLog(Base):
    """API 利用ログ（スクレイピング・eBay API呼び出し等）"""
    __tablename__ = "usage_logs"
    
    id = Column(Uuid, primary_key=True, default=uuid4)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    source = Column(String(50), nullable=False)  # "extension", "manual_rerun", "monitoring"
    fallback_provider = Column(String(50), nullable=True)  # "browserless", "http_api", etc.
    success = Column(Boolean, nullable=False)
    item_count = Column(Integer, default=0)
    cost_estimate = Column(Float, default=0.0)  # 推定コスト（¥）
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # インデックス
    __table_args__ = (
        Index('ix_usage_logs_user_created', 'user_id', 'created_at'),
    )

class ImportSession(Base):
    __tablename__ = "import_sessions"
    
    id = Column(Uuid, primary_key=True, default=uuid4)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    source = Column(String, nullable=False)  # "mercari", "yahoo_auction", "yahoo_flea"
    import_type = Column(String, nullable=False)  # "manual", "auto", "monitoring"
    item_count = Column(Integer, default=0)
    processed_count = Column(Integer, default=0)
    matched_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # 新規フィールド: SavedSearch への FK（NULL = Extension からの直接キャプチャ）
    saved_search_id = Column(Uuid, ForeignKey("saved_searches.id"), nullable=True)
    
    # リレーション
    source_items = relationship("SourceItem", back_populates="import_session")
    saved_search = relationship("SavedSearch", back_populates="import_sessions")

class SourceItem(Base):
    __tablename__ = "source_items"
    
    id = Column(Uuid, primary_key=True, default=uuid4)
    import_session_id = Column(Uuid, ForeignKey("import_sessions.id"), nullable=False)
    source = Column(String, nullable=False)
    source_id = Column(String, nullable=True)  # フリマ側の商品 ID（あれば）
    title = Column(String, nullable=False)
    price_jpy = Column(Integer, nullable=False)
    url = Column(String, nullable=False)
    image_url = Column(String, nullable=True)
    seller_name = Column(String, nullable=True)
    condition = Column(String, nullable=True)  # "new", "almost_new", ...
    category = Column(String, nullable=True)
    fetched_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # リレーション
    import_session = relationship("ImportSession", back_populates="source_items")
    ebay_match = relationship("EbayMatch", back_populates="source_item", uselist=False)

class EbayMatch(Base):
    __tablename__ = "ebay_matches"
    
    id = Column(Uuid, primary_key=True, default=uuid4)
    source_item_id = Column(Uuid, ForeignKey("source_items.id"), nullable=False)
    ebay_item_id = Column(String, nullable=True)
    ebay_title = Column(String, nullable=True)
    ebay_price_usd = Column(Float, nullable=True)
    match_score = Column(Float, default=0.0)  # 0.0-1.0
    match_status = Column(String, default="pending")  # "pending", "matched", "unmatched", "error"
    matched_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # リレーション
    source_item = relationship("SourceItem", back_populates="ebay_match")
    profit_snapshot = relationship("ProfitSnapshot", back_populates="ebay_match", uselist=False)

class ProfitSnapshot(Base):
    __tablename__ = "profit_snapshots"
    
    id = Column(Uuid, primary_key=True, default=uuid4)
    ebay_match_id = Column(Uuid, ForeignKey("ebay_matches.id"), nullable=False)
    source_price_jpy = Column(Integer, nullable=False)
    ebay_price_jpy = Column(Integer, nullable=False)
    profit_jpy = Column(Integer, nullable=False)
    profit_margin_pct = Column(Float, nullable=False)
    exchange_rate_usd_jpy = Column(Float, nullable=False)
    calculated_at = Column(DateTime, default=datetime.utcnow)
    
    # リレーション
    ebay_match = relationship("EbayMatch", back_populates="profit_snapshot")

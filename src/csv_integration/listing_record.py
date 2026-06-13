"""
Listing Data Models

Phase 3 で使用するデータモデル定義
"""

from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

@dataclass
class ValidatedResearchRecord:
    """
    Layer 1: バリデーション・正規化済みレコード

    Research CSV をバリデーション・正規化したもの。
    まだ出品用に変換されていない。
    """
    
    # Research CSV からのフィールド
    candidate_id: str
    product_name: str
    reference_price: Decimal
    currency: str
    product_url: str
    source_type: str
    observed_date: datetime
    research_status: str
    
    # Optional fields
    brand: Optional[str] = None
    model_number: Optional[str] = None
    category: Optional[str] = None
    condition: Optional[str] = None
    user_notes: Optional[str] = None
    user_tags: List[str] = field(default_factory=list)
    judgement_flag: Optional[str] = None
    
    # Validation metadata
    validation_status: str = "pending"
    validation_timestamp: Optional[datetime] = None
    validation_errors: List[str] = field(default_factory=list)
    validation_warnings: List[str] = field(default_factory=list)

@dataclass
class ListingPreparationRecord(ValidatedResearchRecord):
    """
    Layer 2: 出品準備レコード

    SKU 付与、画像解決が実施された段階。
    """
    
    sku: str = ""
    sku_strategy_applied: str = "auto_generation"
    image_dir: str = ""
    image_dir_exists: bool = False
    image_count: int = 0
    image_files: List[str] = field(default_factory=list)
    
    completeness_status: str = "incomplete"
    missing_fields: List[str] = field(default_factory=list)
    pending_fields: List[str] = field(default_factory=list)

@dataclass
class ListingReadyRecord(ListingPreparationRecord):
    """
    Layer 3: 出品準備完了レコード

    すべての必須情報が確定した段階。
    Phase 4 へ引き渡し可能。
    """
    
    listing_ready: bool = False
    ready_timestamp: Optional[datetime] = None
    
    # eBay 関連フィールド（未実装）
    ebay_category_id: Optional[str] = None
    ebay_title_template: Optional[str] = None
    ebay_description_template: Optional[str] = None
    
    # 監査情報
    audit_trail: dict = field(default_factory=lambda: {
        "research_id": "",
        "listing_sku": "",
        "source_type": "",
        "source_url": "",
        "observed_date": "",
        "transformation_timestamp": "",
    })

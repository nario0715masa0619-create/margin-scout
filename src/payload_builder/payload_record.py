"""
eBay Payload Records

Phase 4 で使用するペイロードモデル定義
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict
from datetime import datetime
from decimal import Decimal

@dataclass
class PayloadPreparationRecord:
    """
    Layer 1: Payload 準備レコード

    ListingReadyRecord をもとに、title/description 整形準備、
    category/condition 正規化準備を実施。
    """
    
    # Phase 3 からの基本情報
    candidate_id: str
    sku: str
    product_name: str
    category: str
    condition: str
    
    # Optional
    brand: Optional[str] = None
    model_number: Optional[str] = None
    
    # Layer 1 で準備
    title_draft: str = ""
    description_draft: str = ""
    category_normalized: str = ""
    condition_normalized: str = ""
    
    # 画像
    image_dir: str = ""
    image_list: List[str] = field(default_factory=list)
    
    # Price/Quantity
    listing_price: Optional[Decimal] = None
    quantity: int = 1
    
    # 準備状態
    preparation_status: str = "pending"
    preparation_warnings: List[str] = field(default_factory=list)

@dataclass
class ValidatedPayloadRecord(PayloadPreparationRecord):
    """
    Layer 2: バリデーション済みペイロードレコード

    全フィールドをバリデーション、title/description を最終化、
    readiness 判定。
    """
    
    # Layer 2 で確定
    title: str = ""
    description: str = ""
    
    ebay_category_id: Optional[str] = None
    ebay_condition: str = ""
    
    # Readiness 判定
    payload_readiness: str = "incomplete"  # ready / pending_review / incomplete / rejected
    readiness_reason: str = ""
    requires_review: bool = False
    review_items: List[str] = field(default_factory=list)
    
    # Validation
    validation_result: Dict = field(default_factory=lambda: {
        "passed": False,
        "errors": [],
        "warnings": [],
    })
    
    validation_timestamp: Optional[datetime] = None
    
    def to_ebay_payload(self) -> Dict:
        """
        Layer 3: eBay API 用 JSON に変換
        """
        return {
            "sku": self.sku,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "condition": self.ebay_condition,
            "price": self.listing_price,
            "quantity": self.quantity,
            "images": self.image_list,
            "item_specifics": {
                "Brand": self.brand,
                "Model": self.model_number,
            },
        }
        
    def to_audit_trail(self) -> Dict:
        """
        監査トレイル生成
        """
        return {
            "candidate_id": self.candidate_id,
            "sku": self.sku,
            "payload_readiness": self.payload_readiness,
            "readiness_reason": self.readiness_reason,
            "validation_status": self.validation_result.get("passed", False),
            "review_items": self.review_items,
        }

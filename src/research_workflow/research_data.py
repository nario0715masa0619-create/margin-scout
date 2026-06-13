"""
MarginScout Research Data Models

このモジュールは、リサーチワークフローで使用されるデータモデルを定義します。

設計ドキュメント: docs/RESEARCH_DATA_MODEL.md
詳細ワークフロー: docs/PHASE2_RESEARCH_WORKFLOW.md
"""

from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from enum import Enum


class SourceType(str, Enum):
    EBAY_LISTING = "ebay_listing"
    AMAZON_LISTING = "amazon_listing"
    MANUAL_INPUT = "manual_input"
    STORE_OBSERVATION = "store_observation"


class DataSourceMethod(str, Enum):
    WEB_SCRAPER = "web_scraper"
    MANUAL = "manual"
    API = "api"
    OCR = "ocr"


class ResearchStatus(str, Enum):
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    CONFIRMED = "confirmed"
    EXCLUDED = "excluded"


class JudgementFlag(str, Enum):
    PROMISING = "promising"
    HOLD = "hold"
    REJECTED = "rejected"
    NEEDS_REVIEW = "needs_review"


class Condition(str, Enum):
    NEW = "new"
    USED = "used"
    REFURBISHED = "refurbished"
    UNKNOWN = "unknown"


@dataclass
class ResearchCandidate:
    """
    リサーチ候補エンティティ
    
    参考価格リサーチから得られた商品候補を表現する。
    出品用の最終形ではなく、仕入れ判定や候補整理に用いる
    中間データ構造。
    """
    
    candidate_id: str
    product_name: str
    product_url: str
    source_type: SourceType
    reference_price: Decimal
    currency: str
    observed_date: datetime
    data_source: DataSourceMethod
    
    brand: Optional[str] = None
    model_number: Optional[str] = None
    category: Optional[str] = None
    
    price_low: Optional[Decimal] = None
    price_high: Optional[Decimal] = None
    condition: Optional[Condition] = None
    
    collection_timestamp: datetime = field(default_factory=datetime.utcnow)
    
    user_notes: Optional[str] = None
    user_tags: List[str] = field(default_factory=list)
    judgement_flag: Optional[JudgementFlag] = None
    
    research_status: ResearchStatus = ResearchStatus.DRAFT
    csv_export_ready: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict:
        return {
            'candidate_id': self.candidate_id,
            'product_name': self.product_name,
            'reference_price': str(self.reference_price),
            'currency': self.currency,
            'brand': self.brand or '',
            'model_number': self.model_number or '',
            'category': self.category or '',
            'product_url': self.product_url,
            'source_type': self.source_type.value,
            'observed_date': self.observed_date.isoformat(),
            'condition': self.condition.value if self.condition else '',
            'user_notes': self.user_notes or '',
            'user_tags': ';'.join(self.user_tags) if self.user_tags else '',
            'judgement_flag': self.judgement_flag.value if self.judgement_flag else '',
            'research_status': self.research_status.value,
        }
    
    def mark_for_export(self) -> None:
        self.csv_export_ready = True
        self.updated_at = datetime.utcnow()
    
    def exclude(self) -> None:
        self.research_status = ResearchStatus.EXCLUDED
        self.csv_export_ready = False
        self.updated_at = datetime.utcnow()

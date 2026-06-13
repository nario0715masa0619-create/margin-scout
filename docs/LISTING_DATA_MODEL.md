# MarginScout: Listing Data Model

**作成日**: 2026-06-13  
**バージョン**: 0.1  
**ステータス**: 設計段階

---

## Listing Data Model 層構造

### Layer 1: Validated & Normalized Record
Research CSV をバリデーション・正規化したもの。

```python
class ValidatedResearchRecord:
    candidate_id: str              # ms-res-20260613-0001
    product_name: str
    reference_price: Decimal
    currency: str
    brand: Optional[str]
    model_number: Optional[str]
    category: Optional[str]
    product_url: str
    source_type: str
    observed_date: datetime
    condition: Optional[str]
    user_notes: Optional[str]
    user_tags: List[str]
    judgement_flag: Optional[str]
    research_status: str
    
    # Validation fields
    validation_status: str         # "passed", "warnings", "error"
    validation_timestamp: datetime
    validation_errors: List[str]
    validation_warnings: List[str]
```

### Layer 2: Listing Preparation Record
SKU, 画像解決が追加された段階。

```python
class ListingPreparationRecord(ValidatedResearchRecord):
    sku: str                       # MARGIN-20260613-0001 (新規)
    sku_strategy_applied: str      # "auto_generation"
    image_dir: str                 # data/images/MARGIN-20260613-0001/
    image_dir_exists: bool
    image_count: int
    image_files: List[str]         # ["01.jpg", "02.jpg", ...]
    
    # Completeness
    completeness_status: str       # "ready", "pending_review", "incomplete"
    missing_fields: List[str]      # 欠けている必須フィールド
    pending_fields: List[str]      # レビュー待ちフィールド
```

### Layer 3: Listing-Ready Record
すべての必須情報が確定した段階。

```python
class ListingReadyRecord(ListingPreparationRecord):
    listing_ready: bool            # True
    ready_timestamp: datetime
    
    # eBay-related (未実装、構造のみ)
    ebay_category_id: Optional[str]
    ebay_title_template: Optional[str]
    ebay_description_template: Optional[str]
    
    # Audit trail
    audit_trail: {
        "research_id": str,
        "listing_sku": str,
        "source_type": str,
        "source_url": str,
        "observed_date": datetime,
        "transformation_timestamp": datetime,
    }
```

---

## 責務マトリックス

| レイヤー | 処理責務 | 出力成果物 |
|---|---|---|
| Layer 1 | CSV 取込 + バリデーション + 正規化 | Validated records |
| Layer 2 | SKU 付与 + 画像解決 + 補完判定 | Preparation records |
| Layer 3 | 最終チェック + 監査情報確定 | Ready records + Transformed CSV |
| Layer 4 (未実装) | eBay カテゴリマッピング + Payload 生成 | Payload records |

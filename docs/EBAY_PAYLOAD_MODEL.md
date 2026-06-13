# MarginScout: eBay Payload Model

**作成日**: 2026-06-13  
**バージョン**: 0.1  
**ステータス**: 設計段階

---

## Payload Model 層構造

### Layer 1: Payload Preparation Record
ListingReadyRecord をもとに、title/description 整形準備、category/condition 正規化準備を実施。

```python
class PayloadPreparationRecord:
    # Phase 3 からの基本情報
    candidate_id: str
    sku: str
    product_name: str
    category: str
    condition: str
    brand: Optional[str]
    model_number: Optional[str]
    
    # Layer 1 で準備
    title_draft: str              # product_name ベース
    description_draft: str        # user_notes から整形
    category_normalized: str      # 内部正規化
    condition_normalized: str     # 内部正規化
    
    # 画像
    image_dir: str
    image_list: List[str]         # [01.jpg, 02.jpg, ...]
    
    # Price/Quantity
    listing_price: Optional[Decimal]  # None のまま
    quantity: int = 1
    
    # 準備状態
    preparation_status: str       # ready_for_validation
    preparation_warnings: List[str]
```

### Layer 2: Validated Payload Record
全フィールドをバリデーション、title/description を最終化、readiness 判定。

```python
class ValidatedPayloadRecord(PayloadPreparationRecord):
    # Layer 2 で確定
    title: str                    # 最終 title（80文字以下）
    description: str              # 最終 description（HTML escape済み）
    
    ebay_category_id: Optional[str]  # None でもよい（Phase 5 で決定）
    ebay_condition: str           # new / used / refurbished
    
    # Readiness 判定
    payload_readiness: str        # ready / pending_review / incomplete / rejected
    readiness_reason: str
    requires_review: bool
    review_items: List[str]       # ["brand未確定", "price未決定", ...]
    
    # Validation
    validation_result: {
        "passed": bool,
        "errors": List[str],
        "warnings": List[str],
    }
    
    validation_timestamp: datetime
```

### Layer 3: Final eBay Payload Input Record
eBay API に渡す形式の JSON。

```python
{
    "sku": str,
    "title": str,
    "description": str,
    "category": str,
    "condition": str,           # new / used / refurbished
    "price": Optional[Decimal], # None は許容
    "quantity": int,
    "images": List[str],        # file paths
    
    "item_specifics": {
        "Brand": Optional[str],
        "Model": Optional[str],
    },
}
```

### Audit Record
payload 本体とは別に保持する監査情報。

```python
{
    # 識別情報
    "candidate_id": str,
    "sku": str,
    
    # 源泉情報
    "source_url": str,
    "source_type": str,
    "observed_price": Decimal,
    "observed_date": datetime,
    
    # タイムスタンプ
    "collection_timestamp": datetime,
    "transformation_timestamp": datetime,
    "payload_generation_timestamp": datetime,
    
    # 決定理由
    "title_template": str,
    "condition_mapped_from": str,
    "category_mapped_from": str,
    
    # Validation
    "validation_status": str,
    "readiness_level": str,
    
    # ユーザー情報
    "user_notes": str,
    "user_tags": List[str],
    
    # Version
    "payload_version": str,
    "builder_version": str,
}
```

---

## 責務マトリックス

| レイヤー | 処理責務 | 出力成果物 |
|---|---|---|
| Layer 1 | 入力 readiness 検証 + title/desc draft + category/condition 準備 | Preparation records |
| Layer 2 | title/desc 最終化 + mapping 試行 + readiness 判定 | Validated records |
| Layer 3 | Payload JSON 生成 + Audit trail 生成 | eBay Payload Input + Audit |
| Phase 5+ (未実装) | Payload schema 検証 + Executor 実装 | Live/Dry-run execution |

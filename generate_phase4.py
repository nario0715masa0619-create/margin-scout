import os
import json
from datetime import datetime

project_path = "C:/NewProjects/margin-scout"
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

print("🚀 MarginScout Phase 4: eBay Payload Builder Design")
print("=" * 70)

# ============================================================================
# 1. Create docs/PHASE4_EBAY_PAYLOAD_BUILDER.md
# ============================================================================

phase4_main_doc = r'''# MarginScout Phase 4: eBay Payload Builder 設計

**作成日**: 2026-06-13  
**フェーズ**: Phase 4 - eBay Payload Builder 設計  
**ステータス**: 設計段階  
**前提**: Phase 1-3 完了、ListingReadyRecord 定義済み

---

## 目次

1. [概要](#概要)
2. [Payload Builder の全体像](#payload-builder-の全体像)
3. [Payload 入力仕様](#payload-入力仕様)
4. [eBay Payload 用の内部データモデル設計](#ebay-payload-用の内部データモデル設計)
5. [title 設計方針](#title-設計方針)
6. [description 設計方針](#description-設計方針)
7. [category 設計方針](#category-設計方針)
8. [condition 設計方針](#condition-設計方針)
9. [price / quantity 設計方針](#price--quantity-設計方針)
10. [画像 Payload 設計方針](#画像-payload-設計方針)
11. [Payload Readiness 判定](#payload-readiness-判定)
12. [Dry-Run 前提の設計](#dry-run-前提の設計)
13. [監査・追跡のための設計](#監査追跡のための設計)

---

## 概要

Phase 4 の目的は、Phase 3 で定義した `ListingReadyRecord` をもとに、**eBay 出品に必要な内部 payload モデルを設計**し、将来の出品実装へ安全に引き渡せるようにすることです。

**重要な前提**:

- Payload Builder は **API client ではない**
- Payload Builder は **出品前データ整形責務に集中**
- Live 実行はまだ行わず、**dry-run 接続を意識した設計**
- 未確定情報を黙って埋めない → review フラグで明示
- **追跡性と監査性を常に保持**

---

## Payload Builder の全体像

### ワークフロー図

```
┌──────────────────────────────────────┐
│ Phase 3 Output: ListingReadyRecord     │
│ ・sku, product_name, category, ...     │
│ ・image_dir, image_count, ...          │
│ ・validation_status, completeness      │
└────────────────┬─────────────────────┘
                 │
                 ▼ 【Phase 4: Payload Builder】
        ┌────────┴────────┐
        │                 │
        ▼                 ▼
     Step 1:           Step 2:
    Readiness      Title/Description
     再検証            整形準備
        │                 │
        └────────┬────────┘
                 ▼
              Step 3:
         Category/Condition
        正規化・マッピング
                 │
                 ▼
              Step 4:
           Price/Quantity
       validation & 補完判定
                 │
                 ▼
              Step 5:
               Images
      Directory → Image List
                 │
                 ▼
              Step 6:
        Payload Generation
   eBay Payload Input Record 生成
                 │
                 ▼
              Step 7:
         Validation Report
    Readiness / Review Required 判定
        ┌────────┴────────┐
        │                 │
        ▼                 ▼
     Payload          Audit Trail
     (JSON)            (JSON)
        │                 │
        └────────┬────────┘
                 ▼
         【Payload Output】
   ・eBay Payload Input Record
   ・Validation Report
   ・Audit Trail
                 │
                 ▼
      【Phase 5: Executor (未実装)】
   ・Dry-Run validation
   ・API client preparation
   ・Live execution (将来)
```

### 段階的な処理フロー

| Step | 入力 | 処理 | 出力 | 責務 |
|------|------|------|------|------|
| 1 | ListingReadyRecord | readiness 再検証 | Validation check | Readiness Validator |
| 2 | Validated record | title/description 整形準備 | Title/Desc draft | Title/Description Builder |
| 3 | Draft record | category/condition 正規化 | Normalized category/condition | Category/Condition Mapper |
| 4 | Normalized | price/quantity validation | Price/quantity validated | Price/Quantity Validator |
| 5 | Validated | Image directory → list | Image list resolved | Image Mapper |
| 6 | All fields ready | Payload JSON 構築 | eBay Payload Record | Payload Serializer |
| 7 | Payload | Validation report 作成 | Readiness report | Payload Validator |
| 8 | Report | Final decision | Payload + Audit | Output Generator |

---

## Payload 入力仕様

### ListingReadyRecord からの必須フィールド

| # | フィールド | 型 | 必須 | Payload用途 | 説明 |
|----|----------|-----|------|-----------|------|
| 1 | candidate_id | String | ✅ | 監査・追跡 | Research 元 ID（永続保持） |
| 2 | sku | String | ✅ | Payload 本体 | 出品用 SKU |
| 3 | product_name | String | ✅ | Title 入力 | Title 基盤 |
| 4 | category | String | ✅ | Category mapper | eBay category へマッピング |
| 5 | condition | String | ✅ | Condition mapper | eBay condition へ正規化 |
| 6 | brand | String | △ | Title に含める | Brand 補助 |
| 7 | model_number | String | △ | Title に含める | Model/MPN 補助 |
| 8 | reference_price | Decimal | ✗ | 監査用のみ | 出品価格ではない（参考値） |
| 9 | listing_status | String | ✅ | Readiness 判定 | ready / pending_review / incomplete |
| 10 | validation_status | String | ✅ | Validation report | passed / warnings / error |
| 11 | completeness_status | String | ✅ | Readiness 判定 | ready / pending_review / incomplete |
| 12 | source_url | String | ✅ | 監査用 | Reference source |
| 13 | source_type | String | ✅ | 監査用 | データ取得元 |
| 14 | observed_date | DateTime | ✅ | 監査用 | 観測日時 |
| 15 | image_dir | String | ✅ | Image mapper | 画像ディレクトリ |
| 16 | image_count | Integer | ✅ | Image list | 画像数 |
| 17 | user_notes | String | △ | Description 補助 | ユーザーメモ（公開しない） |
| 18 | user_tags | List[String] | △ | 監査用 | 内部用タグ |

### フィールド分類

#### Payload Builder 必須（payload 化に必須）
- sku, product_name, category, condition, image_dir, image_count

#### Payload Builder 補助（あると良い）
- brand, model_number, user_notes（公開用に整形後）

#### 監査専用（payload に含めず監査で保持）
- candidate_id, source_url, source_type, observed_date, user_tags

#### Phase 5以降で決定
- listing_price（Phase 4 では決めない）
- ebay_category_id（外部 resolver 依存）
- ebay_condition_id（外部 mapper 依存）

---

## eBay Payload 用の内部データモデル設計

### Layer 構造（Phase 3 → Phase 4 → Phase 5）

```
【Layer 0】ListingReadyRecord (Phase 3 出力)
      ↓
【Layer 1】Payload Preparation Record
  ・Readiness 再検証完了
  ・title draft / description draft 作成
  ・category / condition 正規化準備
  ・image list 構築
      ↓
【Layer 2】Validated Payload Record
  ・title 最終化
  ・description 最終化
  ・category / condition マッピング完了
  ・price / quantity 確定
  ・image list 確定
  ・readiness level 確定 (ready / pending_review / incomplete)
      ↓
【Layer 3】Final eBay Payload Input Record
  ・eBay API に渡す形式の JSON
  ・必須項目 100% 確定
  ・optional 項目は明示的に null
      ↓
【Audit Record】
  ・candidate_id, sku 永続
  ・source 情報保持
  ・transformation 履歴
  ・validation report
  ・version / timestamp
```

### 各層の責務

#### Layer 1: Payload Preparation Record

```python
{
    # Phase 3 からの基本情報
    "candidate_id": "ms-res-20260613-0001",
    "sku": "MARGIN-20260613-0001",
    "product_name": "Canon EF 50mm f/1.8 STM",
    "category": "Camera Lenses",
    "condition": "new",
    "brand": "Canon",
    "model_number": "EF50STM",
    
    # Layer 1 で準備
    "title_draft": "Canon EF 50mm f/1.8 STM Lens - New",
    "description_draft": "Professional quality lens. Excellent condition...",
    "category_normalized": "Camera Lenses",  # 内部正規化
    "condition_normalized": "new",
    
    # 画像
    "image_dir": "data/images/MARGIN-20260613-0001/",
    "image_list": ["01.jpg", "02.jpg", "03.jpg"],
    
    # Price/Quantity (未確定)
    "listing_price": None,  # Phase 5 で決定
    "quantity": 1,
    
    # 準備状態
    "preparation_status": "ready_for_validation",
    "preparation_warnings": [],
}
```

#### Layer 2: Validated Payload Record

```python
{
    # Layer 1 をすべて継承
    ...
    
    # Layer 2 で確定
    "title": "Canon EF 50mm f/1.8 STM Lens - Excellent Condition",
    "description": "...(final formatted)...",
    
    "ebay_category_id": None,  # phase 5 で設定予定
    "ebay_condition": "new",
    
    "listing_price": None,  # 未定（Phase 5）
    "quantity": 1,
    
    # Readiness 判定
    "payload_readiness": "ready",  # ready / pending_review / incomplete
    "readiness_reason": "All required fields confirmed",
    "requires_review": False,
    "review_items": [],
    
    # Validation
    "validation_result": {
        "passed": True,
        "errors": [],
        "warnings": [],
    },
    
    "validation_timestamp": "2026-06-13T16:00:00Z",
}
```

#### Layer 3: Final eBay Payload Input Record

```python
{
    # eBay API に渡す形式（JSON）
    "sku": "MARGIN-20260613-0001",
    "title": "Canon EF 50mm f/1.8 STM Lens - Excellent Condition",
    "description": "...(HTML/text formatted)...",
    "category": "Camera Lenses",
    "condition": "new",
    "price": None,  # 未確定、phase 5 で補充
    "quantity": 1,
    "images": [
        "data/images/MARGIN-20260613-0001/01.jpg",
        "data/images/MARGIN-20260613-0001/02.jpg",
        "data/images/MARGIN-20260613-0001/03.jpg",
    ],
    
    # 拡張フィールド（将来 API client で使用）
    "item_specifics": {
        "Brand": "Canon",
        "Model": "EF50STM",
    },
}
```

---

## title 設計方針

### Title 生成ロジック

原則:

- product_name を基盤にする
- brand / model_number / condition を optional に含める
- 80文字制限を厳守
- テンプレート方式で複数パターン対応

### Title Template パターン

**Template A: 標準形式**
```
{BRAND} {PRODUCT_NAME} - {CONDITION}

例: Canon EF 50mm f/1.8 STM - New
    (56文字)
```

**Template B: Model 含有**
```
{BRAND} {MODEL} {PRODUCT_NAME} - {CONDITION}

例: Canon EF50STM EF 50mm f/1.8 STM Lens - New
    (62文字)
```

**Template C: シンプル形式**
```
{PRODUCT_NAME}

例: Canon EF 50mm f/1.8 STM
    (25文字)
```

### Title 確定ルール

```python
def generate_title(product_name, brand, model, condition, template="A"):
    """
    Phase 4 では template A を推奨
    """
    if template == "A":
        title = f"{brand} {product_name} - {condition}"
    elif template == "B":
        title = f"{brand} {model} {product_name} - {condition}"
    else:
        title = product_name
    
    # 80文字制限
    if len(title) > 80:
        title = title[:77] + "..."
    
    return title
```

### Title 未確定時の扱い

- product_name が空 → Hard Error
- title が 80文字超 → 自動切り詰め + Warning
- brand/model 未確定 → Template C（シンプル形式）で対応

---

## description 設計方針

### Description 構成方針

原則:

- user_notes はそのまま公開文に流さない
- 内部メモと公開文を分離
- Description は「標準テンプレート」ベース
- source 情報を無条件転記しない

### Description Template 構成

```
【Header】
{PRODUCT_NAME}
{BRAND} | {MODEL} | {CONDITION}

【Body】
商品説明：
{USER_NOTES_FORMATTED}

追加情報：
- 参考価格: ${REFERENCE_PRICE}
- 観測日: {OBSERVED_DATE}

【Footer】
【注意】
本出品は MarginScout により自動生成されました。
ご不明な点はお問い合わせください。
```

### Description 生成ロジック

```python
def generate_description(product_name, brand, model, condition, 
                        user_notes, reference_price, observed_date):
    """
    user_notes は HTML escape + sanitize
    source URL は含めない（監査用に別途保持）
    """
    header = f"{product_name}\n{brand} | {model} | {condition}\n"
    body = f"商品説明：\n{sanitize_html(user_notes)}\n"
    footer = "【注意】本出品は MarginScout により..."
    
    return header + body + footer
```

### Description 未確定時の扱い

- user_notes が空 → テンプレートのみで OK（Warning）
- description が長い（制限値超） → 自動切り詰め + Warning
- HTML 特殊文字 → Escape 処理

---

## category 設計方針

### Category の二層構造

```
【Phase 3 出力】
internal_category: "Camera Lenses"  (内部カテゴリ)

【Phase 4 入力】
internal_category → category mapper

【Phase 4 出力】
ebay_category_id: None  (Phase 5 で決定予定)
または
ebay_category_id: "12345"  (mapper に成功した場合)
```

### Category Mapping ルール（設計のみ、実装は Phase 5）

```python
CATEGORY_MAP = {
    "Camera Lenses": {
        "ebay_category_id": "625",  # eBay Electronics > Camera
        "confidence": "high",
    },
    "Footwear": {
        "ebay_category_id": "15687",  # eBay Clothing & Accessories > Shoes
        "confidence": "high",
    },
    "Audio Equipment": {
        "ebay_category_id": "14938",  # eBay Electronics > Audio
        "confidence": "medium",
    },
}
```

### Category 未確定時の扱い

- category が未設定 → Hard Error（payload 不可）
- category が unknown → Pending Review
- category が mapping 不可 → Pending Review

---

## condition 設計方針

### Condition 正規化マッピング

```
【内部表現】          【eBay表現】
new          →       new
used         →       used
refurbished  →       refurbished
unknown      →       (mapping 不可→ Pending Review)
```

### Condition 確定ルール

```python
CONDITION_MAP = {
    "new": "new",
    "used": "used",
    "refurbished": "refurbished",
}

def normalize_condition(condition):
    if condition in CONDITION_MAP:
        return CONDITION_MAP[condition], "valid"
    else:
        return None, "pending_review"
```

### Condition 未確定時の扱い

- condition が未設定 → デフォルト "new" を提案（Warning + Pending Review）
- condition が unknown → Pending Review

---

## price / quantity 設計方針

### Price の二層構造

```
【Phase 3】
reference_price: 189.99  (参考価格・監査用)

【Phase 4】
listing_price: ???  (未確定・Phase 5 で決定)
```

### Price 確定ルール

- reference_price は「参考値」であり、出品価格ではない
- listing_price は Phase 4 では決めない（将来 price strategy module で決定）
- Phase 4 では listing_price = None のまま → Pending Review フラグで「価格未決定」を明示

### Quantity の扱い

- quantity: 1  (デフォルト、phase 4 で固定)
- 将来の multi-quantity 対応は Phase 5+

### Price/Quantity 未確定時の扱い

- reference_price が負数 → Hard Error
- listing_price が None → Pending Review（「価格要決定」）
- quantity = 0 → Hard Error

---

## 画像 Payload 設計方針

### Image List 構築ロジック

```
入力:  image_dir = "data/images/MARGIN-20260613-0001/"
      image_count = 3

処理:  
1. ディレクトリ存在確認
2. ファイル走査 (01.jpg, 02.jpg, ...)
3. パターンA（ゼロパディング） 前提に順序決定

出力:  image_list = [
         "data/images/MARGIN-20260613-0001/01.jpg",
         "data/images/MARGIN-20260613-0001/02.jpg",
         "data/images/MARGIN-20260613-0001/03.jpg",
       ]
```

### Image Validation ルール

| 条件 | 判定 | 対応 |
|---|---|---|
| ディレクトリ存在 + 1枚以上 | ✅ | Ready |
| ディレクトリ存在 + 0枚 | ⚠️ | Warning |
| ディレクトリ未存在 | ❌ | Hard Error |
| ファイル形式不正 (.jpg 以外) | ❌ | Hard Error |

### Image 未確定時の扱い

- image_dir が空 → Hard Error
- image_count = 0 → Warning + Pending Review（「画像未配置」）
- image 拡張子が .jpg 以外 → Hard Error

### Image 最適化

- Phase 4: ファイル列挙・順序確定のみ
- Phase 5+: 画像リサイズ・最適化・アップロード

---

## Payload Readiness 判定

### Readiness Level 定義

| Level | 判定 | 次のステップ | 例 |
|---|---|---|---|
| ready | 出品可能 | Phase 5: dry-run / live 実行 | 全項目確定、レビュー不要 |
| pending_review | レビュー待ち | ユーザー補完 | brand 未確定、category mapping 未確定 |
| incomplete | 入力不足 | 入力補完 | title 生成不可、画像未配置 |
| rejected | 不正・除外 | 処理停止 | research_status = excluded |

### Readiness 判定ロジック

```python
def judge_readiness(payload_record):
    """
    Payload 化可能かを判定
    """
    
    # Hard Error チェック
    if not payload_record.sku:
        return "rejected", "SKU empty"
    if not payload_record.product_name:
        return "rejected", "product_name empty"
    if payload_record.image_count == 0:
        return "incomplete", "No images"
    
    # Optional フィールドチェック
    review_items = []
    if not payload_record.brand:
        review_items.append("brand未確定")
    if not payload_record.category_normalized:
        review_items.append("category未確定")
    if payload_record.listing_price is None:
        review_items.append("listing_price未決定")
    
    if review_items:
        return "pending_review", review_items
    
    return "ready", None
```

---

## Dry-Run 前提の設計

### Payload + Validation Report の分離

```
【出力】Payload Builder から

1. eBay Payload Input Record (JSON)
   {
     "sku": "...",
     "title": "...",
     "description": "...",
     ...
   }

2. Validation Report (JSON)
   {
     "readiness": "ready" | "pending_review" | "incomplete",
     "validation_result": {
       "passed": True/False,
       "errors": [...],
       "warnings": [...],
     },
     "review_items": [
       "brand未確定",
       "category mapping未確定",
     ],
   }

3. Audit Trail (JSON)
   {
     "candidate_id": "...",
     "sku": "...",
     "transformation_timestamp": "...",
     ...
   }
```

### Dry-Run での検証ポイント

```
Phase 5 (Executor) での dry-run では以下をチェック:

1. eBay API スキーマ検証
2. 必須項目の presence check
3. eBay category ID 有効性チェック
4. Title / description の length check
5. Image URL 有効性チェック
6. Price 妥当性チェック

Phase 4 はここまで含めない
→ Phase 4 は「payload 整形」まで
→ Phase 5 が「API schema 検証」以降を担当
```

---

## 監査・追跡のための設計

### Audit Trail 構造

```python
{
    # 識別情報
    "candidate_id": "ms-res-20260613-0001",  # Research 元 ID
    "sku": "MARGIN-20260613-0001",            # Listing SKU
    
    # 源泉情報
    "source_url": "https://www.ebay.com/itm/...",
    "source_type": "ebay_listing",
    "observed_price": 189.99,
    "observed_date": "2026-06-13T14:30:00Z",
    
    # 処理タイムスタンプ
    "collection_timestamp": "2026-06-13T14:35:00Z",     # Phase 2
    "transformation_timestamp": "2026-06-13T15:05:00Z", # Phase 3
    "payload_generation_timestamp": "2026-06-13T16:00:00Z",  # Phase 4
    
    # 決定理由
    "title_template_used": "A",
    "title_generation_reason": "standard_format",
    "condition_mapped_from": "new",
    "category_mapped_from": "Camera Lenses",
    
    # Validation 結果
    "validation_status": "passed",
    "readiness_level": "ready",
    
    # ユーザー情報
    "user_notes": "状態良好・レンズクリア",
    "user_tags": ["high-demand"],
    
    # Version
    "payload_version": "1.0",
    "builder_version": "phase4-2026-06-13",
}
```

### 監査ログの活用例

```
Q: SKU「MARGIN-20260613-0001」の title がなぜこうなった？
A: audit_trail.title_template_used = "A"
   audit_trail.title_generation_reason = "standard_format"
   → Template A が使用されたことが明確

Q: Category「Camera Lenses」は誰が決めた？
A: audit_trail.category_mapped_from = "Camera Lenses"
   source_type = "ebay_listing"
   → Research 段階で既に「Camera Lenses」として入力
   → Phase 4 でそのまま使用

Q: Price が pending_review なのはなぜ？
A: validation_report.review_items = ["listing_price未決定"]
   → Phase 5 で price strategy module で決定待ち
```

---

## まとめ

Phase 4 で確定すること:

- ✅ ListingReadyRecord から eBay Payload への変換責務
- ✅ Layer 1-3 段階的な payload 準備設計
- ✅ title / description / category / condition / price / quantity / images の責務分離
- ✅ Readiness 判定（ready / pending_review / incomplete / rejected）
- ✅ Validation report + Audit trail の構造化
- ✅ 未確定情報の明示的な「review フラグ」による扱い

Phase 5 で実装すること:

- ❌ eBay API client 実装
- ❌ 認証トークン管理
- ❌ Price strategy module
- ❌ Category resolver（自動マッピング）
- ❌ Dry-run executor
- ❌ Live execution

Phase 4 の原則:

- Payload Builder は API client ではない
- 未確定情報を 黙って埋めない
- 追跡性と監査性を常に保持
- 公開文と内部メモを分離
- Reference data を無条件転記しない

**版**: 0.1  
**作成日**: 2026-06-13  
**ステータス**: 設計段階  
**次ステップ**: Phase 5 - eBay Executor 実装
'''

os.makedirs(f"{project_path}/docs", exist_ok=True)
with open(f"{project_path}/docs/PHASE4_EBAY_PAYLOAD_BUILDER.md", "w", encoding="utf-8") as f:
    f.write(phase4_main_doc)
print("✅ Created: docs/PHASE4_EBAY_PAYLOAD_BUILDER.md")

# ============================================================================
# 2. Create docs/EBAY_PAYLOAD_MODEL.md
# ============================================================================

ebay_payload_model_doc = r'''# MarginScout: eBay Payload Model

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
'''

with open(f"{project_path}/docs/EBAY_PAYLOAD_MODEL.md", "w", encoding="utf-8") as f:
    f.write(ebay_payload_model_doc)
print("✅ Created: docs/EBAY_PAYLOAD_MODEL.md")

# ============================================================================
# 3. Create examples/ebay_payload_sample.json
# ============================================================================

ebay_payload_sample = {
  "payloads": [
    {
      "candidate_id": "ms-res-20260613-0001",
      "sku": "MARGIN-20260613-0001",
      "payload": {
        "sku": "MARGIN-20260613-0001",
        "title": "Canon EF 50mm f/1.8 STM Lens - New",
        "description": "Professional quality lens. Excellent condition. Minimal use.\nBrand: Canon\nModel: EF50STM\n\n【注意】本出品は MarginScout により自動生成されました。",
        "category": "Camera Lenses",
        "condition": "new",
        "price": None,
        "quantity": 1,
        "images": [
          "data/images/MARGIN-20260613-0001/01.jpg",
          "data/images/MARGIN-20260613-0001/02.jpg",
          "data/images/MARGIN-20260613-0001/03.jpg"
        ],
        "item_specifics": {
          "Brand": "Canon",
          "Model": "EF50STM"
        }
      },
      "validation_report": {
        "readiness": "ready",
        "validation_result": {
          "passed": True,
          "errors": [],
          "warnings": []
        },
        "review_items": []
      },
      "audit_trail": {
        "candidate_id": "ms-res-20260613-0001",
        "sku": "MARGIN-20260613-0001",
        "source_url": "https://www.ebay.com/itm/324901234567",
        "source_type": "ebay_listing",
        "observed_price": 189.99,
        "observed_date": "2026-06-13T14:30:00Z",
        "payload_generation_timestamp": "2026-06-13T16:00:00Z",
        "title_template_used": "A",
        "condition_mapped_from": "new",
        "category_mapped_from": "Camera Lenses",
        "validation_status": "passed",
        "readiness_level": "ready"
      }
    },
    {
      "candidate_id": "ms-res-20260613-0002",
      "sku": "MARGIN-20260613-0002",
      "payload": {
        "sku": "MARGIN-20260613-0002",
        "title": "Nike Air Force 1 US9 - New",
        "description": "Authentic Nike Air Force 1. Size US9. New condition.\nBrand: Nike\nModel: AF1-US9\n\n【注意】本出品は MarginScout により自動生成されました。",
        "category": "Footwear",
        "condition": "new",
        "price": None,
        "quantity": 1,
        "images": [
          "data/images/MARGIN-20260613-0002/01.jpg",
          "data/images/MARGIN-20260613-0002/02.jpg"
        ],
        "item_specifics": {
          "Brand": "Nike",
          "Model": "AF1-US9"
        }
      },
      "validation_report": {
        "readiness": "ready",
        "validation_result": {
          "passed": True,
          "errors": [],
          "warnings": []
        },
        "review_items": []
      },
      "audit_trail": {
        "candidate_id": "ms-res-20260613-0002",
        "sku": "MARGIN-20260613-0002",
        "source_url": "https://www.ebay.com/itm/324901234568",
        "source_type": "ebay_listing",
        "observed_price": 110.0,
        "observed_date": "2026-06-13T14:35:00Z",
        "payload_generation_timestamp": "2026-06-13T16:05:00Z",
        "title_template_used": "A",
        "condition_mapped_from": "new",
        "category_mapped_from": "Footwear",
        "validation_status": "passed",
        "readiness_level": "ready"
      }
    },
    {
      "candidate_id": "ms-res-20260613-0003",
      "sku": "MARGIN-20260613-0003",
      "payload": {
        "sku": "MARGIN-20260613-0003",
        "title": "Sony WH-CH510 - New",
        "description": "Sony WH-CH510 headphones. New condition.\nBrand: Sony\nModel: WHCH510\n\n【注意】本出品は MarginScout により自動生成されました。",
        "category": "Audio Equipment",
        "condition": "new",
        "price": None,
        "quantity": 1,
        "images": [
          "data/images/MARGIN-20260613-0003/01.jpg"
        ],
        "item_specifics": {
          "Brand": "Sony",
          "Model": "WHCH510"
        }
      },
      "validation_report": {
        "readiness": "pending_review",
        "validation_result": {
          "passed": False,
          "errors": [],
          "warnings": [
            "Only 1 image. Recommend 3+ images for better sales."
          ]
        },
        "review_items": [
          "price未決定",
          "image数が少ない"
        ]
      },
      "audit_trail": {
        "candidate_id": "ms-res-20260613-0003",
        "sku": "MARGIN-20260613-0003",
        "source_url": "https://www.amazon.com/dp/B08GFZV8H3",
        "source_type": "amazon_listing",
        "observed_price": 49.99,
        "observed_date": "2026-06-13T14:40:00Z",
        "payload_generation_timestamp": "2026-06-13T16:10:00Z",
        "title_template_used": "C",
        "condition_mapped_from": "new",
        "category_mapped_from": "Audio Equipment",
        "validation_status": "passed_with_warnings",
        "readiness_level": "pending_review"
      }
    }
  ]
}

os.makedirs(f"{project_path}/examples", exist_ok=True)
with open(f"{project_path}/examples/ebay_payload_sample.json", "w", encoding="utf-8") as f:
    json.dump(ebay_payload_sample, f, indent=2, ensure_ascii=False)
print("✅ Created: examples/ebay_payload_sample.json")

# ============================================================================
# 4. Create examples/listing_to_payload_mapping.md
# ============================================================================

listing_to_payload_mapping = r'''# Listing → Payload マッピング対応表

目的: ListingReadyRecord と eBay Payload Input の対応を明確化

## 項目別マッピング

| Listing項目 | Payload項目 | 変換処理 | 説明 |
|---|---|---|---|
| candidate_id | audit_trail.candidate_id | そのまま | 監査用に保持 |
| sku | payload.sku | そのまま | 出品用SKU |
| product_name | payload.title の入力 | Template適用 | title生成の基盤 |
| category | payload.category + audit | Category mapper | 内部→eBay変換 |
| condition | payload.condition | Condition mapper | 正規化変換 |
| brand | item_specifics.Brand | Optional | title補助、item_specificsに |
| model_number | item_specifics.Model | Optional | title補助、item_specificsに |
| reference_price | audit_trail.observed_price | 監査用 | 参考値（出品価格ではない） |
| image_dir | payload.images | Directory→List | ローカルパス列挙 |
| image_count | payload.images 長 | Count | 画像数確認 |
| user_notes | payload.description の入力 | Sanitize + escape | 公開description構成 |
| user_tags | audit_trail.user_tags | 監査用 | 内部用タグ保持 |
| source_url | audit_trail.source_url | 監査用 | 参考価格出典 |
| source_type | audit_trail.source_type | 監査用 | データ取得元 |
| observed_date | audit_trail.observed_date | 監査用 | 観測タイムスタンプ |
| listing_status | (検証に使用) | - | readiness判定に使用 |
| validation_status | validation_report | - | payload readiness決定 |
| completeness_status | validation_report | - | incomplete判定に使用 |

## 変換ルール詳細

### title 変換

```
入力: product_name = "Canon EF 50mm f/1.8 STM"
      brand = "Canon"
      condition = "new"

ルール: Template A = "{BRAND} {PRODUCT_NAME} - {CONDITION}"

出力: title = "Canon EF 50mm f/1.8 STM - new"
      (80文字以下に制限)
```

### description 変換

```
入力: product_name, brand, condition, user_notes

ルール: 
  1. Header = "{PRODUCT_NAME}\n{BRAND} | {CONDITION}"
  2. Body = sanitize_html(user_notes)
  3. Footer = "【注意】本出品は MarginScout により..."

出力: description = header + body + footer
      (HTML escape済み)
```

### category 変換

```
入力: category = "Camera Lenses"

ルール: CATEGORY_MAP["Camera Lenses"] = {
          "ebay_category_id": "625",
          "confidence": "high"
        }

出力: payload.category = "Camera Lenses"
      (ebay_category_id は Phase 5 で決定)
```

### condition 変換

```
入力: condition = "new"

ルール: CONDITION_MAP["new"] = "new"

出力: payload.condition = "new"
```

### images 変換

```
入力: image_dir = "data/images/MARGIN-20260613-0001/"
      image_count = 3

ルール: 
  1. ディレクトリ走査
  2. ゼロパディング順序 (01.jpg, 02.jpg, ...)
  3. 完全パスで返す

出力: images = [
        "data/images/MARGIN-20260613-0001/01.jpg",
        "data/images/MARGIN-20260613-0001/02.jpg",
        "data/images/MARGIN-20260613-0001/03.jpg"
      ]
```

## Payload で追加・変更される項目

| 項目 | Listing | Payload | 説明 |
|---|---|---|---|
| price | None | None | Phase 5で決定 |
| quantity | 1 | 1 | default値で固定 |
| item_specifics | - | {Brand, Model} | 新規追加（Listing には非含） |
'''

with open(f"{project_path}/examples/listing_to_payload_mapping.md", "w", encoding="utf-8") as f:
    f.write(listing_to_payload_mapping)
print("✅ Created: examples/listing_to_payload_mapping.md")

# ============================================================================
# 5. Create src/payload_builder skeleton
# ============================================================================

os.makedirs(f"{project_path}/src/payload_builder", exist_ok=True)

# __init__.py
init_content = r'''"""
MarginScout Payload Builder Package

ListingReadyRecord → eBay Payload Input への変換ロジック
"""

from .payload_record import (
    PayloadPreparationRecord,
    ValidatedPayloadRecord,
)
from .ebay_payload_builder import EBayPayloadBuilder
from .title_builder import TitleBuilder
from .description_builder import DescriptionBuilder
from .image_mapper import ImageMapper
from .payload_validator import PayloadValidator

__all__ = [
    'PayloadPreparationRecord',
    'ValidatedPayloadRecord',
    'EBayPayloadBuilder',
    'TitleBuilder',
    'DescriptionBuilder',
    'ImageMapper',
    'PayloadValidator',
]
'''

with open(f"{project_path}/src/payload_builder/__init__.py", "w", encoding="utf-8") as f:
    f.write(init_content)
print("✅ Created: src/payload_builder/__init__.py")

# payload_record.py
payload_record_content = r'''"""
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
'''

with open(f"{project_path}/src/payload_builder/payload_record.py", "w", encoding="utf-8") as f:
    f.write(payload_record_content)
print("✅ Created: src/payload_builder/payload_record.py")

# title_builder.py
title_builder_content = r'''"""
Title Builder

ListingReadyRecord から eBay payload の title を生成
"""

from typing import Optional

class TitleBuilder:
    """
    title 生成ロジック
    
    Template A / B / C をサポート
    """
    
    MAX_TITLE_LENGTH = 80
    
    TEMPLATES = {
        "A": "{brand} {product_name} - {condition}",
        "B": "{brand} {model} {product_name} - {condition}",
        "C": "{product_name}",
    }
    
    def __init__(self, template: str = "A"):
        self.template = template
        
    def build_title(
        self,
        product_name: str,
        brand: Optional[str] = None,
        model: Optional[str] = None,
        condition: str = "new"
    ) -> tuple[str, list]:
        """
        title を生成
        
        Returns:
            (title, warnings)
        """
        # TODO: Template 適用ロジック実装
        # TODO: 80文字制限処理
        # TODO: 不要語削除・正規化
        raise NotImplementedError("Title builder implementation pending Phase 4")
'''

with open(f"{project_path}/src/payload_builder/title_builder.py", "w", encoding="utf-8") as f:
    f.write(title_builder_content)
print("✅ Created: src/payload_builder/title_builder.py")

# description_builder.py
description_builder_content = r'''"""
Description Builder

ListingReadyRecord から eBay payload の description を生成
"""

from typing import Optional

class DescriptionBuilder:
    """
    description 生成ロジック
    
    user_notes を HTML escape してから description に含める
    """
    
    DESCRIPTION_TEMPLATE = """
{product_name}
{brand} | {model} | {condition}

商品説明：
{user_notes_formatted}

【注意】
本出品は MarginScout により自動生成されました。
ご不明な点はお問い合わせください。
"""

    def build_description(
        self,
        product_name: str,
        brand: Optional[str] = None,
        model: Optional[str] = None,
        condition: str = "new",
        user_notes: Optional[str] = None
    ) -> tuple[str, list]:
        """
        description を生成
        
        Returns:
            (description, warnings)
        """
        # TODO: Template 適用ロジック実装
        # TODO: HTML escape / sanitize
        # TODO: 長さ制限処理
        raise NotImplementedError("Description builder implementation pending Phase 4")
        
    def sanitize_html(self, text: str) -> str:
        """
        HTML 特殊文字を escape
        """
        # TODO: <, >, &, " などを escape
        raise NotImplementedError("HTML sanitize implementation pending")
'''

with open(f"{project_path}/src/payload_builder/description_builder.py", "w", encoding="utf-8") as f:
    f.write(description_builder_content)
print("✅ Created: src/payload_builder/description_builder.py")

# image_mapper.py
image_mapper_content = r'''"""
Image Mapper

ローカル画像ディレクトリを eBay payload 用の image list に変換
"""

from typing import List, Dict

class ImageMapper:
    """
    image_dir → image_list への変換
    
    data/images/{SKU}/ をスキャンして、
    01.jpg, 02.jpg, ... を順序付きで返す
    """
    
    def __init__(self, base_image_dir: str = "data/images"):
        self.base_image_dir = base_image_dir
        
    def map_images(
        self,
        sku: str,
        image_count: int
    ) -> tuple[List[str], Dict]:
        """
        SKU からローカル画像 list を生成
        
        Returns:
            (image_list, metadata)
        """
        # TODO: ディレクトリスキャンロジック実装
        # TODO: ゼロパディング順序確認
        # TODO: 画像ファイル存在確認
        # TODO: 拡張子チェック (.jpg)
        raise NotImplementedError("Image mapper implementation pending Phase 4")
        
    def validate_images(
        self,
        image_dir: str,
        image_count: int
    ) -> tuple[bool, List[str]]:
        """
        画像ディレクトリ・ファイル検証
        
        Returns:
            (valid, warnings)
        """
        # TODO: ディレクトリ存在確認
        # TODO: ファイル数確認
        # TODO: ファイル形式確認
        raise NotImplementedError("Image validation implementation pending Phase 4")
'''

with open(f"{project_path}/src/payload_builder/image_mapper.py", "w", encoding="utf-8") as f:
    f.write(image_mapper_content)
print("✅ Created: src/payload_builder/image_mapper.py")

# payload_validator.py
payload_validator_content = r'''"""
Payload Validator

eBay Payload のバリデーションと readiness 判定
"""

from typing import Tuple, List, Dict
from .payload_record import ValidatedPayloadRecord

class PayloadValidator:
    """
    Payload readiness 検証
    
    ready / pending_review / incomplete / rejected を判定
    """
    
    def __init__(self):
        pass
        
    def judge_readiness(
        self,
        record: ValidatedPayloadRecord
    ) -> Tuple[str, str, List[str]]:
        """
        Payload 化可能か判定
        
        Returns:
            (readiness_level, reason, review_items)
            - ready: 出品可能
            - pending_review: レビュー待ち
            - incomplete: 入力不足
            - rejected: 不正・除外
        """
        # TODO: Hard error チェック
        # TODO: Optional フィールドチェック
        # TODO: Review 項目列挙
        raise NotImplementedError("Readiness judge implementation pending Phase 4")
        
    def validate_title(self, title: str) -> Tuple[bool, List[str]]:
        """
        title バリデーション
        """
        # TODO: 長さチェック (80文字以下)
        # TODO: 空チェック
        raise NotImplementedError("Title validation implementation pending")
        
    def validate_description(self, description: str) -> Tuple[bool, List[str]]:
        """
        description バリデーション
        """
        # TODO: 空チェック
        # TODO: 危険なHTML タグチェック
        raise NotImplementedError("Description validation implementation pending")
        
    def validate_images(self, images: List[str]) -> Tuple[bool, List[str]]:
        """
        images バリデーション
        """
        # TODO: リスト空チェック
        # TODO: ファイル存在確認
        raise NotImplementedError("Images validation implementation pending")
'''

with open(f"{project_path}/src/payload_builder/payload_validator.py", "w", encoding="utf-8") as f:
    f.write(payload_validator_content)
print("✅ Created: src/payload_builder/payload_validator.py")

# ebay_payload_builder.py
ebay_payload_builder_content = r'''"""
eBay Payload Builder

ListingReadyRecord → eBay Payload への変換エンジン
"""

from typing import Tuple, Dict, Optional
from .payload_record import ValidatedPayloadRecord
from .title_builder import TitleBuilder
from .description_builder import DescriptionBuilder
from .image_mapper import ImageMapper
from .payload_validator import PayloadValidator

class EBayPayloadBuilder:
    """
    eBay Payload Builder
    
    Phase 4 の中核エンジン
    ListingReadyRecord を eBay Payload に変換
    """
    
    def __init__(self):
        self.title_builder = TitleBuilder()
        self.description_builder = DescriptionBuilder()
        self.image_mapper = ImageMapper()
        self.validator = PayloadValidator()
        
    def build_payload(
        self,
        listing_record: Dict
    ) -> Tuple[Dict, Dict, Dict]:
        """
        Payload を生成
        
        Args:
            listing_record: ListingReadyRecord (dict form)
        
        Returns:
            (ebay_payload, validation_report, audit_trail)
        """
        # TODO: Step 1: Readiness 再検証
        # TODO: Step 2: Title/Description 整形
        # TODO: Step 3: Category/Condition 正規化
        # TODO: Step 4: Price/Quantity validation
        # TODO: Step 5: Images マッピング
        # TODO: Step 6: Payload 生成
        # TODO: Step 7: Validation report 作成
        # TODO: Step 8: Audit trail 生成
        raise NotImplementedError("Payload builder implementation pending Phase 4")
        
    def generate_title(
        self,
        product_name: str,
        brand: Optional[str] = None,
        model: Optional[str] = None,
        condition: str = "new"
    ) -> Tuple[str, list]:
        """
        Title を生成
        """
        return self.title_builder.build_title(product_name, brand, model, condition)
        
    def generate_description(
        self,
        product_name: str,
        brand: Optional[str] = None,
        model: Optional[str] = None,
        condition: str = "new",
        user_notes: Optional[str] = None
    ) -> Tuple[str, list]:
        """
        Description を生成
        """
        return self.description_builder.build_description(
            product_name, brand, model, condition, user_notes
        )
        
    def map_images(self, sku: str, image_count: int) -> Tuple[list, Dict]:
        """
        Images を map
        """
        return self.image_mapper.map_images(sku, image_count)
'''

with open(f"{project_path}/src/payload_builder/ebay_payload_builder.py", "w", encoding="utf-8") as f:
    f.write(ebay_payload_builder_content)
print("✅ Created: src/payload_builder/ebay_payload_builder.py")

# ============================================================================
# 6. Create PHASE4_COMPLETION_REPORT.json
# ============================================================================

phase4_report = {
    "timestamp": timestamp,
    "phase": "Phase 4: eBay Payload Builder Design",
    "status": "COMPLETED",
    "documents_created": [
        "docs/PHASE4_EBAY_PAYLOAD_BUILDER.md",
        "docs/EBAY_PAYLOAD_MODEL.md",
        "examples/ebay_payload_sample.json",
        "examples/listing_to_payload_mapping.md",
        "src/payload_builder/__init__.py",
        "src/payload_builder/payload_record.py",
        "src/payload_builder/title_builder.py",
        "src/payload_builder/description_builder.py",
        "src/payload_builder/image_mapper.py",
        "src/payload_builder/payload_validator.py",
        "src/payload_builder/ebay_payload_builder.py",
    ],
    "key_design_decisions": {
        "payload_builder_role": "Data preparation & validation - NOT API client",
        "title_strategy": "Template-based generation (A/B/C templates, 80-char limit)",
        "description_strategy": "HTML-escaped user notes + standard template",
        "category_strategy": "Internal normalization first, eBay mapping in Phase 5",
        "condition_strategy": "new/used/refurbished normalization",
        "price_strategy": "reference_price is observation only, listing_price decided in Phase 5",
        "image_strategy": "SKU-based directory → sorted file list",
        "readiness_levels": "ready / pending_review / incomplete / rejected",
    },
    "data_layers": {
        "layer_1": "Payload Preparation Record (draft title/desc, normalized category/condition)",
        "layer_2": "Validated Payload Record (finalized title/desc, readiness judgment)",
        "layer_3": "Final eBay Payload Input Record (eBay API format JSON)",
        "audit": "Separate audit trail with full traceability",
    },
    "validation_levels": {
        "ready": "All required fields confirmed - payload ready for Phase 5",
        "pending_review": "Missing optional fields or price not decided - user review needed",
        "incomplete": "Required fields missing - cannot proceed",
        "rejected": "Invalid data or explicitly excluded - skip",
    },
    "next_phase": "Phase 5: eBay Executor & Dry-Run Implementation",
    "next_phase_scope": [
        "eBay API client implementation",
        "Authentication token management",
        "Price strategy module",
        "Category resolver (automated mapping)",
        "Dry-run executor with validation",
        "Live execution handler",
        "Audit logging integration",
    ],
    "not_in_scope_phase4": [
        "eBay API implementation",
        "Authentication/token management",
        "Live execution"
    ]
}

with open(f"{project_path}/PHASE4_COMPLETION_REPORT.json", "w", encoding="utf-8") as f:
    json.dump(phase4_report, f, indent=2, ensure_ascii=False)
print("✅ Created: PHASE4_COMPLETION_REPORT.json")

# ============================================================================
# 7. Update README.md
# ============================================================================

readme_phase4_update = """

---

## 📋 Phase 4: eBay Payload Builder 設計 (完了)

**ステータス**: 設計完了  
**完了日**: 2026-06-13

### 成果物

✅ docs/PHASE4_EBAY_PAYLOAD_BUILDER.md — Payload Builder 全体設計  
✅ docs/EBAY_PAYLOAD_MODEL.md — Payload 内部モデル定義  
✅ examples/ebay_payload_sample.json — eBay ペイロード サンプル  
✅ examples/listing_to_payload_mapping.md — Listing→Payload 列マッピング  
✅ src/payload_builder/ — Pythonスケルトン (title, description, image, builder)  

### 設計要点

**責務**:
- Payload Builder は API Client ではなく、データ準備に特化
- Title (80文字制限, テンプレートA/B/C) 
- Description (User Notes 統合, サニタイズ)
- Category, Condition 正規化 (内部表現 → eBay表現準備)
- Readiness 判定 (ready / pending_review / incomplete)
- 監査追跡情報 (Audit Trail) の確保
"""

readme_path = f"{project_path}/README.md"
try:
    with open(readme_path, "r", encoding="utf-8") as f:
        readme_content = f.read()
    readme_content += readme_phase4_update
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme_content)
    print("✅ Updated: README.md (Phase 4 status added)")
except Exception as e:
    print(f"⚠️ README.md update failed: {e}")

# ============================================================================
# 8. Final Summary
# ============================================================================

print("\n" + "=" * 70)
print("✨ Phase 4: eBay Payload Builder Design - COMPLETED")
print("=" * 70)
print("")
print("📄 Created Documents:")
print("  • docs/PHASE4_EBAY_PAYLOAD_BUILDER.md")
print("  • docs/EBAY_PAYLOAD_MODEL.md")
print("  • examples/ebay_payload_sample.json")
print("  • examples/listing_to_payload_mapping.md")
print("  • src/payload_builder/ (Pythonスケルトン)")
print("")
print("🎯 Key Design Outcomes:")
print("  ✓ Payload Builder 責務の明確化 (API実行分離)")
print("  ✓ Title, Description のテンプレート化戦略")
print("  ✓ Category, Condition 正規化設計")
print("  ✓ Readiness 判定と Review Required フラグの導入")
print("  ✓ 監査用 Audit Trail 情報の分離")
print("")
print("🚀 Next Phase: Phase 5 - eBay Executor Implementation")
print("=" * 70)

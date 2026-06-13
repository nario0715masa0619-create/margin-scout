# MarginScout Phase 4: eBay Payload Builder 設計

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

# MarginScout Phase 3: CSVデータ連携設計

**作成日**: 2026-06-13  
**フェーズ**: Phase 3 - CSVデータ連携設計  
**ステータス**: 設計段階  
**前提**: Phase 2「リサーチワークフロー設計」完了

---

## 目次

1. [概要](#概要)
2. [CSV連携の全体像](#csv連携の全体像)
3. [責務分離の原則](#責務分離の原則)
4. [CSV入力仕様](#csv入力仕様)
5. [データ層の段階化](#データ層の段階化)
6. [必須項目・任意項目・補完項目の分類](#必須項目任意項目補完項目の分類)
7. [SKU戦略](#sku戦略)
8. [画像マッピング戦略](#画像マッピング戦略)
9. [バリデーション戦略](#バリデーション戦略)
10. [Research CSV と Listing CSV の関係](#research-csv-と-listing-csv-の関係)
11. [eBay Payload への橋渡し](#ebay-payload-への橋渡し)
12. [監査・追跡設計](#監査追跡設計)

---

## 概要

Phase 3 の目的は、Phase 2 で定義した「**リサーチ候補 CSV**」を、「**出品準備用 CSV**」へ安全に変換し、最終的に eBay 出品ペイロードへ接続できるようにすることです。

**設計の要点**:

- Research CSV と Listing CSV を明確に分離
- 責務の境界を明確化
- 段階的な変換レイヤーを設計
- 追跡性と監査ログの確保
- ユーザーレビュー・ポイントの明記

---

## CSV連携の全体像

### ワークフロー図

```
┌────────────────────────────────────────────────────────────┐
│ Phase 2: Research Workflow (完了)                            │
│ 複数ソース → 正規化 → 候補構築 → ユーザー確認 → CSV出力       │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ▼ research_sample.csv (15列: candidate_id, product_name, 価格, ...)
      ┌──────────────┴──────────────┐
      │                             │
      ▼ 【Phase 3】                 ▼ 【Phase 3】
  (本ドキュメント)                 (本ドキュメント)

CSV 検証 & 正規化
├─ 必須列の存在確認
├─ 空値チェック
├─ 型チェック
└─ 値域チェック
      │
      ▼ Normalized Research Record (研究結果を正規化)
      │
      ▼ Listing Preparation Record (出品準備層へ変換)
├─ SKU 付与
├─ eBay カテゴリ関連付け
├─ 画像ディレクトリ解決
└─ 欠損補完戦略の適用
      │
      ▼ Listing-Ready Record (出品可能な状態)
├─ 必須項目 100% 充足
├─ バリデーション完了
├─ 監査情報残存
└─ 追跡性確保
      │
      ▼ transformed_listing.csv (出品用CSV: candidate_id 保持、SKU追加、...)
      │
      ▼ 【Phase 4 以降】 eBay Payload Builder → eBay API → 実出品
                            (本フェーズでは未実装)
```

### 段階的な処理フロー

| Step | 入力 | 処理 | 出力 | 責務 |
|------|------|------|------|------|
| 1 | research_sample.csv | CSV読込 | Raw CSV rows | CSV I/O |
| 2 | Raw rows | 構造検証 | Validation report | Validator |
| 3 | Validated rows | 正規化 | Normalized records | Mapper |
| 4 | Normalized | SKU付与 | SKU assigned records | SKU Strategy |
| 5 | SKU assigned | 画像解決 | Image path resolved | Image Mapper |
| 6 | Image resolved | 補完判定 | Completion status | Completion Logic |
| 7 | Completed | 最終チェック | Listing-ready flag | Final Validator |
| 8 | Listing-ready | CSV生成 | transformed_listing.csv | CSV Exporter |

---

## 責務分離の原則

### MarginScout リサーチ層の責務 (Phase 2)

- ✅ 複数ソースから候補収集
- ✅ 形式正規化
- ✅ メタデータ抽出
- ✅ ユーザー補完・判定
- ✅ Research CSV 出力

**責務終了点**: Research CSV ファイル生成

### MarginScout 出品準備層の責務 (Phase 3 - 本フェーズ)

- ✅ Research CSV 取込
- ✅ CSV 構造検証
- ✅ SKU 戦略適用
- ✅ 画像ディレクトリ解決
- ✅ 欠損データ補完判定
- ✅ Listing-ready 状態判定
- ✅ Transformed CSV 出力

**責務終了点**: Listing-ready データ確定

### 別システムの責務 (Phase 4 以降)

- ❌ eBay API 連携
- ❌ 実出品実行
- ❌ 出品後販売追跡
- ❌ 在庫管理

---

## CSV入力仕様

### Research CSV (入力) - Phase 2 から受け取るもの

**ファイル名**: `research_sample.csv`

**エンコード**: UTF-8

**カラム数**: 15列

**カラム定義**:

| # | Column Name | Type | 必須 | 説明 |
|----|------------|------|------|------|
| 1 | candidate_id | String | ✅ | リサーチ候補ID (例: ms-res-20260613-0001) |
| 2 | product_name | String | ✅ | 商品名 |
| 3 | reference_price | Decimal | ✅ | 参考価格 |
| 4 | currency | String | ✅ | 通貨コード (USD, JPY, ...) |
| 5 | brand | String | ✗ | ブランド名 |
| 6 | model_number | String | ✗ | 型番 |
| 7 | category | String | ✗ | 商品カテゴリ |
| 8 | product_url | String | ✅ | 参考価格観測元 URL |
| 9 | source_type | String | ✅ | ソース種別 (ebay_listing, amazon_listing, ...) |
| 10 | observed_date | String (ISO 8601) | ✅ | 観測日時 |
| 11 | condition | String | ✗ | 商品状態 (new, used, refurbished, ...) |
| 12 | user_notes | String | ✗ | ユーザーメモ |
| 13 | user_tags | String (semicolon-separated) | ✗ | ユーザータグ |
| 14 | judgement_flag | String | ✗ | 判定フラグ (promising, hold, rejected, needs_review) |
| 15 | research_status | String | ✅ | ステータス (draft, under_review, confirmed, excluded) |

**制約**:

- 空行は不可
- BOM なし UTF-8
- CRLF または LF
- 日付は ISO 8601 形式
- 小数は小数第2位まで

---

## データ層の段階化

### Layer 構造 (Phase 3)

```
【Layer 0】Raw CSV Row
      ↓
【Layer 1】Validated & Normalized Record
  型チェック完了
  値域チェック完了
  必須フィールド確認
      ↓
【Layer 2】Listing Preparation Record
  SKU が付与された
  画像ディレクトリが解決された
  欠損値が「pending」か「補完可能」かが判定されている
      ↓
【Layer 3】Listing-Ready Record
  すべての必須項目が充足
  バリデーション 100% 完了
  監査情報が残存
      ↓
【Layer 4】Transformed Listing CSV
  出品準備用CSVファイル
  candidate_id 保持（追跡性確保）
  SKU 追加
  画像参照解決済み
```

### 各層の責務

#### Layer 1: Validated & Normalized Record

```python
{
  "candidate_id": "ms-res-20260613-0001",  # 元ID保持
  "product_name": "Canon EF 50mm f/1.8 STM",
  "reference_price": 189.99,  # 小数第2位
  "currency": "USD",
  "brand": "Canon",
  "model_number": "EF50STM",
  "category": "Camera Lenses",
  "product_url": "https://www.ebay.com/itm/...",
  "source_type": "ebay_listing",
  "observed_date": "2026-06-13T14:30:00Z",  # ISO 8601
  "condition": "new",
  "user_notes": "状態良好・レンズクリア",
  "user_tags": ["high-demand", "checked"],
  "judgement_flag": "promising",
  "research_status": "confirmed",
  
  # Layer 1 追加フィールド
  "validation_status": "passed",
  "validation_timestamp": "2026-06-13T15:00:00Z",
}
```

#### Layer 2: Listing Preparation Record

```python
{
  # Layer 1 をすべて継承
  ...
  
  # Layer 2 追加フィールド
  "sku": "MARGIN-20260613-0001",  # 新規採番
  "sku_strategy_applied": "auto_generation",
  "image_dir": "data/images/MARGIN-20260613-0001/",
  "image_dir_exists": True,
  "image_count": 3,
  "image_validation": "passed",
  
  # 欠損補完の状態
  "completeness_status": "ready",  # ready / pending_review / incomplete
  "missing_fields": [],
  "pending_fields": [],
}
```

#### Layer 3: Listing-Ready Record

```python
{
  # Layer 2 をすべて継承
  ...
  
  # Layer 3 判定フィールド
  "listing_ready": True,
  "ready_timestamp": "2026-06-13T15:05:00Z",
  
  # eBay 関連フィールド（未実装だが構造定義）
  "ebay_category_id": None,  # Phase 4 で設定
  "ebay_title": None,
  "ebay_description_template": None,
  
  # 監査フィールド
  "audit_trail": {
    "created_from_research_id": "ms-res-20260613-0001",
    "research_source_url": "https://www.ebay.com/itm/...",
    "transformation_timestamp": "2026-06-13T15:05:00Z",
    "user_notes_preserved": "状態良好・レンズクリア",
  }
}
```

---

## 必須項目・任意項目・補完項目の分類

### 分類マトリックス

| Item | 項目 | Research CSV での扱い | Listing Preparation での扱い | 分類 | 欠損時の対応 |
|---|---|---|---|---|---|
| 1 | candidate_id | ✅ 必須 | ✅ 必須 (追跡用) | 必須 | Hard Error |
| 2 | product_name | ✅ 必須 | ✅ 必須 | 必須 | Hard Error |
| 3 | reference_price | ✅ 必須 | △ 参考値 | 参考 | Warning |
| 4 | currency | ✅ 必須 | △ eBay連携で変換 | 参考 | Warning |
| 5 | brand | ✗ 任意 | △ eBay title に使用 | 補完 | Pending Review |
| 6 | model_number | ✗ 任意 | △ eBay title に使用 | 補完 | Pending Review |
| 7 | category | ✗ 任意 | ✅ eBay category マッピング必須 | 補完 | Hard Error |
| 8 | product_url | ✅ 必須 | ✅ 監査・追跡用 | 必須 | Hard Error |
| 9 | source_type | ✅ 必須 | ✅ 監査用 | 監査 | Soft Error |
| 10 | observed_date | ✅ 必須 | ✅ 監査用 | 監査 | Soft Error |
| 11 | condition | ✗ 任意 | ✅ eBay condition マッピング | 必須 | Hard Error |
| 12 | user_notes | ✗ 任意 | △ listing note に含める | 任意 | Skip |
| 13 | user_tags | ✗ 任意 | △ 内部タグとして保持 | 任意 | Skip |
| 14 | judgement_flag | ✗ 任意 | △ 出品判定補助 | 任意 | Skip |
| 15 | research_status | ✅ 必須 | ✅ フィルタ用 (confirmed のみ) | 必須 | Skip (除外) |

### 分類の説明

- **必須項目 (Hard Error - 欠けると出品不可)**
  - candidate_id: 追跡性の根本
  - product_name: eBay title の基盤
  - category: eBay category マッピングが必須
  - product_url: 参考価格出典の記録（監査）
  - condition: eBay の条件設定に必須

- **参考項目 (Warning - 欠けても出品可能だが通知)**
  - reference_price: 参考値、実eBay価格は別判定
  - currency: 通貨変換で対応

- **補完項目 (Pending Review - 欠けても補完戦略で対応)**
  - brand: 商品名から抽出可能性あり、UI 補完も可能
  - model_number: 商品名から抽出、ユーザーUI 補完

- **任意項目 (Skip - 欠けても問題なし)**
  - user_notes: 参考情報、欠けても OK
  - user_tags: 内部用、欠けても OK
  - judgement_flag: 判定補助、欠けても OK

- **監査項目 (Soft Error - 欠けるとログ警告だが続行)**
  - source_type: 監査追跡用
  - observed_date: 監査タイムスタンプ

---

## SKU戦略

### 基本方針

Research と Listing では SKU を明確に分離する

```
Research 層: candidate_id (ms-res-20260613-0001)
   ↓
   ├─ 追跡・監査用に保持
   │
Listing 層: SKU (MARGIN-20260613-0001)
   ↓
   ├─ eBay 出品用に新規採番
   ├─ data/images/{SKU}/ のフォルダとリンク
   └─ Phase 4 で payload builder へ渡す
```

### SKU 採番戦略

**Strategy A: 自動採番 (推奨)**

```
フォーマット: MARGIN-{YYYYMMDD}-{4桁連番}

例:
- MARGIN-20260613-0001
- MARGIN-20260613-0002
- MARGIN-20260613-0003

利点:
- 簡潔
- ファイルシステムフレンドリー
- ERE Phase2 資産の data/images/{SKU}/ と整合
- 自動採番なので人的ミスなし
```

**Strategy B: Candidate ID ベース (代替案)**

```
フォーマット: ms-res-{candidate_id}

例:
- ms-res-ms-res-20260613-0001

短所:
- 長すぎる
- 重複の可能性あり (candidate_id 生成ルール次第)

非推奨
```

### SKU 付与タイミング

```
Research CSV 取込
  ↓
CSV バリデーション
  ↓
★ SKU 自動採番 (ここで付与)
  ↓
画像ディレクトリ解決
  ↓
Listing-ready チェック
```

### 追跡性の確保

SKU 付与後も、元の candidate_id を保持:

```json
{
  "candidate_id": "ms-res-20260613-0001",  # 元ID (必ず保持)
  "sku": "MARGIN-20260613-0001",           # 新規SKU
  "audit_trail": {
    "research_id": "ms-res-20260613-0001",
    "listing_sku": "MARGIN-20260613-0001",
    "mapping_timestamp": "2026-06-13T15:00:00Z"
  }
}
```

### 画像ディレクトリとのリンク

```
ローカル画像構造 (ERE Phase2 流用):

data/images/
  ├─ MARGIN-20260613-0001/
  │   ├─ 01.jpg
  │   ├─ 02.jpg
  │   └─ 03.jpg
  ├─ MARGIN-20260613-0002/
  │   ├─ 01.jpg
  │   └─ 02.jpg
  ...

Listing-ready record では:

{
  "sku": "MARGIN-20260613-0001",
  "image_dir": "data/images/MARGIN-20260613-0001/",
  "image_count": 3,
  "image_files": ["01.jpg", "02.jpg", "03.jpg"]
}
```

---

## 画像マッピング戦略

### 基本方針

画像は CSV に含めず、SKU ベースのディレクトリ解決に統一

```
Research CSV: 画像列なし
  ↓
Listing Preparation: SKU → image_dir 解決
  ↓
Listing-ready: image_count, image_files 確認
  ↓
Phase 4: Image Upload (未実装)
```

### ディレクトリ構造

```
推奨ディレクトリ構造:

data/
  └─ images/
      └─ {SKU}/
          ├─ 01.jpg
          ├─ 02.jpg
          ├─ 03.jpg
          ... (最大99まで対応可能)

命名規則:
- ゼロパディング: 01, 02, ... , 99
- 拡張子: .jpg (将来 .png 対応予定)
- 順序: 01 から 99 の番号順で自動並び
```

### 画像検証ルール

| ルール | 判定 | 対応 |
|---|---|---|
| 画像ディレクトリが存在 | ✅ | Continue |
| 画像ディレクトリが存在しない | ❌ | Pending Review (ユーザーが配置待ち) |
| 画像が0枚 | ⚠️ | Warning + Pending Review |
| 画像が1枚以上 | ✅ | Ready |
| ファイル形式不正 | ❌ | Hard Error |
| ファイルサイズ異常 (5MB 超過など) | ⚠️ | Warning |

### Phase 3 での扱い

Phase 3 では **画像の存在確認と metadata 記録** までとする。
画像の最適化・加工は Phase 4 以降。

```json
# Phase 3 の画像レコード

{
  "sku": "MARGIN-20260613-0001",
  "image_dir": "data/images/MARGIN-20260613-0001/",
  "image_dir_exists": True,
  "image_count": 3,
  "image_files": [
    {
      "filename": "01.jpg",
      "exists": True,
      "size": 245632,  # bytes
      "validation": "passed"
    },
    {
      "filename": "02.jpg",
      "exists": True,
      "size": 312805,
      "validation": "passed"
    },
    {
      "filename": "03.jpg",
      "exists": True,
      "size": 198456,
      "validation": "passed"
    }
  ],
  "image_validation_status": "ready"
}
```

---

## バリデーション戦略

### バリデーションレベルの定義

**Hard Error (処理停止)**
条件不充足で出品不可。該当行をスキップ、エラーログ出力。

```
- candidate_id が空
- product_name が空
- product_url が無効 (URL形式でない)
- reference_price が負数
- currency が未知のコード
- research_status != "confirmed"
```

**Soft Warning (処理続行、通知)**
欠損があるが処理は続行。ユーザー確認推奨。

```
- brand が空 → "要確認: ブランド名なし" と記録
- condition が空 → デフォルト値を提案
- category が空 → Pending Review マーク
```

**Pending Review (処理続行、ユーザー確認待ち)**
重要な欠損だが、UI 補完の可能性あり。

```
- brand 不在 → ユーザーが手動入力可能
- model_number 不在 → ユーザーが手動入力可能
- 画像ディレクトリ不在 → ユーザーが後で配置可能
```

**Skip (その行をスキップ)**
該当行の処理をスキップ。理由をログ。

```
- research_status = "excluded" → "リサーチで除外済み" と記録、行スキップ
- research_status = "draft" → "確定前" と記録、行スキップ
```

### バリデーション実装ロードマップ

```python
class CSVValidator:
    def validate_row(row):
        # Step 1: 必須フィールド
        if not row.get("candidate_id"):
            return HardError("candidate_id required")
        
        # Step 2: research_status フィルタ
        if row.get("research_status") != "confirmed":
            return Skip("research_status is not confirmed")
        
        # Step 3: URL バリデーション
        if not is_valid_url(row.get("product_url")):
            return HardError("product_url invalid")
        
        # Step 4: 数値バリデーション
        if not is_valid_decimal(row.get("reference_price")):
            return SoftWarning("reference_price invalid format")
        
        # Step 5: Soft バリデーション
        warnings = []
        if not row.get("brand"):
            warnings.append(SoftWarning("brand empty"))
        if not row.get("condition"):
            warnings.append(SoftWarning("condition empty"))
        
        return ValidationResult(
            status="passed",
            warnings=warnings,
            pending_review=[]
        )
```

---

## Research CSV と Listing CSV の関係

**採用方針**: B (中間変換ステップを設ける)

**理由**:
- **責務明確化**: research CSV はリサーチ専用、listing CSV は出品準備専用
- **変更耐性**: 今後ソースが増えても listing CSV 形式は安定
- **追跡性**: 元データ (research) が常に参照可能
- **ユーザーレビュー**: 変換ポイントが明確 → レビュー容易

### 関係図

```
【Research CSV】(Phase 2 出力)
  research_sample.csv
  ├─ candidate_id (ms-res-20260613-0001)
  ├─ product_name
  ├─ reference_price
  ├─ user_notes (リサーチ時メモ)
  ├─ user_tags (リサーチ時タグ)
  └─ ... (15列)

        ↓ (Transformation by Phase 3)
        
【Listing CSV】(Phase 3 出力)
  transformed_listing.csv
  ├─ candidate_id (元追跡用)
  ├─ sku (新規付与)
  ├─ product_name
  ├─ reference_price
  ├─ brand (未補完時は空)
  ├─ model_number (未補完時は空)
  ├─ category (未補完時は空)
  ├─ image_dir (SKU から自動解決)
  ├─ image_count
  ├─ user_notes (参考として保持)
  ├─ listing_status (ready / pending_review / incomplete)
  ├─ source_url (監査用)
  └─ ... (追加項目)

        ↓ (To be handed to Phase 4)
        
【Payload Builder】(Phase 4 以降)
  - eBay category ID マッピング
  - eBay title 生成
  - eBay description テンプレート適用
  - Price & Quantity 設定
  - API call
```

### 変換責務

```python
class ResearchToListingTransformer:
    
    def transform(research_row):
        """
        Research row → Listing row
        """
        # Step 1: 検証
        validation = validate(research_row)
        if validation.is_hard_error():
            return SkipRow(validation.error_message)
        
        # Step 2: SKU 付与
        sku = generate_sku()  # MARGIN-20260613-0001
        
        # Step 3: 画像解決
        image_dir = resolve_image_dir(sku)
        image_info = inspect_images(image_dir)
        
        # Step 4: 補完判定
        completeness = check_completeness(research_row)
        
        # Step 5: Listing row 構築
        listing_row = {
            "candidate_id": research_row["candidate_id"],
            "sku": sku,
            "product_name": research_row["product_name"],
            "brand": research_row.get("brand") or "",
            "model_number": research_row.get("model_number") or "",
            "category": research_row.get("category") or "",
            "image_dir": image_dir,
            "image_count": image_info["count"],
            "listing_status": completeness["status"],
            "source_url": research_row["product_url"],
            ...
        }
        
        return listing_row
```

### 欠損処理方針

| 項目 | Research での扱い | Listing での扱い | 変換時処理 |
|---|---|---|---|
| brand | 任意 | 補完希望 | 空の場合、Pending Review |
| model_number | 任意 | 補完希望 | 空の場合、Pending Review |
| category | 任意 | 必須 | 空の場合、Hard Error |
| condition | 任意 | 必須 | 空の場合、デフォルト (new) を提案 |
| user_notes | 任意 | 参考 | そのまま transfer |
| user_tags | 任意 | 参考 | そのまま transfer |

---

## eBay Payload への橋渡し

### Listing-Ready の完成条件

以下をすべて満たした時点で「Listing-Ready」と判定

```
✅ candidate_id が存在
✅ product_name が存在し、30文字以上、最大80文字
✅ sku が確定（MARGIN-YYYYMMDD-NNNN 形式）
✅ category が確定（eBay category ID と紐付けられている状態）
✅ condition が正規化済み (new / used / refurbished のいずれか)
✅ image_dir が存在し、最低1枚以上の画像がある
✅ reference_price が小数第2位の有効な数値
✅ source_url（product_url）が保持されている
✅ 監査情報（observed_date, source_type）が残存
✅ validation_status = "passed"
✅ completeness_status = "ready" or "pending_review"（hard_error でない）
```

### Phase 3 出力の構造

```python
listing_ready_record = {
    # 基本識別情報
    "candidate_id": "ms-res-20260613-0001",
    "sku": "MARGIN-20260613-0001",
    
    # 商品基本情報
    "product_name": "Canon EF 50mm f/1.8 STM",
    "brand": "Canon",
    "model_number": "EF50STM",
    "category": "Camera Lenses",
    "condition": "new",
    
    # 価格・通貨
    "reference_price": 189.99,
    "currency": "USD",
    
    # 画像情報
    "image_dir": "data/images/MARGIN-20260613-0001/",
    "image_count": 3,
    "image_files": ["01.jpg", "02.jpg", "03.jpg"],
    
    # 状態・検証
    "listing_status": "ready",  # ready, pending_review, incomplete
    "validation_status": "passed",
    "completeness_status": "ready",
    
    # 監査・追跡
    "source_url": "https://www.ebay.com/itm/...",
    "source_type": "ebay_listing",
    "observed_date": "2026-06-13T14:30:00Z",
    "transformation_timestamp": "2026-06-13T15:05:00Z",
    "user_notes": "状態良好・レンズクリア",
    "user_tags": ["high-demand", "checked"],
    
    # Phase 4 のための構造 (未実装)
    "ebay_category_id": None,  # Phase 4 で設定
    "ebay_title_template": "{brand} {model_number} {condition}",
    "ebay_description_template": None,
}
```

### Phase 4 への引き渡し

```
Phase 3 出力: transformed_listing.csv

Phase 4 入力:
  1. transformed_listing.csv を読込
  2. 各行を listing_ready_record に復元
  3. eBay category ID をマッピング
  4. eBay title を生成
  5. eBay description テンプレートを適用
  6. Price & Quantity を設定（参考価格 → 出品価格への変換ロジック）
  7. Payload builder へ渡す
  8. eBay API へ出品実行
```

---

## 監査・追跡設計

### 追跡性の確保方針

Research ID と Listing SKU を分離しながら、常に相互参照可能にする

```
Research phase:
  candidate_id: ms-res-20260613-0001 (リサーチ時の一意ID)

Listing phase:
  sku: MARGIN-20260613-0001 (出品用SKU)
  audit_trail.research_id: ms-res-20260613-0001 (元ID保持)
  
逆引き可能性:
  transformed_listing.csv の各行に candidate_id が含まれる
  → CSV を見れば research ID で元データを検索可能
```

### 監査ログに残すべき最小項目

```python
audit_record = {
    # 識別情報
    "research_id": "ms-res-20260613-0001",
    "listing_sku": "MARGIN-20260613-0001",
    
    # 源泉情報
    "source_type": "ebay_listing",  # どこから取得したか
    "source_url": "https://www.ebay.com/itm/...",
    "observed_price": 189.99,
    "observed_date": "2026-06-13T14:30:00Z",
    
    # ユーザー判定
    "user_notes": "状態良好・レンズクリア",
    "user_tags": ["high-demand"],
    "judgement_flag": "promising",
    
    # 変換タイムスタンプ
    "collection_timestamp": "2026-06-13T14:35:00Z",  # リサーチ収集時
    "transformation_timestamp": "2026-06-13T15:05:00Z",  # CSV変換時
    
    # 検証結果
    "validation_status": "passed",
    "completeness_status": "ready",
    
    # 変換ルール適用
    "sku_strategy": "auto_generation",
    "image_resolution_status": "resolved",
}
```

### 監査ログの活用例

```
Q: SKU「MARGIN-20260613-0001」が不適切に出品された。原因は何か？
A: transformed_listing.csv から candidate_id を検索
   → research_sample.csv で元の観測データを確認
   → user_notes, source_url を確認
   → どのユーザー判定のもとに出品判定されたかが明確に

Q: reference_price と 実出品価格が乖離している。
A: 監査ログから observed_price を確認
   → pricing_rule の設定内容を検証
   → Phase 4 での価格変換ロジックに問題ないか確認
```

---

## まとめ

Phase 3 で確定すること:

- ✅ Research CSV と Listing CSV の明確な分離
- ✅ 段階的な変換レイヤー (Layer 1-4)
- ✅ 必須・任意・補完・監査項目の分類
- ✅ SKU 自動採番戦略
- ✅ 画像ディレクトリ解決戦略
- ✅ バリデーションレベルの定義
- ✅ Listing-Ready の完成条件
- ✅ 追跡性と監査情報の保持

次フェーズ (Phase 4) への引き渡し:

- ✅ Transformed Listing CSV
- ✅ Listing-Ready レコードの構造
- ✅ eBay Category マッピングルール（定義のみ、実装はPhase 4）
- ✅ eBay Payload Builder への入力形式

**版**: 0.1  
**作成日**: 2026-06-13  
**ステータス**: 設計段階  
**次ステップ**: Phase 4 - eBay Payload Builder 実装

# MarginScout 最終スコープ定義書

**作成日**: 2026-06-14
**ステータス**: スコープ確定フェーズ
**バージョン**: 1.1
**責務**: 自動爆益商品リサーチ・評価専門

---

## 1. 概要

MarginScout は**商品候補の自動リサーチと評価に特化した Research App** です。

- ✅ **責務**: リサーチ・分析・評価・CSV 出力まで
- ❌ **責務外**: 最終カテゴリ確定・最終価格決定・eBay 出品実行

**最終カテゴリ確定・最終価格決定・出品実行は別アプリ（eBay Listing App）で実施されます。**

**スローガン**: 「高利益候補を自動発掘し、参考価格・参考カテゴリを CSV で提供する」

---

## 2. 入力仕様

### 2.1 データソース
- **小売店 CSV**（仕入元商品リスト）
  - 必須カラム: SKU, 商品名, 仕入価格, カテゴリ, URL
  - 例: `retail_products.csv`
- **eBay カテゴリマッピング** (static/参考用)
  - `docs/EBAY_CATEGORY_MAPPING.md` 参照
  - **用途**: リサーチ中の参考・候補評価のみ。最終カテゴリ確定は eBay Listing App で実施
- **参考価格戦略設定** (static/config)
  - `docs/EBAY_PRICE_STRATEGY.md` 参照
  - **用途**: 相場分析・利益計算の参考のみ。最終価格決定は eBay Listing App で実施

---

## 3. 処理フロー (Phase 1-2)

```text
Input CSV
       ↓
[Research Workflow]
  ├─ Product Normalization
  ├─ Category Mapping (参考用・候補抽出)
  ├─ Price Analysis (参考相場取得)
  ├─ Profit Evaluation (利益率計算)
  └─ Risk Assessment
       ↓
Output CSV (research_results.csv + listing_seed.csv)
       + Audit Log
       ↓
[eBay Listing App] ← 別アプリで最終確定・出品
  ├─ 最終カテゴリ確定
  ├─ 最終価格決定
  ├─ Payload 生成
  └─ eBay への出品実行
```

---

## 4. 出力仕様

### 4.1 research_results.csv
最終的なリサーチ結果。参考情報として eBay Listing App が利用可能。

**カラム例**:
| カラム | 型 | 説明 |
|---|---|---|
| research_id | string | 一意識別子 (MSCOUT-YYYYMMDD-XXXXXX) |
| sku | string | 仕入元 SKU |
| product_name | string | 正規化後の商品名 |
| category | string | **参考** eBay カテゴリ ID（最終確定は eBay Listing App） |
| retail_price | float | 仕入価格 (JPY) |
| ebay_market_price | float | **参考** eBay 市場相場 (USD)（最終価格は eBay Listing App） |
| estimated_profit | float | **参考** 推定利益 (USD)（最終は eBay Listing App） |
| profit_margin | float | **参考** 利益率 (%)（最終計算は eBay Listing App） |
| risk_flag | string | リスク評価 (LOW, MEDIUM, HIGH) |
| recommendation | string | 出品推奨度 (STRONG, WEAK, NOT_RECOMMENDED) |
| timestamp | datetime | リサーチ実行時刻 |

**重要**: 本カラムの価格・カテゴリは MarginScout の参考値です。最終的な eBay 出品時の価格・カテゴリは eBay Listing App で確定されます。

### 4.2 listing_seed.csv
eBay Listing App へのインプット。候補情報を参考として提供。

**カラム例**:
| カラム | 例 | 備考 |
|---|---|---|
| research_id | MSCOUT-20260614-001 | 参考用 ID |
| sku | MARGIN-SCOUT-001 | MarginScout 内部 SKU |
| product_name | Example Product | 正規化済み商品名 |
| ebay_category_id | 27000 | **参考** カテゴリ ID（最終確定は eBay Listing App） |
| estimated_price_usd | 99.99 | **参考** 相場価格（最終価格は eBay Listing App） |
| quantity_available | 10 | 在庫数 |

**重要**: カテゴリ ID・価格は参考値です。eBay Listing App が最終確定・検証して出品します。

### 4.3 監査ログ
- `research_audit_YYYYMMDD_HHMMSS.log`
- タイムスタンプ
- 処理内容 (normalization, category_mapping, price_analysis, profit_evaluation)
- 入力数 / 成功数 / 失敗数
- エラー詳細

---

## 5. 責務一覧（DO）

### Phase 1: Research Framework Design
- [ ] データ正規化エンジンの設計
- [ ] カテゴリマッピング候補抽出ロジック（参考用）の実装
- [ ] 価格分析エンジンの構築（参考相場取得用）

### Phase 2: Automated Product Research Workflow
- [ ] 商品候補の自動収集・分析
- [ ] eBay 参考相場データ取得・分析
- [ ] 利益率・ROI 参考値の計算
- [ ] 参考カテゴリ候補の提示
- [ ] CSV 出力フォーマット定義
- [ ] リサーチ監査ログの記録

### 共通
- [ ] 商品正規化ロジック
- [ ] 参考カテゴリマッピング（最終確定は eBay Listing App）
- [ ] 参考価格戦略の適用（最終価格は eBay Listing App）
- [ ] 利益率計算（参考値）
- [ ] CSV I/O (research_results.csv, listing_seed.csv)
- [ ] error handling & logging
- [ ] unit tests & integration tests

---

## 6. 責務一覧（DO NOT）

### ❌ eBay Listing App が責務を取る
- [ ] **最終カテゴリ確定** ← MarginScout は参考候補のみ提示
- [ ] **最終価格決定** ← MarginScout は参考相場のみ提示
- [ ] eBay OAuth 認証
- [ ] eBay Live API 連携
- [ ] Inventory Item 作成
- [ ] Offer 生成・Publish
- [ ] 在庫同期 (Inventory Sync)
- [ ] 注文ポーリング (Order Poller)
- [ ] 注文履行管理 (Order Management)
- [ ] Sandbox/Production API テスト

### 除外モジュール（削除対象）
- `src/payload_builder/*` – eBay Listing App へ MOVE
- `src/executor/*` – eBay Listing App へ MOVE
- `src/api_integration/*` – eBay Listing App へ MOVE
- `src/order_management/*` – eBay Listing App へ MOVE
- `oauth_handler.py` – eBay Listing App へ MOVE
- `ebay_client.py` – eBay Listing App へ MOVE
- PHASE6, PHASE7 ドキュメント – eBay Listing App へ MOVE

---

## 7. 技術スタック

| 項目 | 詳細 |
|---|---|
| 言語 | Python 3.11+ |
| フレームワーク | pandas, numpy |
| データ入力 | CSV (UTF-8) |
| データ出力 | CSV (UTF-8) + JSON (監査ログ) |
| 設定管理 | .env (config_loader.py) |
| テスト | pytest |
| ログ | logging + 監査ログファイル |

---

## 8. ディレクトリ構成（最終）

```text
margin-scout/
├── src/
│   └── research_workflow/
│       ├── research_data.py
│       ├── research_processor.py
│       ├── normalizer.py
│       ├── category_mapper.py (参考用)
│       ├── price_analyzer.py (参考用)
│       └── profit_evaluator.py
├── tests/
│   ├── test_normalizer.py
│   ├── test_category_mapper.py
│   ├── test_price_analyzer.py
│   └── test_profit_evaluator.py
├── docs/
│   ├── RESEARCH_DATA_MODEL.md
│   ├── PHASE2_RESEARCH_WORKFLOW.md
│   ├── EBAY_CATEGORY_MAPPING.md (参考用)
│   ├── EBAY_PRICE_STRATEGY.md (参考用)
│   └── MARGINSCOUT_SCOPE.md
├── examples/
│   ├── research_sample.csv
│   └── research_to_listing_mapping.md
├── config_loader.py (共有)
├── requirements.txt
├── README.md (修正版)
└── .env
```

---

## 9. CSV インターフェース仕様

### 入力フォーマット (小売店提供)
```csv
sku,product_name,retail_price_jpy,category,url
R001,Product A,5000,Electronics,https://...
R002,Product B,15000,Books,https://...
```

### 出力フォーマット (research_results.csv)
```csv
research_id,sku,product_name,category,retail_price,ebay_market_price,estimated_profit,profit_margin,risk_flag,recommendation,timestamp
MSCOUT-20260614-001,R001,Product A,12345,5000,80.00,250.00,18.5,LOW,STRONG,2026-06-14T10:00:00Z
```
**注記**: `category`, `ebay_market_price`, `estimated_profit`, `profit_margin` は参考値です。最終的な eBay 出品時は eBay Listing App で確定されます。

### Listing Seed CSV (listing_seed.csv)
```csv
research_id,sku,product_name,ebay_category_id,estimated_price_usd,quantity_available
MSCOUT-20260614-001,MARGIN-SCOUT-001,Product A,12345,80.00,10
```
**注記**: `ebay_category_id`, `estimated_price_usd` は参考値です。eBay Listing App が最終確定します。

---

## 10. テスト計画
| テスト | 対象モジュール | 成功基準 |
|---|---|---|
| Unit | normalizer, category_mapper, price_analyzer, profit_evaluator | 100% pass |
| Integration | research_workflow end-to-end | input CSV → output CSV 生成成功 |
| CSV I/O | csv_exporter, csv_validator | フォーマット正合性、エンコーディング確認 |

---

## 11. eBay Listing App との連携

### データフロー
```text
MarginScout (参考情報提供)
  ↓
listing_seed.csv (参考カテゴリ・参考価格含む)
  ↓
eBay Listing App (最終確定・出品実行)
  - 最終カテゴリ検証・確定
  - 最終価格計算・確定
  - Payload 生成
  - eBay Live API へ送信
```

### 責務の明確な分離
- **MarginScout**: 参考情報の提供まで
- **eBay Listing App**: 最終確定・出品実行

---

## 12. 次ステップ
- ✅ スコープ承認
- → eBay Listing App スコープ確認 (LISTING_APP_SCOPE.md)
- → MIGRATION_PLAN.md Phase 2 開始

---

## 付録: 設計参考
- `RESEARCH_DATA_MODEL.md`: データモデル詳細
- `PHASE2_RESEARCH_WORKFLOW.md`: Phase 2 実装仕様
- `research_to_listing_mapping.md`: CSV インターフェース詳細

MarginScout スコープ定義書 v1.1
作成日: 2026-06-14
修正日: 2026-06-14
承認待ち

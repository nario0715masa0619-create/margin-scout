# MarginScout 最終スコープ定義書

**作成日**: 2026-06-14
**ステータス**: スコープ確定フェーズ
**バージョン**: 1.0
**責務**: 自動爆益商品リサーチ機能専門

---

## 1. 概要

MarginScout は**商品候補の自動リサーチと評価に特化した Research App** です。eBay 出品・在庫管理・注文処理は別アプリ（eBay Listing App）で行います。

**スローガン**: 「高利益候補を自動発掘し、CSV で提供する」

---

## 2. 入力仕様

### 2.1 データソース
- **小売店 CSV**（仕入元商品リスト）
  - 必須カラム: SKU, 商品名, 仕入価格, カテゴリ, URL
  - 例: `retail_products.csv`
- **eBay カテゴリマッピング** (static)
  - `docs/EBAY_CATEGORY_MAPPING.md` 参照
- **価格戦略設定** (static/config)
  - `EBAY_PRICE_STRATEGY.md` 参照

### 2.2 リサーチ対象
- 仕入価格 1,000 ～ 50,000 円
- eBay で取扱可能なカテゴリ
- 利益率目標 20% 以上

---

## 3. 処理フロー (Phase 1-2)

```text
Input CSV
       ↓
[Research Workflow]
  1. Product Normalization
  2. Category Mapping
  3. Price Analysis (相場調査)
  4. Profit Evaluation
  5. Risk Assessment
       ↓
Output CSV (research_results.csv)
Listing Seed CSV (listing_seed.csv)
Audit Log
```

---

## 4. 出力仕様

### 4.1 research_results.csv
最終的なリサーチ結果。eBay Listing App が参考用に利用可能。

**カラム例**:
| カラム | 型 | 説明 |
|---|---|---|
| research_id | string | 一意識別子 (MSCOUT-YYYYMMDD-XXXXXX) |
| sku | string | 仕入元 SKU |
| product_name | string | 正規化後の商品名 |
| category | string | eBay カテゴリ ID |
| retail_price | float | 仕入価格 (JPY) |
| ebay_market_price | float | eBay 市場相場 (USD) |
| estimated_profit | float | 推定利益 (USD) |
| profit_margin | float | 利益率 (%) |
| risk_flag | string | リスク評価 (LOW, MEDIUM, HIGH) |
| recommendation | string | 出品推奨度 (STRONG, WEAK, NOT_RECOMMENDED) |
| timestamp | datetime | リサーチ実行時刻 |

### 4.2 listing_seed.csv
eBay Listing App にインプットするための CSV。必須フィールドのみ。

**カラム例**:
| カラム | 例 |
|---|---|
| research_id | MSCOUT-20260614-001 |
| sku | MARGIN-SCOUT-001 |
| product_name | Example Product |
| ebay_category_id | 27000 |
| estimated_price_usd | 99.99 |
| quantity_available | 10 |

### 4.3 監査ログ
`research_audit_YYYYMMDD_HHMMSS.log`
- タイムスタンプ
- 処理内容 (normalization, category_mapping, price_analysis, profit_evaluation)
- 入力数 / 成功数 / 失敗数
- エラー詳細

---

## 5. 責務一覧（DO）

### Phase 1: Research Framework Design
- [ ] データ正規化エンジンの設計
- [ ] カテゴリマッピングロジックの実装
- [ ] 価格分析エンジンの構築

### Phase 2: Automated Product Research Workflow
- [ ] 商品候補の自動収集
- [ ] eBay 相場データ取得・分析
- [ ] 利益率計算と評価
- [ ] CSV 出力フォーマット定義
- [ ] リサーチ監査ログの記録

### 共通
- [ ] data normalization logic
- [ ] category mapping rules
- [ ] profit evaluation formula
- [ ] CSV I/O (research_results.csv, listing_seed.csv)
- [ ] error handling & logging
- [ ] unit tests & integration tests

---

## 6. 責務一覧（DO NOT）

### ❌ eBay Listing App が責務を取る
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
│       ├── category_mapper.py
│       ├── price_analyzer.py
│       └── profit_evaluator.py
├── tests/
│   ├── test_normalizer.py
│   ├── test_category_mapper.py
│   ├── test_price_analyzer.py
│   └── test_profit_evaluator.py
├── docs/
│   ├── RESEARCH_DATA_MODEL.md
│   ├── PHASE2_RESEARCH_WORKFLOW.md
│   ├── EBAY_CATEGORY_MAPPING.md
│   └── EBAY_PRICE_STRATEGY.md
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

### Listing Seed CSV (listing_seed.csv)
```csv
research_id,sku,product_name,ebay_category_id,estimated_price_usd,quantity_available
MSCOUT-20260614-001,MARGIN-SCOUT-001,Product A,12345,80.00,10
```

---

## 10. テスト計画
| テスト | 対象モジュール | 成功基準 |
|---|---|---|
| Unit | normalizer, category_mapper, price_analyzer, profit_evaluator | 100% pass |
| Integration | research_workflow end-to-end | input CSV → output CSV 일치 |
| CSV I/O | csv_exporter, csv_validator | フォーマット正合性、エンコーディング確認 |

---

## 11. 次ステップ
- ✅ スコープ承認
- → eBay Listing App スコープ確認 (`LISTING_APP_SCOPE.md`)
- → `MIGRATION_PLAN.md` Phase 2 開始

### 付録: 設計参考
- `RESEARCH_DATA_MODEL.md`: データモデル詳細
- `PHASE2_RESEARCH_WORKFLOW.md`: Phase 2 実装仕様
- `research_to_listing_mapping.md`: CSV インターフェース詳細

```text
MarginScout スコープ定義書 v1.0
作成日: 2026-06-14
承認待ち
```

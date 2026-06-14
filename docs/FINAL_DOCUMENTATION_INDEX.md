# マージスカウト・eBay リスティング アプリ 最終ドキュメント INDEX

**バージョン**: 1.0
**作成日**: 2026-06-14
**ステータス**: 分離完了

---

## 全体概要

MarginScout プロジェクトは、**自動爆益商品リサーチ機能** と **eBay 出品・在庫・注文管理機能** を 2 つの独立したアプリケーションに分離しました。

---

## MarginScout（リサーチエンジン）

**責務**: 商品候補の自動リサーチ・分析・CSV 出力

### ドキュメント
- [MARGINSCOUT_SCOPE.md](../margin-scout/docs/MARGINSCOUT_SCOPE.md) – 最終スコープ定義
- [RESEARCH_DATA_MODEL.md](../margin-scout/docs/RESEARCH_DATA_MODEL.md) – データモデル
- [PHASE2_RESEARCH_WORKFLOW.md](../margin-scout/docs/PHASE2_RESEARCH_WORKFLOW.md) – 実装仕様
- [EBAY_CATEGORY_MAPPING.md](../margin-scout/docs/EBAY_CATEGORY_MAPPING.md) – カテゴリマッピング
- [README.md](../margin-scout/README.md) – クイックスタート

### 入出力
- **入力**: retail_products.csv（小売店商品）
- **出力**: research_results.csv + listing_seed.csv

---

## eBay Listing App（出品・管理エンジン）

**責務**: eBay への自動出品・在庫同期・注文管理

### ドキュメント
- [LISTING_APP_SCOPE.md](../ebay-listing-app/docs/LISTING_APP_SCOPE.md) – 最終スコープ定義
- [PHASE3_CSV_INTEGRATION.md](../ebay-listing-app/docs/PHASE3_CSV_INTEGRATION.md) – Phase 3
- [PHASE4_EBAY_PAYLOAD_BUILDER.md](../ebay-listing-app/docs/PHASE4_EBAY_PAYLOAD_BUILDER.md) – Phase 4
- [PHASE5_EBAY_EXECUTOR.md](../ebay-listing-app/docs/PHASE5_EBAY_EXECUTOR.md) – Phase 5
- [PHASE6_EBAY_API_INTEGRATION.md](../ebay-listing-app/docs/PHASE6_EBAY_API_INTEGRATION.md) – Phase 6
- [PHASE7_INVENTORY_SYNC_AND_ORDER_MANAGEMENT.md](../ebay-listing-app/docs/PHASE7_INVENTORY_SYNC_AND_ORDER_MANAGEMENT.md) – Phase 7
- [EBAY_OAUTH_FLOW.md](../ebay-listing-app/docs/EBAY_OAUTH_FLOW.md) – OAuth フロー
- [README.md](../ebay-listing-app/README.md) – クイックスタート

### 入出力
- **入力**: listing_seed.csv（MarginScout 出力）
- **出力**: eBay Live Account（リスティング・在庫・注文）

---

## 分離プロセス

### 関連ドキュメント
- [SEPARATION_REPORT.md](#separation_reportmd) – 分離完了報告書
- [MIGRATION_PLAN.md](../margin-scout/docs/MIGRATION_PLAN.md) – 実行計画
- [KEEP_MOVE_ARCHIVE_MATRIX.md](../margin-scout/docs/KEEP_MOVE_ARCHIVE_MATRIX.md) – 棚卸しマトリクス

---

## CSV インターフェース仕様

### research_results.csv（MarginScout 出力）
\\\csv
research_id,sku,product_name,category,retail_price,ebay_market_price,estimated_profit,profit_margin,risk_flag,recommendation,timestamp
MSCOUT-20260614-001,R001,Product Name,12345,5000,80.00,250.00,18.5,LOW,STRONG,2026-06-14T10:00:00Z
\\\

### listing_seed.csv（MarginScout → eBay Listing App）
\\\csv
research_id,sku,product_name,ebay_category_id,estimated_price_usd,quantity_available
MSCOUT-20260614-001,MARGIN-SCOUT-001,Product Name,12345,80.00,10
\\\

---

## セットアップガイド

### MarginScout
\\\ash
cd margin-scout
pip install -r requirements.txt
python -m src.research_workflow.research_processor input.csv
\\\

### eBay Listing App
\\\ash
cd ebay-listing-app
pip install -r requirements.txt
python -m src.executor.dry_run_executor listing_seed.csv
\\\

---

## サポート・トラブルシューティング

### MarginScout のトラブル
- インポートエラー → 仮想環境を確認
- CSV 形式エラー → RESEARCH_DATA_MODEL.md を参照

### eBay Listing App のトラブル
- OAuth エラー → EBAY_OAUTH_FLOW.md を参照
- API エラー → EBAY_LIVE_API_SPEC.md を参照
- CSV エラー → PHASE3_CSV_INTEGRATION.md を参照

---
最終更新: 2026-06-14
ステータス: Production-Ready (Research), Phase 3-7 Implementation Pending (Listing App)

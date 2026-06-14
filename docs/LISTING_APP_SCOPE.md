# eBay Listing App 初期スコープ定義書

**作成日**: 2026-06-14
**ステータス**: スコープ確定フェーズ
**バージョン**: 1.0
**責務**: eBay 出品・在庫・注文管理専門

---

## 1. 概要

**eBay Listing App** は MarginScout が出力した CSV を取り込み、eBay での出品・在庫同期・注文管理を一貫して行う **Listing & Order Management App** です。

**スローガン**: 「リサーチ結果を eBay に自動出品・管理する」

---

## 2. 入力仕様

### 2.1 データソース
- **MarginScout 出力**: `listing_seed.csv`
  - 必須カラム: research_id, sku, product_name, ebay_category_id, estimated_price_usd, quantity_available
- **eBay OAuth 認証情報** (.env)
  - EBAY_CLIENT_ID, EBAY_CLIENT_SECRET, EBAY_REFRESH_TOKEN
- **出品ポリシー** (Payment/Return/Fulfillment Policy)
  - eBay Seller Account にて事前設定済み

### 2.2 処理トリガー
- 手動実行: `python listing_app.py --input listing_seed.csv`
- スケジュール実行: cron/scheduler で定期実行可能

---

## 3. 処理フロー (Phase 3-7)

```text
listing_seed.csv (MarginScout)
       ↓
[eBay Listing App]
  Phase 3: CSV Integration (読込・検証)
  Phase 4: eBay Payload Builder (ペイロード生成)
  Phase 5: Dry-run Executor (テスト実行)
  Phase 6: OAuth & Live API (本番出品)
  Phase 7: Inventory Sync & Order Management (同期・注文管理)
       ↓
eBay Live Account
  + Inventory Item 作成
  + Offer 生成・Publish
  + 在庫リアルタイム同期
  + 注文受信・処理
```

---

## 4. 出力仕様

### 4.1 リスティング結果ログ
`listing_execution_YYYYMMDD_HHMMSS.log`
- timestamp
- research_id → ebay_item_id マッピング
- 出品ステータス (SUCCESS, PARTIAL_FAIL, FAILED)
- エラー詳細

### 4.2 在庫同期ログ
`inventory_sync_YYYYMMDD_HHMMSS.log`
- 同期時刻
- MarginScout 数量 vs eBay 現在数量
- 差分調整履歴

### 4.3 注文ポーリングログ
`order_poll_YYYYMMDD_HHMMSS.log`
- ポーリング時刻
- 新規受注数
- 処理状態 (RECEIVED, PROCESSED, SHIPPED)

---

## 5. 責務一覧（DO）

### Phase 3: CSV Integration
- [ ] listing_seed.csv 読込・パース
- [ ] データ検証・正規化
- [ ] 入力エラーハンドリング

### Phase 4: eBay Payload Builder
- [ ] Inventory Item ペイロード生成
- [ ] Offer ペイロード生成
- [ ] eBay API 仕様への準拠

### Phase 5: Dry-run Executor
- [ ] Mock API での動作確認
- [ ] ペイロード検証
- [ ] テストレポート生成

### Phase 6: OAuth & Live API
- [ ] eBay OAuth トークン管理
- [ ] Live API への Inventory Item 作成
- [ ] Offer 生成・Publish
- [ ] レスポンス処理・エラーハンドリング
- [ ] リスティング結果ログ

### Phase 7: Inventory Sync & Order Management
- [ ] 在庫リアルタイム同期 (eBay ← MarginScout)
- [ ] 注文ポーリング (eBay Order API)
- [ ] 注文ステータス管理
- [ ] 出荷連携

---

## 6. 責務一覧（DO NOT）

### ❌ MarginScout が責務を取る
- [ ] 商品リサーチ
- [ ] 価格分析
- [ ] 利益評価
- [ ] CSV データソース管理

### 除外・禁止事項
- MarginScout の research_results.csv 直接変更
- MarginScout の リサーチロジック変更
- 独立した商品情報管理（MarginScout に一元化）

---

## 7. 技術スタック

| 項目 | 詳細 |
|---|---|
| 言語 | Python 3.11+ |
| フレームワーク | requests (eBay API), pandas |
| 認証 | OAuth 2.0 (eBay) |
| API | eBay Sell Inventory API, eBay Order API |
| データ入力 | CSV (UTF-8) from MarginScout |
| 設定管理 | .env (config_loader.py 共有) |
| テスト | pytest, mocking |
| ログ | logging + 実行ログファイル |

---

## 8. ディレクトリ構成（初期）

```text
ebay-listing-app/
├── src/
│   ├── csv_integration/
│   │   ├── csv_loader.py
│   │   └── csv_validator.py
│   ├── payload_builder/
│   │   ├── inventory_builder.py
│   │   └── offer_builder.py
│   ├── executor/
│   │   ├── dry_run_executor.py
│   │   └── live_executor.py
│   ├── api_integration/
│   │   ├── oauth_handler.py
│   │   ├── ebay_client.py
│   │   └── response_processor.py
│   ├── order_management/
│   │   ├── order_poller.py
│   │   ├── inventory_sync.py
│   │   └── order_processor.py
│   └── config_loader.py (共有)
├── tests/
│   ├── test_csv_loader.py
│   ├── test_payload_builder.py
│   ├── test_dry_run_executor.py
│   └── test_live_executor.py
├── docs/
│   ├── PHASE3_CSV_INTEGRATION.md
│   ├── PHASE4_EBAY_PAYLOAD_BUILDER.md
│   ├── PHASE5_EBAY_EXECUTOR.md
│   ├── PHASE6_EBAY_API_INTEGRATION.md
│   ├── PHASE7_INVENTORY_SYNC_AND_ORDER_MANAGEMENT.md
│   ├── EBAY_OAUTH_FLOW.md
│   ├── EBAY_LIVE_API_SPEC.md
│   └── ORDER_MANAGEMENT_SPECIFICATION.md
├── examples/
│   └── listing_seed_sample.csv
├── requirements.txt
├── setup.py
├── README.md
└── .env
```

---

## 9. CSV インターフェース仕様

### 入力: listing_seed.csv (MarginScout → Listing App)
```csv
research_id,sku,product_name,ebay_category_id,estimated_price_usd,quantity_available
MSCOUT-20260614-001,MARGIN-SCOUT-001,Example Product,12345,80.00,10
```

### 出力: listing_execution_log (内部ログ)
```text
[2026-06-14 10:30:45] STARTED: Processing listing_seed.csv
[2026-06-14 10:30:46] INVENTORY_CREATE: MSCOUT-20260614-001 → SKU-EBAY-001 (status 204)
[2026-06-14 10:30:47] OFFER_CREATE: SKU-EBAY-001 → Offer ID 11165324010 (status 201)
[2026-06-14 10:30:48] PUBLISH: Offer 11165324010 (status 200)
[2026-06-14 10:30:49] SUCCESS: 1/1 listings published
```

---

## 10. テスト計画
| テスト | 対象モジュール | 成功基準 |
|---|---|---|
| Unit | csv_loader, payload_builder, oauth_handler | 100% pass |
| Integration | CSV → Payload → Mock Executor | end-to-end 成功 |
| Live (Sandbox) | Live API 連携 | Inventory/Offer/Publish 確認 |
| E2E (Production) | 本番環境テスト | リスティング作成確認 |

---

## 11. エラーハンドリング
| 例外 | 対応 |
|---|---|
| CSV パースエラー | ログ出力 + スキップ |
| OAuth トークン無効 | リフレッシュ試行 |
| API 400 エラー | ペイロード再検証 + ログ |
| API 500 エラー | リトライ (最大 3 回) |

---

## 12. セキュリティ考慮
- OAuth トークンは `.env` 環境変数で管理（Git 追跡外）
- API レスポンスから機密情報をフィルタリング
- ログファイルに機密情報を記録しない

---

## 13. 次ステップ
- ✅ eBay Listing App スコープ承認
- → `MIGRATION_PLAN.md` Phase 2 開始（リポジトリ初期化）
- → Phase 3 実装開始

### 付録: 参考ドキュメント
- `PHASE3_CSV_INTEGRATION.md`
- `PHASE6_EBAY_API_INTEGRATION.md`
- `EBAY_OAUTH_FLOW.md`

```text
eBay Listing App スコープ定義書 v1.0
作成日: 2026-06-14
承認待ち
```

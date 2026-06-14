# ファイル・モジュール棚卸しマトリクス

**作成日**: 2026-06-14  
**ステータス**: 計画フェーズ（実装前）  
**バージョン**: 1.0

---

## 目次
1. [凡例](#凡例)
2. [ディレクトリ・ファイル棚卸し](#ディレクトリファイル棚卸し)
3. [統計サマリー](#統計サマリー)
4. [移設対象の詳細リスト](#移設対象の詳細リスト)
5. [一時保留項目](#一時保留項目)
6. [アーカイブ対象](#アーカイブ対象)

---

## 凡例

| 記号 | 意味 | 説明 | 対応 |
|------|------|------|------|
| 🔵 | KEEP | MarginScout に残す | そのまま保持 |
| 🔴 | MOVE | eBay Listing App へ移す | コピー後、元リポは削除 |
| 🟡 | HOLD | 一時保留 | 後で判断 |
| ⚫ | ARCHIVE | 参考用に保持 | 共有パッケージ等 |

---

## ディレクトリ・ファイル棚卸し

### `src/research_workflow/` ディレクトリ

| ファイル | 行数 | 決定 | 理由 | 備考 |
|---------|------|------|------|------|
| `__init__.py` | - | 🔵 KEEP | MarginScout コア | リサーチ初期化 |
| `research_data.py` | ~150 | 🔵 KEEP | リサーチデータ構造 | MarginScout コア機能 |
| `research_processor.py` | ~200 | 🔵 KEEP | リサーチ処理エンジン | MarginScout コア機能 |

**小計**: KEEP 3 / MOVE 0 / HOLD 0 / ARCHIVE 0 = **3 ファイル**

---

### `src/csv_integration/` ディレクトリ

| ファイル | 行数 | 決定 | 理由 | 備考 |
|---------|------|------|------|------|
| `__init__.py` | - | 🔴 MOVE | 出品用 CSV 統合 | eBay Listing App 責務 |
| `csv_mapper.py` | ~250 | 🔴 MOVE | CSV → Payload マッピング | 出品データ変換 |
| `csv_validator.py` | ~180 | 🟡 HOLD | バリデーション（兼用？） | リサーチ CSV と出品 CSV で別々か? |
| `csv_exporter.py` | ~150 | 🔵 KEEP | リサーチ結果の CSV 出力 | MarginScout コア機能 |

**小計**: KEEP 1 / MOVE 2 / HOLD 1 / ARCHIVE 0 = **4 ファイル**

---

### `src/payload_builder/` ディレクトリ

| ファイル | 行数 | 決定 | 理由 | 備考 |
|---------|------|------|------|------|
| `__init__.py` | - | 🔴 MOVE | eBay Payload 生成 | 出品用 |
| `ebay_payload_builder.py` | ~400 | 🔴 MOVE | Payload 生成エンジン | 出品用 |
| `payload_validator.py` | ~200 | 🔴 MOVE | Payload 検証 | 出品用 |
| `payload_templates.py` | ~300 | 🔴 MOVE | Payload テンプレート | 出品用 |

**小計**: KEEP 0 / MOVE 4 / HOLD 0 / ARCHIVE 0 = **4 ファイル**

---

### `src/executor/` ディレクトリ

| ファイル | 行数 | 決定 | 理由 | 備考 |
|---------|------|------|------|------|
| `__init__.py` | - | 🔴 MOVE | 実行エンジン | 出品実行 |
| `dry_run_executor.py` | ~300 | 🔴 MOVE | Dry-run 実行 | 出品テスト |
| `live_executor.py` | ~350 | 🔴 MOVE | Live 実行 | eBay 出品実行 |
| `mock_ebay_service.py` | ~200 | 🔴 MOVE | Mock eBay サービス | 出品テスト用 |

**小計**: KEEP 0 / MOVE 4 / HOLD 0 / ARCHIVE 0 = **4 ファイル**

---

### `src/api_integration/` ディレクトリ

| ファイル | 行数 | 決定 | 理由 | 備考 |
|---------|------|------|------|------|
| `__init__.py` | - | 🔴 MOVE | eBay API 統合 | 出品用 |
| `oauth_handler.py` | ~250 | 🔴 MOVE | OAuth 認証 | eBay 認証（出品用） |
| `ebay_client.py` | ~400 | 🔴 MOVE | eBay Live API クライアント | eBay API 操作 |
| `response_processor.py` | ~200 | 🔴 MOVE | API レスポンス処理 | 出品用 |
| `error_handler.py` | ~150 | 🔴 MOVE | エラーハンドリング | 出品用 |

**小計**: KEEP 0 / MOVE 5 / HOLD 0 / ARCHIVE 0 = **5 ファイル**

---

### `src/order_management/` ディレクトリ

| ファイル | 行数 | 決定 | 理由 | 備考 |
|---------|------|------|------|------|
| `__init__.py` | - | 🔴 MOVE | 注文管理 | 出品用 |
| `order_poller.py` | ~300 | 🔴 MOVE | 注文ポーリング | 注文取得 |
| `inventory_sync.py` | ~280 | 🔴 MOVE | 在庫同期 | 在庫管理 |
| `order_processor.py` | ~200 | 🔴 MOVE | 注文処理 | 注文管理 |

**小計**: KEEP 0 / MOVE 4 / HOLD 0 / ARCHIVE 0 = **4 ファイル**

---

### `src/` ルート ディレクトリ

| ファイル | 行数 | 決定 | 理由 | 備考 |
|---------|------|------|------|------|
| `__init__.py` | - | 🔵 KEEP | パッケージ初期化 | 両アプリで必要 |
| `config_loader.py` | ~150 | ⚫ ARCHIVE | 環境設定読み込み | 共有ライブラリ化予定 |

**小計**: KEEP 1 / MOVE 0 / HOLD 0 / ARCHIVE 1 = **2 ファイル**

---

### `docs/` ディレクトリ

#### Research / Design Documents

| ファイル | 行数 | 決定 | 理由 | 備考 |
|---------|------|------|------|------|
| `PROJECT_ORIGIN.md` | ~80 | 🔵 KEEP | プロジェクト背景 | MarginScout 原点 |
| `PHASE1_BOOTSTRAP_DESIGN.md` | ~150 | 🔵 KEEP | Phase 1 設計（リサーチ基礎） | MarginScout 設計書 |
| `PHASE2_RESEARCH_WORKFLOW.md` | ~200 | 🔵 KEEP | リサーチワークフロー設計 | MarginScout 核心設計 |
| `RESEARCH_DATA_MODEL.md` | ~120 | 🔵 KEEP | リサーチデータモデル | MarginScout 設計書 |
| `research_to_listing_mapping.md` | ~100 | 🔵 KEEP | リサーチ → 出品マッピング | インターフェース仕様 |

**小計**: KEEP 5 / MOVE 0 / HOLD 0 / ARCHIVE 0 = **5 ファイル**

#### eBay Integration Documents

| ファイル | 行数 | 決定 | 理由 | 備考 |
|---------|------|------|------|------|
| `PHASE3_CSV_INTEGRATION.md` | ~200 | 🔴 MOVE | CSV 取込設計 | 出品用 |
| `PHASE4_EBAY_PAYLOAD_BUILDER.md` | ~250 | 🔴 MOVE | Payload Builder 設計 | 出品用 |
| `PHASE5_EBAY_EXECUTOR.md` | ~200 | 🔴 MOVE | Executor 設計 | 出品用 |
| `PHASE6_EBAY_API_INTEGRATION.md` | ~300 | 🔴 MOVE | OAuth & Live API 設計 | 出品用 |
| `PHASE7_INVENTORY_SYNC_AND_ORDER_MANAGEMENT.md` | ~250 | 🔴 MOVE | 在庫・注文管理設計 | 出品用 |

**小計**: KEEP 0 / MOVE 5 / HOLD 0 / ARCHIVE 0 = **5 ファイル**

#### Reference Documents

| ファイル | 行数 | 決定 | 理由 | 備考 |
|---------|------|------|------|------|
| `EBAY_OAUTH_FLOW.md` | ~120 | 🔴 MOVE | OAuth フロー設計 | 出品用 |
| `EBAY_LIVE_API_SPEC.md` | ~180 | 🔴 MOVE | eBay Live API 仕様 | 出品用 |
| `EBAY_PAYLOAD_MODEL.md` | ~150 | 🔴 MOVE | Payload データモデル | 出品用 |
| `EBAY_CATEGORY_MAPPING.md` | ~300 | ⚫ ARCHIVE | eBay カテゴリマッピング | 共有参照（両アプリで使用） |
| `EBAY_PRICE_STRATEGY.md` | ~180 | 🟡 HOLD | 価格戦略 | リサーチ評価と出品設定で共有? |
| `LISTING_DATA_MODEL.md` | ~150 | 🔴 MOVE | リスティングデータモデル | 出品用 |
| `ORDER_MANAGEMENT_SPECIFICATION.md` | ~200 | 🔴 MOVE | 注文管理仕様 | 出品用 |
| `CONFIGURATION.md` | ~100 | 🟡 HOLD | 環境設定（共通） | 両アプリで必要 |
| `SANDBOX_TEST_EXECUTION_GUIDE.md` | ~150 | 🔴 MOVE | Sandbox テスト実行手順 | 出品用 |

**小計**: KEEP 0 / MOVE 7 / HOLD 2 / ARCHIVE 1 = **10 ファイル**

**docs/ 合計**: KEEP 5 / MOVE 12 / HOLD 2 / ARCHIVE 1 = **20 ファイル**

---

### `tests/` ディレクトリ

| ファイル | 行数 | 決定 | 理由 | 備考 |
|---------|------|------|------|------|
| `test_research_workflow.py` | ~250 | 🔵 KEEP | リサーチワークフロー テスト | MarginScout テスト |
| `test_research_data.py` | ~200 | 🔵 KEEP | リサーチデータ テスト | MarginScout テスト |
| `test_csv_export.py` | ~150 | 🔵 KEEP | CSV エクスポート テスト | MarginScout テスト |
| `test_csv_integration_*.py` | 複数 | 🔴 MOVE | CSV 統合テスト（出品） | 出品テスト |
| `test_payload_builder_*.py` | 複数 | 🔴 MOVE | Payload Builder テスト | 出品テスト |
| `test_executor_*.py` | 複数 | 🔴 MOVE | Executor テスト | 出品テスト |
| `test_api_integration_*.py` | 複数 | 🔴 MOVE | API 統合テスト | 出品テスト |
| `test_order_management_*.py` | 複数 | 🔴 MOVE | 注文管理テスト | 出品テスト |
| `conftest.py` | ~100 | 🟡 HOLD | pytest 共通設定 | 両アプリで必要か確認 |

**小計**: KEEP 3+ / MOVE 5+ / HOLD 1 / ARCHIVE 0 = **9+ ファイル**

---

### `examples/` ディレクトリ

| ファイル | サイズ | 決定 | 理由 | 備考 |
|---------|--------|------|------|------|
| `research_sample.csv` | ~1KB | 🔵 KEEP | リサーチ出力サンプル | MarginScout 例 |
| `research_to_listing_mapping.md` | ~2KB | 🔵 KEEP | マッピング例 | インターフェース仕様 |
| `ebay_payload_example.json` | ~5KB | 🔴 MOVE | eBay Payload 例 | 出品用 |
| `dry_run_result_sample.json` | ~3KB | 🔴 MOVE | Dry-run 結果例 | 出品用 |
| `live_listing_example.json` | ~4KB | 🔴 MOVE | Live リスティング例 | 出品用 |

**小計**: KEEP 2 / MOVE 3 / HOLD 0 / ARCHIVE 0 = **5 ファイル**

---

### ルートディレクトリ

| ファイル | 決定 | 理由 | 備考 |
|---------|------|------|------|
| `README.md` | 🔵 KEEP (修正) | README 修正予定 | MarginScout 用に修正 |
| `.gitignore` | 🔵 KEEP | Git 設定 | MarginScout 保持 |
| `pyproject.toml` | 🔵 KEEP (修正) | パッケージ管理 | MarginScout 用に修正 |
| `setup.py` | 🔵 KEEP (修正) | セットアップ | MarginScout 用に修正 |
| `requirements.txt` | 🔵 KEEP (修正) | 依存関係 | MarginScout 必要分のみ |
| `LICENSE` | 🔵 KEEP | ライセンス | 共通 |
| `CHANGELOG.md` | 🔵 KEEP | 変更履歴 | MarginScout 記録 |
| `PHASE*_COMPLETION_REPORT.json` | 🟡 HOLD | 完了レポート | Phase 1-2 は KEEP, Phase 3-7 は MOVE |

**小計**: KEEP 7 / MOVE 0 / HOLD 1 / ARCHIVE 0 = **8 ファイル**

---

## 統計サマリー

### ディレクトリ単位集計

| ディレクトリ | KEEP | MOVE | HOLD | ARCHIVE | 合計 |
|------------|------|------|------|---------|------|
| `src/research_workflow/` | ✅ 3 | 0 | 0 | 0 | **3** |
| `src/csv_integration/` | 1 | 2 | 1 | 0 | **4** |
| `src/payload_builder/` | 0 | ✅ 4 | 0 | 0 | **4** |
| `src/executor/` | 0 | ✅ 4 | 0 | 0 | **4** |
| `src/api_integration/` | 0 | ✅ 5 | 0 | 0 | **5** |
| `src/order_management/` | 0 | ✅ 4 | 0 | 0 | **4** |
| `src/` root | 1 | 0 | 0 | 1 | **2** |
| `docs/` | 5 | 12 | 2 | 1 | **20** |
| `tests/` | 3+ | 5+ | 1 | 0 | **9+** |
| `examples/` | 2 | 3 | 0 | 0 | **5** |
| root | 7 | 0 | 1 | 0 | **8** |
| **合計** | **22+** | **39+** | **5** | **2** | **68+** |

### サマリー集計

```text
MarginScout に残す: 22+ ファイル (32%)
eBay Listing App へ移す: 39+ ファイル (57%)
一時保留: 5 ファイル (7%)
アーカイブ: 2 ファイル (3%)
─────────────────────────────────────
合計: 68+ ファイル (100%)
```

---

## 移設対象の詳細リスト

### MarginScout に残す（🔵 KEEP）

**ディレクトリ構造**:
```text
margin-scout/ (Research App 専用)
├── src/
│   ├── research_workflow/
│   │   ├── __init__.py
│   │   ├── research_data.py # リサーチデータ構造
│   │   └── research_processor.py # リサーチ処理エンジン
│   ├── csv_integration/
│   │   ├── __init__.py
│   │   └── csv_exporter.py # CSV エクスポート（重要）
│   └── __init__.py
├── docs/
│   ├── PROJECT_ORIGIN.md
│   ├── PHASE1_BOOTSTRAP_DESIGN.md
│   ├── PHASE2_RESEARCH_WORKFLOW.md
│   ├── RESEARCH_DATA_MODEL.md
│   └── research_to_listing_mapping.md # インターフェース仕様
├── tests/
│   ├── test_research_workflow.py
│   ├── test_research_data.py
│   └── test_csv_export.py
├── examples/
│   ├── research_sample.csv
│   └── research_to_listing_mapping.md
├── README.md (修正版)
├── requirements.txt (修正版 - リサーチ用依存関係のみ)
├── pyproject.toml (修正版)
└── .gitignore
```
**ファイル数**: 22+ ファイル

---

### eBay Listing App へ移す（🔴 MOVE）

**ディレクトリ構造**:
```text
margin-scout-listing-app/ (Listing & Order Management)
├── src/
│   ├── csv_integration/
│   │   ├── __init__.py
│   │   ├── csv_mapper.py # CSV → Payload マッピング
│   │   └── csv_validator.py # CSV バリデーション
│   ├── payload_builder/
│   │   ├── __init__.py
│   │   ├── ebay_payload_builder.py
│   │   ├── payload_validator.py
│   │   └── payload_templates.py
│   ├── executor/
│   │   ├── __init__.py
│   │   ├── dry_run_executor.py
│   │   ├── live_executor.py
│   │   └── mock_ebay_service.py
│   ├── api_integration/
│   │   ├── __init__.py
│   │   ├── oauth_handler.py
│   │   ├── ebay_client.py
│   │   ├── response_processor.py
│   │   └── error_handler.py
│   └── order_management/
│       ├── __init__.py
│       ├── order_poller.py
│       ├── inventory_sync.py
│       └── order_processor.py
├── docs/
│   ├── PHASE3_CSV_INTEGRATION.md
│   ├── PHASE4_EBAY_PAYLOAD_BUILDER.md
│   ├── PHASE5_EBAY_EXECUTOR.md
│   ├── PHASE6_EBAY_API_INTEGRATION.md
│   ├── PHASE7_INVENTORY_SYNC_AND_ORDER_MANAGEMENT.md
│   ├── EBAY_OAUTH_FLOW.md
│   ├── EBAY_LIVE_API_SPEC.md
│   ├── EBAY_PAYLOAD_MODEL.md
│   ├── LISTING_DATA_MODEL.md
│   ├── ORDER_MANAGEMENT_SPECIFICATION.md
│   └── SANDBOX_TEST_EXECUTION_GUIDE.md
├── tests/
│   ├── test_csv_integration_*.py
│   ├── test_payload_builder_*.py
│   ├── test_executor_*.py
│   ├── test_api_integration_*.py
│   └── test_order_management_*.py
├── examples/
│   ├── ebay_payload_example.json
│   ├── dry_run_result_sample.json
│   └── live_listing_example.json
├── README.md (新規)
├── requirements.txt (新規 - eBay 出品用依存関係)
├── pyproject.toml (新規)
└── .gitignore
```
**ファイル数**: 39+ ファイル

---

## 一時保留項目

### 🟡 HOLD - 要検討

| # | ファイル | 理由 | 検討内容 | 決定予定 |
|----|---------|------|--------|---------|
| 1 | `src/csv_integration/csv_validator.py` | 両方で使用可能？ | リサーチ CSV 検証 vs 出品 CSV 検証を分離するか、共有するか | Phase 1 |
| 2 | `docs/EBAY_PRICE_STRATEGY.md` | リサーチと出品で共有 | 価格戦略ドキュメント（参考用か、コード化するか） | Phase 1 |
| 3 | `docs/CONFIGURATION.md` | 環境設定（両アプリ） | 共有パッケージ化するか、各アプリで独立管理するか | Phase 1 |
| 4 | `tests/conftest.py` | pytest 共通設定 | 両アプリで必要か、各アプリで独立させるか | Phase 1 |
| 5 | `PHASE*_COMPLETION_REPORT.json` | 完了レポート | Phase 1-2 レポートは KEEP, Phase 3-7 は MOVE | Phase 1 |

---

## アーカイブ対象

### ⚫ ARCHIVE - 参考用に保持

| # | ファイル | 理由 | 配置 |
|----|---------|------|------|
| 1 | `src/config_loader.py` | 共有ライブラリ化予定 | 共有パッケージ /  or submodule |
| 2 | `docs/EBAY_CATEGORY_MAPPING.md` | eBay カテゴリ参照（両アプリで使用） | 共有参照ドキュメント |

**注**: これらは削除されるのではなく、共有ライブラリ / 共有ドキュメントとして統合予定

---

## 実装ロードマップ

### Phase 3: ファイル移設 実行順序

```text
Step 1. src/ ディレクトリ移設
├─ src/payload_builder/ → eBay Listing App
├─ src/executor/ → eBay Listing App
├─ src/api_integration/ → eBay Listing App
└─ src/order_management/ → eBay Listing App

Step 2. docs/ ドキュメント移設
├─ docs/PHASE3-7_*.md → eBay Listing App
├─ docs/EBAY_*.md → eBay Listing App
└─ docs/EBAY_CATEGORY_MAPPING.md → 共有化

Step 3. tests/ テスト移設
├─ tests/test_payload_builder_*.py → eBay Listing App
├─ tests/test_executor_*.py → eBay Listing App
├─ tests/test_api_integration_*.py → eBay Listing App
└─ tests/test_order_management_*.py → eBay Listing App

Step 4. examples/ 例移設
├─ examples/ebay_payload_example.json → eBay Listing App
├─ examples/dry_run_result_sample.json → eBay Listing App
└─ examples/live_listing_example.json → eBay Listing App

Step 5. import パス調整
├─ eBay Listing App 内のパスを修正
└─ 動作確認
```

---

## チェックリスト

### Phase 3 実行前の確認

```text
□ file_inventory.json で全ファイルをスキャン
□ 各ファイルの MOVE / KEEP 判定を確認
□ eBay Listing App リポジトリの初期化完了
□ バックアップ作成完了 (git tag)
□ import 依存関係を完全に把握
□ CSV インターフェース仕様確定
```

### Phase 3 実行後の確認

```text
□ ファイルが正しくコピーされた
□ eBay Listing App で import が正しく動作
□ eBay Listing App テストが 100% パス
□ MarginScout テストが 100% パス
□ CSV インターフェーステスト成功
```

---

## 次ステップ

1. ✅ MIGRATION_PLAN.md 確認
2. ✅ **KEEP_MOVE_ARCHIVE_MATRIX.md 確認** ← **次はここ**
3. ⏳ MARGINSCOUT_SCOPE.md 確認
4. ⏳ LISTING_APP_SCOPE.md 確認
5. ⏳ README 修正案確認
6. ⏳ Phase 2 実行開始

---

## 付録

### A. ファイル棚卸しの判定基準

**🔵 KEEP の判定基準**:
- MarginScout の責務に直結している
- リサーチ、価格分析、正規化に必須
- CSV 出力の一部

**🔴 MOVE の判定基準**:
- eBay Payload 生成・変換に関連
- eBay API 操作に関連
- 出品・在庫・注文管理に関連
- eBay OAuth・認証に関連

**🟡 HOLD の判定基準**:
- 複数のアプリで使用される可能性
- 共有 vs 分離を判断需要
- Phase 1 で最終決定

**⚫ ARCHIVE の判定基準**:
- 両アプリで参照する共有リソース
- 共有パッケージ化検討
- ライブラリ化予定

### B. 参考資料

- `file_inventory.json` - 全ファイルの詳細一覧
- `migration_context.json` - 分離コンテキスト
- `MIGRATION_PLAN.md` - 分離実行計画

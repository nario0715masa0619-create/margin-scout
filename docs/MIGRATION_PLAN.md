# MarginScout / eBay Listing App 分離実行計画書

**作成日**: 2026-06-14  
**ステータス**: 計画フェーズ（実装前）  
**バージョン**: 1.0

---

## 目次
1. [目的](#目的)
2. [現状分析](#現状分析)
3. [分離方針](#分離方針)
4. [実行フェーズ](#実行フェーズ)
5. [リスク管理](#リスク管理)
6. [ロールバック方針](#ロールバック方針)
7. [成功基準](#成功基準)
8. [承認フロー](#承認フロー)

---

## 目的

margin-scout リポジトリ内に混在している以下の2つの責務を分離し、それぞれ独立した専門アプリとして確立する。

| アプリ | 役割 | 出力 |
|--------|------|------|
| **MarginScout** | 自動爆益商品リサーチ専用 | research_results.csv, listing_seed.csv |
| **eBay Listing App** | eBay 自動出品・在庫・注文管理 | eBay リスティング, 在庫データ, 注文管理 |

---

## 現状分析

### 2.1 責務の混在状況

```text
現在の margin-scout リポジトリ
├── ✅ Research（正しい配置）
│   ├── src/research_workflow/
│   ├── docs/PHASE2_RESEARCH_WORKFLOW.md
│   └── examples/research_sample.csv
│
├── ❌ Listing（分離対象）
│   ├── src/csv_integration/        → CSV Payload マッピング
│   ├── src/payload_builder/        → eBay Payload 生成
│   ├── src/executor/               → Dry-run & Live 実行
│   ├── src/api_integration/        → OAuth & Live API
│   ├── src/order_management/       → 在庫・注文管理
│   ├── docs/PHASE3-7_*             → 出品関連設計
│   └── tests/test_*_listing.py     → 出品テスト
│
└── 🔄 共有（整理対象）
    ├── src/config_loader.py
    ├── docs/EBAY_CATEGORY_MAPPING.md
    └── docs/CONFIGURATION.md
```

### 2.2 問題点

| # | 問題 | 影響 | 優先度 |
|----|------|------|--------|
| 1 | 責務の混在 | 保守性低下、テスト困難 | 🔴 High |
| 2 | eBay API 変更の波及 | MarginScout に無関係な影響 | 🔴 High |
| 3 | 独立した更新困難 | リサーチと出品を別々にアップデート不可 | 🟠 Medium |
| 4 | コード再利用困難 | 他の出品アプリから MarginScout CSV を使用できない | 🟠 Medium |
| 5 | テスト管理の複雑化 | Research と Listing テストが混在 | 🟡 Low |

### 2.3 分離のメリット

- ✅ **責務明確化**: 各アプリの役割が一目瞭然
- ✅ **独立ライフサイクル**: リサーチと出品を独立してアップデート
- ✅ **再利用性向上**: MarginScout CSV を複数の出品ツールで利用可能
- ✅ **保守性向上**: eBay API 変更が MarginScout に波及しない
- ✅ **スケーラビリティ**: 将来、Amazon / Shopify 等の出品アプリも追加可能

---

## 分離方針

### 3.1 データフロー（分離後）

```text
┌─────────────────────────────────────────────────────────────────┐
│ MarginScout (Research App)                                      │
│                                                                 │
│ ├─ Input: eBay / Amazon / その他ソース                          │
│ ├─ Process: 価格分析・正規化・利益評価                          │
│ └─ Output: research_results.csv + listing_seed.csv              │
└──────────────────────┬──────────────────────────────────────────┘
                       │ (CSV Interface)
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ eBay Listing App (Listing & Order Management)                   │
│                                                                 │
│ ├─ Input: listing_seed.csv (from MarginScout)                   │
│ ├─ Process: Payload生成→Dry-run→OAuth→Live API→Inventory→Order│
│ └─ Output: eBay リスティング / 在庫管理 / 注文管理              │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 インターフェース仕様

**MarginScout 出力 → eBay Listing App 入力**

```csv
research_id,sku,product_title,description,category_id,price,quantity,notes
RES001,PROD001,Product Title,Description,27000,99.99,10,High margin
```
詳細は `docs/research_to_listing_mapping.md` を参照。

### 3.3 分離タイムライン
| Phase | 内容 | 期間 | 依存 |
|---|---|---|---|
| Phase 0 | 計画・承認 | 1日 | - |
| Phase 1 | スコープ確定 | 0.5日 | Phase 0 |
| Phase 2 | eBay Listing App リポジトリ初期化 | 0.5日 | Phase 1 |
| Phase 3 | ファイル移設（準備） | 1.5日 | Phase 2 |
| Phase 4 | MarginScout クリーンアップ | 1日 | Phase 3 |
| Phase 5 | 統合テスト | 1.5日 | Phase 4 |

**合計**: 約 5.5日

---

## 実行フェーズ

### Phase 0: 計画・承認 ← 現在ここ
**成果物**:
- ✅ `MIGRATION_PLAN.md`（本ドキュメント）
- ✅ `KEEP_MOVE_ARCHIVE_MATRIX.md`
- ✅ `MARGINSCOUT_SCOPE.md`
- ✅ `LISTING_APP_SCOPE.md`
- ✅ `README_MARGINSCOUT_REVISED_SUMMARY.md`
- ✅ `README_LISTING_APP_INITIAL_SUMMARY.md`

**承認ポイント**: 分離計画と棚卸し結果の確認

### Phase 1: スコープ確定
**実行内容**:
```bash
# MarginScout スコープ確定
- Research App としての責務確認
- 出力 CSV 仕様確定
- 共有ライブラリ定義

# eBay Listing App スコープ確定
- 初期フェーズ定義
- インターフェース仕様確定
```
**成果物**:
- `MARGINSCOUT_FINAL_SCOPE.md`
- `LISTING_APP_FINAL_SCOPE.md`
- `CSV_INTERFACE_SPECIFICATION.md`

**承認ポイント**: スコープ確定の確認

### Phase 2: eBay Listing App リポジトリ初期化
**実行内容**:
```bash
mkdir margin-scout-listing-app
cd margin-scout-listing-app
git init
mkdir -p src/{csv_integration,payload_builder,executor,api_integration,order_management}
mkdir -p docs tests examples
touch README.md .gitignore pyproject.toml
```
**ディレクトリ構造**:
```text
margin-scout-listing-app/
├── src/
│   ├── csv_integration/
│   ├── payload_builder/
│   ├── executor/
│   ├── api_integration/
│   └── order_management/
├── docs/
├── tests/
├── examples/
├── README.md
├── .gitignore
├── pyproject.toml
└── requirements.txt
```
**承認ポイント**: リポジトリ初期化の確認

### Phase 3: ファイル移設（準備段階）
**実行内容**:
```bash
# ファイルをコピー（削除ではなくコピー）
cp -r src/csv_integration/* ../margin-scout-listing-app/src/csv_integration/
cp -r src/payload_builder/* ../margin-scout-listing-app/src/payload_builder/
cp -r src/executor/* ../margin-scout-listing-app/src/executor/
cp -r src/api_integration/* ../margin-scout-listing-app/src/api_integration/
cp -r src/order_management/* ../margin-scout-listing-app/src/order_management/

# ドキュメント移設
cp docs/PHASE3-7_*.md ../margin-scout-listing-app/docs/
cp docs/EBAY_*.md ../margin-scout-listing-app/docs/

# import パス調整
# （eBay Listing App 内のパスを修正）
```
**検証項目**:
- [ ] ファイルが正しくコピーされた
- [ ] import パスが正しく調整された
- [ ] eBay Listing App が独立して動作

**承認ポイント**: 移設ファイルの動作確認

### Phase 4: MarginScout クリーンアップ
**実行内容**:
```bash
# git で削除履歴を記録しながら削除
git rm -r src/csv_integration/
git rm -r src/payload_builder/
git rm -r src/executor/
git rm -r src/api_integration/
git rm -r src/order_management/
git rm docs/PHASE3-7_*.md
git rm docs/EBAY_*.md
git commit -m "refactor: Move Listing features to separate eBay Listing App"

# README / requirements.txt 修正
vim README.md
vim requirements.txt
vim pyproject.toml
git add -A
git commit -m "docs: Update MarginScout as Research App only"
```
**確認項目**:
- [ ] MarginScout が Research App のみとして機能
- [ ] 不要な依存関係が削除された
- [ ] テストが全てパス

**承認ポイント**: MarginScout クリーンアップ後の動作確認

### Phase 5: 統合テスト
**実行内容**:
```bash
# MarginScout テスト
cd margin-scout
python -m pytest tests/ -v
# 期待: Research テストのみパス

# eBay Listing App テスト
cd ../margin-scout-listing-app
python -m pytest tests/ -v
# 期待: Listing テストのみパス

# CSV インターフェーステスト
# MarginScout が生成した research_results.csv が
# eBay Listing App で正しく読み込まれるか確認
```
**成功基準**:
- [ ] MarginScout テスト: 100% パス
- [ ] eBay Listing App テスト: 100% パス
- [ ] CSV インターフェーステスト: 成功
- [ ] ドキュメント矛盾なし

**承認ポイント**: 統合テスト結果の確認

---

## リスク管理

### 4.1 リスク評価マトリクス
| # | リスク | 確率 | 影響 | レベル | 対策 |
|---|---|---|---|---|---|
| 1 | git history 断絶 | 中 | 中 | 🟠 | フルコピー後、git filter で整理 |
| 2 | import パス断裂 | 高 | 高 | 🔴 | 事前に全パス依存関係を抽出 |
| 3 | CSV インターフェース不整合 | 中 | 高 | 🔴 | インターフェース定義を先に確定 |
| 4 | 共有ライブラリ管理 | 中 | 中 | 🟠 | 共有パッケージ化検討 |
| 5 | ファイル漏れ | 低 | 中 | 🟡 | 棚卸しマトリクスで完全確認 |
| 6 | ドキュメント同期ずれ | 中 | 低 | 🟡 | 移設後にドキュメント一括確認 |

### 4.2 High リスク対策
**リスク #2: import パス断裂**
**対策**:
```bash
# Phase 3 実行前に、全ての import 依存関係を抽出
grep -r "^from src\|^import src" src/ > import_dependencies.txt

# eBay Listing App 内でパスを修正
# 例: from src.payload_builder → from margin_scout_listing_app.payload_builder
```

**リスク #3: CSV インターフェース不整合**
**対策**:
```bash
# Phase 1 で CSV 仕様を確定
# research_results.csv の全カラムを明記
# eBay Listing App の期待カラムと一致確認
```

### 4.3 バックアップ戦略
```bash
# Phase 3 実行前
git tag backup-before-phase3-$(date +%Y%m%d_%H%M%S)
cp -r . ../margin-scout.backup

# Phase 4 実行前
git tag backup-before-phase4-$(date +%Y%m%d_%H%M%S)
cp -r . ../margin-scout.backup

# Phase 5 後（最終バックアップ）
git tag v1.0-after-separation-$(date +%Y%m%d_%H%M%S)
```

---

## ロールバック方針

### 5.1 各フェーズでのロールバック
**Phase 2 後のロールバック**
```bash
# eBay Listing App リポジトリを削除
rm -rf ../margin-scout-listing-app
# MarginScout は未修正のため何もしない
```
復旧時間: 5 分

**Phase 3 後のロールバック**
```bash
# eBay Listing App を修正版に再初期化
# MarginScout は未修正のため何もしない
```
復旧時間: 30 分

**Phase 4 後のロールバック**
```bash
# MarginScout を復元
git revert <phase4-commit-hash>
# または
git reset --hard backup-before-phase4
```
復旧時間: 1 時間

**Phase 5 後のロールバック**
```bash
# 両アプリとも復元
# MarginScout
cd margin-scout
git reset --hard v0-before-separation

# eBay Listing App
# （新規リポジトリのため不要）
```
復旧時間: 1-2 時間

---

## 成功基準

### 6.1 分離完了後の確認項目
```text
□ MarginScout (Research App)
  ├─ □ リサーチ機能が正常に動作
  ├─ □ research_results.csv が生成される
  ├─ □ listing_seed.csv が生成される
  ├─ □ テスト 100% パス
  ├─ □ eBay 関連コードが完全に削除
  └─ □ ドキュメントが最新

□ eBay Listing App
  ├─ □ CSV 取込が正常に動作
  ├─ □ Payload Builder が正常に動作
  ├─ □ Dry-run Executor が正常に動作
  ├─ □ OAuth & Live API が正常に動作
  ├─ □ テスト 100% パス
  └─ □ ドキュメントが最新

□ インターフェーステスト
  ├─ □ MarginScout CSV → eBay Listing App で正しく読込
  ├─ □ CSV フォーマットの互換性確認
  └─ □ データ完全性確認
```

---

## 承認フロー

### 7.1 承認ポイント
| # | フェーズ | 承認者 | 承認内容 | 期限 |
|---|---|---|---|---|
| 1 | Phase 0 | 👤 ユーザー | 分離計画書の確認 | 2026-06-14 |
| 2 | Phase 1 | 👤 ユーザー | スコープ確定の確認 | 2026-06-15 |
| 3 | Phase 2 | 👤 ユーザー | リポジトリ初期化の確認 | 2026-06-15 |
| 4 | Phase 3 | 👤 ユーザー | 移設ファイルの確認 | 2026-06-16 |
| 5 | Phase 4 | 👤 ユーザー | MarginScout クリーンアップの確認 | 2026-06-16 |
| 6 | Phase 5 | 👤 ユーザー | 統合テスト結果の確認 | 2026-06-17 |

### 7.2 承認前の チェックリスト
```text
Phase 0 承認前:
□ MIGRATION_PLAN.md (本ドキュメント) を確認
□ KEEP_MOVE_ARCHIVE_MATRIX.md を確認
□ MARGINSCOUT_SCOPE.md を確認
□ LISTING_APP_SCOPE.md を確認
□ README 修正案を確認
□ リスクと対策に同意
□ ロールバック方針に同意
```

**次ステップ**
- ✅ 本計画書の承認 ← 次はここ
- ⏳ KEEP_MOVE_ARCHIVE_MATRIX.md 確認
- ⏳ MARGINSCOUT_SCOPE.md 確認
- ⏳ LISTING_APP_SCOPE.md 確認
- ⏳ README 修正案確認
- ⏳ Phase 2 実行開始

---

## 付録
**A. 参考ドキュメント**
- `docs/PROJECT_ORIGIN.md` - プロジェクト背景
- `docs/PHASE2_RESEARCH_WORKFLOW.md` - リサーチワークフロー設計
- `docs/research_to_listing_mapping.md` - リサーチ → 出品マッピング

**B. 関連ファイル**
- `file_inventory.json` - 全ファイル一覧
- `migration_context.json` - 分離コンテキスト

**承認署名**:
```text
MarginScout 分離実行計画書 v1.0
作成日: 2026-06-14
承認日: _______________
承認者: _______________
```

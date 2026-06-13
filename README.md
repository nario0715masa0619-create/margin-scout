# MarginScout

**MarginScout は、eBay セラー向けの参考価格リサーチおよび CSV ベース出品支援プラットフォームです。**

MarginScout は、ERE Phase2 で確立した実装基盤・検証知見・一部設計思想を出発点として、新たに立ち上げたプロジェクトです。  
ERE Phase2 の有効な要素を継承しつつ、**リサーチ機能**と**出品機能**を分離した、より商品化を意識したプラットフォームとして再定義しています。

---

## 概要

MarginScout は、eBay 向けの商品リサーチおよび出品支援を、次の 2 層構造で扱うことを想定したプロジェクトです。

1. **リサーチ層**  
   参考価格や商品候補情報を収集・整理し、仕入れ判断や商品選定に使える CSV として出力する機能を担います。

2. **出品支援層**  
   MarginScout が出力した CSV **"も"** 取り込める、汎用 CSV インポート対応の eBay 出品支援機能を担います。

MarginScout は、**ワンクリックで一気通貫の自動転売を行うシステム**としては定義しません。  
あくまで、**リサーチ主導・CSV中心・ローカル画像管理前提の出品支援プラットフォーム**として設計します。

---

## プロジェクトの位置づけ

MarginScout は、**ERE Phase2 の単純な改名版ではなく、新規プロジェクト**です。

- **ERE Phase2** は、eBay 向け出品実行基盤として整理されていました
- **MarginScout** は、より広い商品化を前提とした **商品リサーチ + CSV連携型出品支援プラットフォーム** として再定義されます
- アーキテクチャ上、**リサーチ責務** と **出品責務** を意図的に分離します
- ブランド、ドキュメント、将来の拡張方針も独立させます

---

## コアコンセプト

MarginScout は、以下の原則に基づいて構成します。

- **参考価格リサーチを起点にする**
- **CSV を中核の連携フォーマットとする**
- **リサーチ機能と出品機能を分離する**
- **汎用 CSV インポートに対応する**
- **出品画像はローカル管理を前提とする**
- **dry-run を優先する安全設計を重視する**
- **実行履歴と監査可能性を重視する**

---

## ERE Phase2 との関係

MarginScout は、**ERE Phase2** で蓄積した設計知見・検証結果・一部実装思想をベースに開始した新規プロジェクトです。

### ERE Phase2
- eBay 向け出品実行基盤
- SKU ベースの出品制御
- ローカル画像管理
- dry-run 安全設計
- 実行監査ログ

### MarginScout
- 商品リサーチ主導のプラットフォーム
- CSV 出力可能なワークフロー基盤
- 汎用 CSV インポート対応の eBay 出品支援
- リサーチと出品を分離した構造
- 独立したブランド・ドキュメント・リポジトリ構成

MarginScout は ERE Phase2 を直接置き換えるものではありません。  
ERE Phase2 で有効性が確認された基盤要素を活かしつつ、別のプロダクトとして再構成していきます。

詳細は [docs/PROJECT_ORIGIN.md](docs/PROJECT_ORIGIN.md) を参照してください。

---

## 初期スコープ

MarginScout の初期スコープは、以下を含みます。

- プロジェクト定義とリポジトリ初期構成
- プロダクト方針とドキュメント整備
- リサーチワークフロー設計
- CSV 中心のデータ連携設計
- eBay 向け出品支援設計
- ローカル画像管理前提の出品運用設計
- 将来のモジュール分離を見据えた構造整理

---

## MarginScout が目指すもの

MarginScout は、将来的に次のようなプラットフォームへ発展することを想定しています。

- **商品候補の発見を支援するリサーチ基盤**
- **参考価格整理のためのワークフロー層**
- **CSV 出力可能な中間処理基盤**
- **汎用 CSV を受け入れられる eBay 出品支援基盤**
- **リサーチと出品の責務が分離されたモジュール型プラットフォーム**

---

## MarginScout が目指さないもの

MarginScout は、以下のようなものとしては定義しません。

- ワンクリック型の自動転売システム
- 完全自動の一気通貫 resale bot
- 任意の第三者マーケットプレイスをそのまま複製するシステム
- ローカル画像を不要とする出品システム
- ERE Phase2 の単純コピーや単純リネーム版

---

## ワークフロー思想

MarginScout は、**分離型ワークフロー**を前提に設計します。

### リサーチワークフロー
- 商品候補を見つける
- 参考価格を観測する
- 候補データを整理する
- CSV として出力する

### 出品ワークフロー
- 互換性のある CSV を取り込む
- 実行前にデータを検証する
- ローカル画像を紐づける
- eBay 出品用データを整形する
- dry-run を優先して確認する
- 実行履歴を追跡可能にする

この分離により、リサーチ結果を単一の出品経路に強く依存させず、柔軟な運用を可能にします。

---

## データと出品に関する基本原則

MarginScout は、以下の運用原則を採用します。

- CSV を主要なデータ交換フォーマットとして扱う
- 出品ワークフローは **MarginScout が出力した CSV** だけでなく、**他の互換 CSV** にも対応する
- 出品画像は **ローカル画像管理** を前提とする
- 出品前の確認・検証・監査可能性を重視する
- live 実行よりも前に **dry-run 可能な設計** を優先する

---

## 初期ディレクトリ構成

```text
margin-scout/
├─ README.md
├─ .gitignore
├─ docs/
│  ├─ PROJECT_ORIGIN.md
│  └─ CONFIGURATION.md
├─ src/
│  ├─ config_loader.py
│  └─ .gitkeep
├─ tests/
│  └─ .gitkeep
└─ data/
   └─ .gitkeep
```

初期段階では、意図的に最小構成で開始し、必要に応じて段階的に拡張していきます。

---

## セットアップと設定

### クイックスタート

1. **リポジトリをクローン**
   ```bash
   git clone https://github.com/nario0715masa0619-create/margin-scout.git
   cd margin-scout
   ```

2. **ユーザー設定ディレクトリを作成**
   ```powershell
   # Windows の場合
   Test-Path C:\Users\$env:USERNAME\.marginscount
   ```

3. **環境変数を設定**
   ```powershell
   # テンプレートをコピー
   Copy-Item .env.example C:\Users\$env:USERNAME\.marginscount\.env
   
   # API キーを編集
   notepad C:\Users\$env:USERNAME\.marginscount\.env
   ```

4. **設定を検証**
   ```bash
   python verify_config.py
   ```

### 設定の詳細

詳細は [docs/CONFIGURATION.md](docs/CONFIGURATION.md) を参照してください。

**環境変数の保存場所:**
```
C:\Users\{ユーザ名}\.marginscount\.env
```

**eBay 連携に必要な環境変数:**
- `EBAY_SANDBOX_CLIENT_ID`
- `EBAY_SANDBOX_CLIENT_SECRET`
- `EBAY_APP_ID`

詳細な設定リファレンスは [docs/CONFIGURATION.md](docs/CONFIGURATION.md) を参照してください。

---

## 今後の開発予定

今後、以下のようなモジュールを段階的に追加していく想定です。

- リサーチデータ取込モジュール
- CSV 正規化レイヤー
- 出品準備モジュール
- ローカル画像検証モジュール
- eBay 出品用ペイロード整形ユーティリティ
- 実行監査ユーティリティ
- テストモジュール
- 運用ドキュメント

---

## 現在のステータス

**ステータス: プロジェクト初期立ち上げ段階**

MarginScout は、独立したリポジトリとプロダクト定義を確立するフェーズにあります。  
今後、設計を維持しながらモジュール単位で実装を拡張していきます。

---

## 開発メモ

- MarginScout は、ERE Phase2 から独立したリポジトリとして運用します
- ERE Phase2 は重要な技術的・概念的基盤として位置づけます
- MarginScout は以下の境界をより明確にしながら発展させます
  - リサーチ
  - CSV ワークフロー生成
  - 出品支援
  - 実行設計
  - ドキュメント

詳細なプロジェクト起源については [docs/PROJECT_ORIGIN.md](docs/PROJECT_ORIGIN.md) を参照してください。

---

## プロジェクト起源

MarginScout は、ERE Phase2 で蓄積した実装基盤と設計知見をベースに、新たなプロダクト方針で立ち上げられた新規プロジェクトです。  

詳細は [docs/PROJECT_ORIGIN.md](docs/PROJECT_ORIGIN.md) を参照してください。

---

## ライセンス

TBD

---

## メンテナー

TBD

---

**最終更新**: 2026-06-13  
**プロジェクトステータス**: Bootstrap Phase (Active Development)  
**リポジトリ**: https://github.com/nario0715masa0619-create/margin-scout


---

## 📋 Phase 2: リサーチワークフロー設計 (完了)

**ステータス**: 設計完了  
**完了日**: 2026-06-13

### 成果物

✅ docs/PHASE2_RESEARCH_WORKFLOW.md — リサーチワークフロー詳細設計  
✅ docs/RESEARCH_DATA_MODEL.md — リサーチデータモデル仕様  
✅ examples/research_sample.csv — サンプル CSV（リサーチ候補）  
✅ src/research_workflow/ — Python skeleton (research_data.py, research_processor.py)  

### 設計要点

**リサーチ責務**: データ収集 → 正規化 → ユーザー確認 → CSV 出力

**中間データ層 (Layer 構造)**:
- Layer 0: 生データ (Raw Data)
- Layer 1: 正規化データ (Normalized Data)
- Layer 2: リサーチ候補 (Research Candidate Data)
- Layer 3: 確認済みデータ (Confirmed Research Data)
- Layer 4: CSV 出力候補 (CSV-Ready Data)

**表モード / 裏モード分離**:
- 表: 手入力 CSV、eBay リスティング観測（公式ドキュメント記載）
- 裏: Amazon 観測、実店舗メモ（実装時のみ言及）

**リサーチ終了点**: CSV 出力まで（出品実行は別フェーズ）

---


---

## 📋 Phase 3: CSVデータ連携設計 (完了)

**ステータス**: 設計完了  
**完了日**: 2026-06-13

### 成果物

✅ docs/PHASE3_CSV_INTEGRATION.md — CSV連携方針・責務分離・変換戦略  
✅ docs/LISTING_DATA_MODEL.md — Listing層データモデル定義  
✅ examples/listing_input_sample.csv — サンプル（Research→Listing変換後）  
✅ examples/research_to_listing_mapping.md — 列マッピング対応表  
✅ src/csv_integration/ — Pythonスケルトン (validator, mapper, models)  

### 設計要点

**責務分離**:
- Phase 2 Research: 候補収集→正規化→CSV出力
- Phase 3 Listing: CSV取込→SKU付与→画像解決→Listing-Ready判定
- Phase 4 以降: eBay API連携・実出品

**データ層構造**:
- Layer 1: Validated & Normalized Record (CSV検証・正規化)
- Layer 2: Listing Preparation Record (SKU付与・画像解決)
- Layer 3: Listing-Ready Record (最終検証・監査確定)

**SKU戦略**: 自動採番 (MARGIN-YYYYMMDD-NNNN) + 追跡性確保 (candidate_id保持)

**画像戦略**: SKUベースディレクトリ解決 (data/images/{SKU}/)

**バリデーション**: 4段階 (Hard Error / Soft Warning / Pending Review / Skip)


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

---

## 📋 Phase 5: eBay Executor & Dry-Run Implementation Design
**Status**: ✅ Completed
**Date**: 2026-06-13

### Deliverables
- docs/PHASE5_EBAY_EXECUTOR.md – Overall executor design, workflow, readiness judgment, dry-run, audit
- docs/EBAY_PRICE_STRATEGY.md – Price calculation model (margin + fees)
- docs/EBAY_CATEGORY_MAPPING.md – Category resolution specification
- examples/price_strategy_sample.json – Sample price calculations
- examples/ebay_dry_run_sample.json – Sample dry-run outputs
- examples/execution_audit_log_sample.json – Sample audit trails
- examples/listing_to_payload_mapping.md – Field mapping reference
- src/executor/ – Skeleton code (price_calculator, category_resolver, executor, dry_run_executor)

### Key Design Decisions
- Price Formula: price = reference_price / (1 - margin% - fee%)
- Category Policy: Single category, leaf-node required, fallback to "Miscellaneous" if unresolved
- Readiness Levels: ready, pending_review, incomplete, rejected
- Dry-Run Design: Deterministic simulation without live API call
- Audit Trail: Full traceability with candidate_id, SKU, pricing, category, validation results

### Handoff to Phase 6
- Execution-ready payload (Layer 4)
- Audit trail (timestamp, pricing decision, category resolution, validation results)
- Mock response (for reference)
- Readiness level (ready / pending_review / incomplete / rejected)

Phase 6 Responsibility: Authenticate with live eBay API, submit payload, handle responses, update status.

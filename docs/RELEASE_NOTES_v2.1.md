# MarginScout v2.1

## リリース概要

MarginScout v2.1 は、日本国内の複数ソースから商品候補を取得し、eBay の参照市場データと照合することで、利益が見込める候補商品を抽出する **リサーチ専用ツール** です。

本リリースでは、MarginScout の責務を「単独で稼働するリサーチツール」として明確化し、仕様外機能を整理・削除しました。これにより、以下の中核機能に集中した構成となっています。

- 日本国内ソースからの商品候補取得
- eBay Browse API による参考価格取得
- 商品マッチング
- 利益計算
- CSV / JSON / JSONL 形式での結果出力

## 主な内容

### コア機能

**4つの対応ソースからの商品取得**
- Mercari
- Yahoo Flea Market
- Yahoo Auction
- Hardoff

**eBay Browse API 連携による参照市場検索**
- OAuth 2.0 認証（Sandbox / Live 両対応）
- 複数キーワードでの並行検索

**商品マッチング処理**
- Jaccard 類似度ベースの段階的マッチング（閾値 0.35）
- SequenceMatcher による補完的マッチング

**利益計算**
- eBay Final Value Fee (13.6% + $0.40) を含む正確な計算
- 国際送料 ($20) 自動計算
- 為替レート対応（デフォルト: 157.50 JPY/USD）

**監査ログを含む構造化出力**
- research_results.csv（利益候補リスト）
- research_summary.json（実行サマリー）
- research_audit_*.jsonl（監査ログ）

### スコープ整理

本リリースでは、MarginScout を **リサーチ専用アプリケーション** として再整理しています。

**対象外機能**
- 出品実行
- 在庫管理
- 注文管理
- メール通知
- 内蔵スケジューラ
- eBay Sell API 連携

## v2.1 における改善点

初期段階と比較して、取得・出力性能に大きな改善が見られました。

**成功率**
- Sandbox: 1.9% → Live: 25.0%（**約 13 倍向上**）

**検索ヒット率**
- 7.1% → 67.3%（**約 9.5 倍向上**）

**マッチング精度**
- 25.0% → 38.2%（**約 1.5 倍向上**）

**CSV 出力件数**
- 1件 → 13件（**13 倍向上**）

あわせて、以下の改善を実施しています。

- **日本語キーワード正規化**：pykakasi による日本語→ローマ字変換
- **クエリ最適化およびフォールバック処理**：複数段階のクエリ生成戦略
- **段階的マッチング調整**：完全一致→強い一致→中程度一致→シーケンスマッチの階層化
- **eBay 検索条件詳細化**：中古品・正評価出品者による絞込み
- **ドキュメント整理とスコープ整合**：仕様書と実装の完全一致

## 現在の位置づけ

MarginScout v2.1 は、

- ❌ 完成済みの運用システムではなく
- ❌ 継続的な本番常用を前提とした成熟製品でもなく
- ✅ **実運用テストに進める段階の、単独稼働可能なリサーチツール**

として位置づけられます。

今後は、以下の観点で継続的な改善が期待されます。

- カテゴリ別の成功率分析
- キーワード最適化
- マッチング精度向上
- 利益計算結果の検証

## 技術詳細

### 新規モジュール（Phase B+）
- `query_optimizer_advanced.py`：複数段階クエリ生成
- `product_matcher_advanced.py`：段階的マッチング
- `product_matcher_improved.py`：閾値緩和版マッチング
- `keyword_normalizer.py`：日本語→eBay 標準形正規化
- `csv_handler_advanced.py`：拡張 CSV 出力（利益フラグ・警告フラグ）
- `advanced_ebay_searcher.py`：検索条件詳細化

### 依存関係
- `pykakasi==2.2.1`：日本語→ローマ字変換

### E2E テスト結果
- 総入力: 52件
- CSV 出力: 13件
- 成功率: 25.0%
- 平均処理時間: 2.7秒/アイテム

## 補足

- MarginScout は、eBay を **参照市場** として利用します。
- 本リリースで使用する eBay API は **Browse API のみ** であり、出品や販売運用は行いません。
- 定期実行はユーザ側で cron / Task Scheduler を設定してください。本ツールは CLI 単体実行を前提としています。

## ドキュメント

- [README.md](https://github.com/nario0715masa0619-create/margin-scout/blob/main/README.md)：概要・使い方
- [DEPLOYMENT_GUIDE.md](https://github.com/nario0715masa0619-create/margin-scout/blob/main/docs/DEPLOYMENT_GUIDE.md)：環境構築
- [PHASE_B_PLUS_IMPROVEMENT_REPORT.md](https://github.com/nario0715masa0619-create/margin-scout/blob/main/docs/PHASE_B_PLUS_IMPROVEMENT_REPORT.md)：改善詳細
- [PRODUCTION_DEPLOYMENT_CHECKLIST.md](https://github.com/nario0715masa0619-create/margin-scout/blob/main/docs/PRODUCTION_DEPLOYMENT_CHECKLIST.md)：デプロイ前確認
- [PRODUCTION_OPERATIONS_GUIDE.md](https://github.com/nario0715masa0619-create/margin-scout/blob/main/docs/PRODUCTION_OPERATIONS_GUIDE.md)：本番運用ガイド

## リポジトリ

GitHub: https://github.com/nario0715masa0619-create/margin-scout

# MarginScout スコープ v2.0

**作成日**: 2026-06-15
**ステータス**: 思想・責務 全面再定義
**優先度**: 最高

---

## 一文定義

**MarginScout は、日本ならではの商品を中心に、仕入れ元の価格情報と eBay 上の参考価格・商品情報などの事実をもとに、爆益が狙える商品候補を見つけて出力するリサーチツールである。出品・在庫・注文・販売運用は扱わない。**

---

## 責務範囲（DO）

| # | 責務 | 詳細 | 実装状況 |
|---|---|---|---|
| 1 | 爆益候補の発掘 | 日本の仕入れ元から商品を探索 | ⏳ 実装予定 |
| 2 | 仕入れ価格取得 | 仕入れ元の商品情報・価格を記録 | ⏳ 実装予定 |
| 3 | eBay 参考価格取得 | Browse API で参考相場を検索 | ⏳ 実装予定 |
| 4 | 利益計算 | 仕入れ価格と eBay 参考価格から利益を推定 | ✅ 実装完了 |
| 5 | CSV 出力 | 爆益候補を CSV で出力 | ✅ 実装完了 |
| 6 | 監査ログ | 処理履歴を JSONL で記録 | ✅ 実装完了 |

---

## 非責務範囲（DO NOT）

| # | 非責務 | 理由 |
|---|---|---|
| 1 | 出品実行 | MarginScout はリサーチ専用 |
| 2 | eBay Sell API | 出品権限が必要（スコープ外） |
| 3 | 在庫同期 | 出品後の運用（スコープ外） |
| 4 | 注文管理 | 販売運用（スコープ外） |
| 5 | 仕入れ先評価 | 品質判定はユーザーが行う |
| 6 | 出品可否判定 | 最終決定はユーザーが行う |
| 7 | 販路決定 | eBay に限定されない |

---

## eBay との関係

### eBay は「参照市場」

eBay は**出品先ではなく、参考市場**として扱う。

- ✅ 商品情報取得
- ✅ 参考価格取得
- ✅ 需要参考
- ❌ 出品実行
- ❌ 在庫管理
- ❌ 注文処理

### 使用 API

- **Browse API**: 商品検索・商品詳細取得（✅ 使用）
- **Sell API**: 出品・在庫・注文（❌ 非使用）

---

## 仕入れ先ポリシー

### 探索対象（フリマ系を含む）

- Mercari（メルカリ）
- Yahoo Fleamarket
- Hardoff
- 2nd Street
- Rakuten
- Amazon 中古
- 地域のリユース店舗

### 探索対象外

- なし（すべて対象）

### 重要

仕入れ先を「公式 / フリマ」で区別しない。
「商品情報と価格がある場所」は全て探索対象。
品質判定はユーザーが行う。

---

## 出力仕様

### 出力ファイル

| ファイル | 用途 | 形式 |
|---|---|---|
| research_results.csv | 爆益候補一覧（詳細） | CSV |
| research_summary.json | 実行結果サマリー | JSON |
| research_audit_*.jsonl | 処理監査ログ | JSONL |

### research_results.csv の必須列

| 列 | 説明 |
|---|---|
| candidate_id | 候補識別子 |
| product_name | 正規化済み商品名 |
| source_channel | 仕入れ元 |
| source_url | 仕入れ元 URL |
| source_price | 仕入れ価格 |
| source_currency | 通貨 |
| reference_sale_price | eBay 参考価格 |
| reference_currency | 通貨 |
| estimated_profit | 推定利益 |
| profit_margin_percent | 推定利益率（%） |

---

## CLI インターフェース

```bash
python cli.py --category <category> --days <days> --min-sales <min_sales>
```

### パラメータ

| パラメータ | 説明 | デフォルト | 例 |
|---|---|---|---|
| `--category` | eBay カテゴリ | electronics | footwear, camera |
| `--days` | 売上実績の期間（日数） | 90 | 180 |
| `--min-sales` | 最小売上件数 | 2 | 5, 10 |
| `--output-dir` | 出力ディレクトリ | output | result |

## 今後の実装計画

### Phase 1: 基盤実装
- [ ] eBay Browse API 認証実装
- [ ] 仕入れ元の定義と初期実装
- [ ] 商品マッチング基本ロジック

### Phase 2: 探索機能拡張
- [ ] Mercari API / スクレイピング
- [ ] Yahoo Fleamarket 対応
- [ ] Rakuten 対応

### Phase 3: 精度向上
- [ ] 商品マッチング精度向上
- [ ] 偽陽性削減
- [ ] 大規模データセット検証

## 重要な確認事項

**この定義が最優先**

- 既存ドキュメント・実装との矛盾が見つかった場合、この定義を優先する
- 出品ツール的な責務は一切持たない
- eBay は参照市場である

MarginScout v2.0 – 思想を固定し、実装を開始する。

# MarginScout v2.0 再定義 – 最終報告書

**実施日**: 2026-06-15
**実施内容**: 思想・責務・仕様の全面再定義
**ステータス**: ✅ 完了

---

## 📌 実行サマリー

MarginScout の思想を「出品ツールの前処理」から「純粋なリサーチツール」に全面的に再定義しました。

- ✅ 思想の固定化
- ✅ 責務の明確化
- ✅ ドキュメントの統一
- ✅ 実装スコープの確定

---

## 1. MarginScout の最終一文定義

**「MarginScout は、日本ならではの商品を中心に、仕入れ元の価格情報と eBay 上の参考価格・商品情報などの事実をもとに、爆益が狙える商品候補を見つけて出力するリサーチツールである。出品・在庫・注文・販売運用は扱わない。」**

---

## 2. やること / やらないこと一覧

### ✅ MarginScout がやること

| # | 責務 | 詳細 |
|---|---|---|
| 1 | 爆益候補の発掘 | 日本の仕入れ元から商品を探索 |
| 2 | 仕入れ価格取得 | 商品情報・価格・URL・観測日時を記録 |
| 3 | eBay 参考価格取得 | Browse API で参考相場を検索 |
| 4 | 利益計算 | 仕入れ価格と eBay 参考価格から利益を推定 |
| 5 | CSV 出力 | 爆益候補を比較しやすい形式で出力 |
| 6 | 監査ログ | 処理履歴を JSONL で記録 |

### ❌ MarginScout がやらないこと

| # | 非責務 | 理由 |
|---|---|---|
| 1 | 出品実行 | リサーチ専用ツール |
| 2 | eBay Sell API 連携 | 出品権限が必要（スコープ外） |
| 3 | 在庫同期 | 出品後の運用（スコープ外） |
| 4 | 注文管理 | 販売運用（スコープ外） |
| 5 | 仕入れ先評価 | 品質判定はユーザーが行う |
| 6 | 出品可否判定 | 最終決定はユーザーが行う |
| 7 | 無在庫/有在庫推奨 | 運用判断はユーザーが行う |
| 8 | 販路の最終決定 | eBay に限定されない |

---

## 3. eBay API の使用範囲 / 非使用範囲

### ✅ 使用する API

| API | 用途 | 理由 |
|---|---|---|
| Buy / Browse API search | 商品検索 | 参考価格・商品情報取得 |
| Buy / Browse API getItem | 商品詳細取得 | 詳細情報取得 |

**認証方法**: OAuth 2.0 Application Token (Client Credentials)

### ❌ 使用しない API

| カテゴリ | 理由 |
|---|---|
| Sell Inventory API | 在庫管理はスコープ外 |
| Offer API | 出品作成はスコープ外 |
| Listing API | 出品管理はスコープ外 |
| Fulfillment API | 注文管理はスコープ外 |
| Order API | 注文取得はスコープ外 |
| Account API | セラーアカウント管理はスコープ外 |

---

## 4. 仕入れ先の扱い方針

### 仕入れ先は「評価対象」ではなく「探索対象」

MarginScout は仕入れ先を審査・格付けしません。

### 探索対象（フリマ系を含む）

- Mercari（メルカリ）
- Yahoo Fleamarket
- Hardoff
- 2nd Street
- Rakuten
- Amazon 中古
- その他すべての商品情報と価格がある場所

### 記録してよい情報

- 仕入れ元（channel）
- URL
- 価格
- 状態記述
- 観測日時

### やらないこと

- 公式店 / フリマの区別による排除
- 仕入れ先の信頼度スコアリング
- 安定度評価
- 主軸 / 補助ラベル付け

**重要**: フリマ系を最初から除外しない。商品情報と価格がある場所はすべて探索対象。

---

## 5. 出力 CSV の意味と項目一覧

### 出力の意味

出力は「最終意思決定」ではなく、「爆益候補一覧」。

MarginScout が出すもの:
- 「この商品は事実ベースで見ると利益が狙えそう」という候補データ

MarginScout が出さないもの:
- 出品命令
- 販売判断
- 仕入れ命令

### research_results.csv の項目一覧

| # | 項目 | 説明 | 例 |
|---|---|---|---|
| 1 | candidate_id | 候補一意識別子 | RESEARCH-20260615-0001 |
| 2 | product_name | 正規化済み商品名 | Sony Headphones |
| 3 | source_channel | 仕入れ元 | mercari, hardoff など |
| 4 | source_url | 仕入れ元 URL | https://mercari.com/item/xxx |
| 5 | source_price | 仕入れ価格 | 5000 |
| 6 | source_currency | 通貨 | JPY |
| 7 | condition_text | 商品状態記述 | Good condition |
| 8 | observed_at | 観測日時 | 2026-06-15T10:00:00 |
| 9 | reference_market | 参考市場 | ebay |
| 10 | reference_item_id | eBay item ID | 123456789 |
| 11 | reference_item_url | eBay 商品 URL | https://ebay.com/itm/xxx |
| 12 | reference_sale_price | eBay 参考販売価格 | 60.00 |
| 13 | reference_currency | 通貨 | USD |
| 14 | estimated_profit | 推定利益 | 35.00 |
| 15 | profit_margin_percent | 推定利益率（%） | 37.5 |
| 16 | notes | 摘要 | 自由記述 |

---

## 6. 修正したドキュメント一覧

| # | ファイル | 変更内容 |
|---|---|---|
| 1 | README.md | リサーチ専用ツールとしての説明に刷新 |
| 2 | MARGINSCOUT_SCOPE.md | v2.0 として責務範囲を再定義 |
| 3 | MARGINSCOUT_REDEFINED.md | 新規作成：思想・責務の最終定義 |
| 4 | API_SCOPE_DEFINITION.md | 新規作成：eBay API 使用範囲の明記 |
| 5 | RESEARCH_DATA_MODEL_V2.md | 新規作成：最小化したデータモデル |
| 6 | MARGINSCOUT_SCOPE_v1_ARCHIVED.md | v1 をアーカイブ（参考用） |

---

## 7. 修正・追加した実装ファイル一覧

### 現状

```text
src/research_workflow/ 
├── __init__.py (既存) 
├── research_data.py (既存) 
├── research_processor.py (既存、v2.0 思想は反映) 
├── normalizer.py (既存) 
├── category_mapper.py (既存) 
├── price_analyzer.py (既存) 
├── profit_evaluator.py (既存) 
├── csv_handler.py (既存) 
├── audit_logger.py (既存) 
└── cli.py (既存、プロジェクトルート)
```

### 実装上の注意

- **出品ツール的コード**: 既に除外済み（payload_builder, executor, Sell API など）
- **Browse API**: 実装予定（未実装）
- **仕入れ元スクレイピング**: 実装予定（未実装）

---

## 8. 既存設計から削除・分離した責務一覧

| # | 削除・分離した責務 | 理由 | 状態 |
|---|---|---|---|
| 1 | payload_builder | eBay Listing App 責務 | ✅ 既に分離（別リポジトリ） |
| 2 | executor（dry-run / live） | eBay Listing App 責務 | ✅ 既に分離（別リポジトリ） |
| 3 | api_integration（Sell系） | eBay Listing App 責務 | ✅ 既に分離（別リポジトリ） |
| 4 | order_management | eBay Listing App 責務 | ✅ 既に分離（別リポジトリ） |
| 5 | inventory_sync | eBay Listing App 責務 | ✅ 既に分離（別リポジトリ） |
| 6 | 仕入れ先信頼度評価 | 運用判断（ユーザー責務） | ✅ 非スコープ化 |
| 7 | 出品可否自動判定 | 運用判断（ユーザー責務） | ✅ 非スコープ化 |

---

## 9. 今回の思想に照らした実装上の注意点

### 必ず守ること

1. **eBay Browse API のみ使用**
   - Sell API は一切実装しない
   - 参考価格取得に徹する

2. **フリマ系を探索対象に含める**
   - Mercari, Yahoo Fleamarket など
   - 「商品情報と価格がある場所」はすべて対象

3. **出力は候補一覧**
   - 出品命令ではない
   - 品質判定・運用指示は入れない

4. **仕入れ先を評価しない**
   - チャネル名は記録するが、良し悪しは判定しない
   - スコアリング・格付けは実装しない

5. **認証は最小限**
   - Application Token のみ
   - Seller アカウント認証は不要

### 避けるべき実装

- ❌ OAuth の Sell フロー
- ❌ 仕入れ先スコアリング
- ❌ 出品判定アルゴリズム
- ❌ 無在庫/有在庫推奨ロジック
- ❌ eBay Sell API 統合

---

## 10. 未解決事項一覧

| # | 項目 | 状態 |
|---|---|---|
| 1 | eBay Browse API の実装 | ⏳ 実装予定 |
| 2 | Mercari スクレイピング/API 統合 | ⏳ 実装予定 |
| 3 | Yahoo Fleamarket 対応 | ⏳ 実装予定 |
| 4 | 商品マッチング精度向上 | ⏳ 実装予定 |
| 5 | 大規模データセット検証 | ⏳ テスト予定 |

---

## 総括

### 達成したこと

✅ MarginScout の思想を「リサーチ専用ツール」に統一
✅ 責務境界を明確化
✅ eBay API スコープを限定（Browse のみ）
✅ 仕入れ先ポリシーを柔軟化（フリマ系を含む）
✅ ドキュメントを全面刷新
✅ 実装は既に責務外コードなし

### 次のステップ

1. **eBay Browse API 実装** – 参考価格取得
2. **仕入れ元スクレイピング** – Mercari, Yahoo Fleamarket など
3. **商品マッチング** – 仕入れ元と eBay の商品を対応付け
4. **大規模テスト** – 実運用データでの検証

---

**MarginScout v2.0 – 思想固定、実装開始の準備完了。** ✅

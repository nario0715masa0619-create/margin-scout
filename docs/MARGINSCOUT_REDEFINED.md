# MarginScout - 最終定義 v2.0

**作成日**: 2026-06-15
**ステータス**: 思想・責務・仕様 全面再定義
**優先度**: 最高（これ以降の全設計はこの定義に従う）

---

## 一文定義

**MarginScout は、日本ならではの商品を中心に、仕入れ元の価格情報と eBay 上の参考価格・商品情報などの事実をもとに、爆益が狙える商品候補を見つけて出力するリサーチツールである。出品・在庫・注文・販売運用は扱わない。**

---

## MarginScout の責務（DO）

MarginScout がやるべきことは、以下に限定する。

1. **爆益候補の発掘**
   - 日本ならではの商品や、価格差が大きく利益が狙えそうな商品候補を見つける

2. **仕入れ側の事実取得**
   - 商品名、価格、状態、URL、取得日時などを記録
   - フリマアプリ、リユース店舗、ショッピングサイトなど、あらゆる仕入れ元を対象とする

3. **eBay 参照市場の情報取得**
   - eBay Browse API を用いて商品情報・参考価格を取得
   - あくまで「参考情報」として扱う

4. **利益計算**
   - 仕入れ価格と eBay 参考価格の差から利益を推定
   - 手数料・送料見込みを含めた簡潔な計算

5. **爆益候補の出力**
   - CSV 形式で候補を比較しやすく出力
   - 利益が大きい順、または条件に合う順で提示

---

## MarginScout の非責務（DO NOT）

以下は MarginScout の責務外である。やらない。

**出品・販売運用系:**
- 出品実行
- eBay Sell API 連携
- ペイロード生成
- Offer 作成・Publish
- 在庫管理
- 注文管理
- Fulfillment

**運用判断系:**
- 仕入れ先の信頼性評価
- 仕入れ先の安定度スコアリング
- 在庫再現性の担保
- 無在庫 / 有在庫の推奨
- 出品可否の自動判定
- 販路の最終決定

**認証・基盤系:**
- 売り手アカウント認証
- OAuth の Sell 系フロー
- セラーセントラル連携

---

## eBay との関係

### eBay は「参照市場」

eBay を「出品実行先」ではなく、「参考市場」として扱う。

eBay から取得する情報:
- 商品の参考価格
- 商品情報（説明、状態など）
- 需要の参考

eBay では実行しないこと:
- 出品
- 在庫管理
- 注文処理

### eBay API の使用範囲

**必要（使用対象）:**
- Buy / Browse API の search
- Buy / Browse API の getItem
- リサーチ用途の最小限の認証

**不要（非使用対象）:**
- Sell Inventory API
- Offer API
- Fulfillment API
- Account API
- Order API
- すべての出品実行 API

---

## 仕入れ先ポリシー

### 仕入れ先は「評価対象」ではなく「探索対象」

仕入れ先を審査・格付け・保証しない。

保持してよい情報:
- 仕入れ元（Mercari, Hardoff, Rakuten など）
- URL
- 価格
- 状態記述
- 観測日時

やらないこと:
- 公式店だから安全、フリマだから危険、などの判定
- 仕入れ先の主軸・補助ラベル付け
- 信頼度スコアリング

### フリマ系を探索対象から除外しない

- Mercari, Yahoo Fleamarket, Hardoff, 2nd Street など
- すべての商品情報と価格がある場所を探索対象とする
- 仕入れ可能性の判定はユーザーが行う

---

## 出力の意味

出力は「最終意思決定」ではなく、「爆益候補一覧」である。

MarginScout が出すものは:
- 「この商品は事実ベースで見ると利益が狙えそう」
- という候補データ

MarginScout が出すもの ではない:
- 出品命令
- 販売判断
- 仕入れ命令

---

## 必須出力項目

### research_results.csv

必須項目:
| 項目 | 説明 |
|---|---|
| candidate_id | 候補一意識別子 |
| product_name | 正規化済み商品名 |
| source_channel | 仕入れ元（mercari, hardoff など） |
| source_url | 仕入れ元 URL |
| source_price | 仕入れ価格 |
| source_currency | 通貨 |
| observed_at | 観測日時 |
| reference_market | 参考市場（eBay） |
| reference_item_url | 参考商品 URL |
| reference_sale_price | 参考販売価格 |
| reference_currency | 通貨 |
| estimated_profit | 推定利益 |
| profit_margin_percent | 推定利益率（%） |
| notes | 摘要 |

可選項目:
- brand, model_number, category, condition_text, shipping_estimate, fee_estimate

---

## 実装スコープ

### 実装対象

- 商品候補取得
- 商品情報正規化
- 仕入れ価格取得
- 状態記述取得
- eBay Browse API search / getItem
- eBay 参考価格取得
- 利益計算
- CSV 出力
- 監査ログ / 実行ログ

### 実装対象外

- eBay Sell API
- 出品ペイロード生成
- 在庫同期
- 注文ポーリング
- OAuth Sell系フロー
- inventory / order / fulfillment 周辺
- eBay Listing App 側責務全般

---

## 最終確認

この定義に基づき、以下を確認する:

- [ ] MarginScout は Research App である
- [ ] eBay は参照市場である
- [ ] Browse API のみを使用する
- [ ] Sell API は使用しない
- [ ] 出力は候補一覧である
- [ ] 仕入れ先評価をしない
- [ ] フリマ系を除外しない
- [ ] 出品実行責務を持たない

---

**この定義が MarginScout の最高位ドキュメントとなる。**
**以降のすべての設計・実装はこれに準拠する。**

# MarginScout v2.1

**eBay をターゲット市場とした自動リサーチツール**

> 日本国内の複数プラットフォーム（Mercari, Yahoo Flea Market, Yahoo Auction, Hardoff）から商品候補を自動抽出し、eBay Browse API を使用して参考価格・商品情報を取得。利益計算を自動実行し、CSV ファイルで結果出力するリサーチツール。

---

## ✨ 主な特徴

- **多ソース対応**: Mercari, Yahoo Flea Market, Yahoo Auction, Hardoff から同時検索
- **eBay Live API 統合**: OAuth 2.0 で認証、参考市場価格を自動取得
- **自動マッチング**: Jaccard 類似度 + SequenceMatcher で柔軟に商品マッチング
- **利益自動計算**: eBay 手数料（FVF 13.6% + $0.40）+ 国際送料（$20）を含む正確な利益計算
- **日本語対応**: 日本語キーワード → eBay 検索向け英語自動変換（pykakasi）
- **CSV/JSONL ログ出力**: 結果を CSV・JSON で記録、監査ログも自動生成

---

## 📊 v2.1 パフォーマンス

| 指標 | 値 |
|------|-----|
| **CSV 出力成功率** | 25.0% (13/52) |
| **eBay 検索ヒット率** | 67.3% (37/52) |
| **マッチング成功率** | 38.2% (13/34) |
| **平均処理時間** | 2.7 秒/アイテム |
| **Live API 対応** | ✅ 完全対応 |

> **初期版との比較**: Sandbox 1.9% → Live 改善後 25.0%（**約 13 倍向上**）

---

## 🚀 インストール

### 前提条件
- Python 3.11 以上
- eBay Developer アカウント（Live API クレデンシャル取得済み）
- インターネット接続

### セットアップ手順

```bash
# 1. リポジトリクローン
git clone https://github.com/nario0715masa0619-create/margin-scout.git
cd margin-scout

# 2. 依存パッケージインストール
pip install -r requirements.txt

# 3. 環境変数設定
# ~/.marginscount/.env または ./margin-scout/.env に以下を記載:
cat > ~/.marginscount/.env << 'EOF'
EBAY_ENV=live
EBAY_CLIENT_ID=your_production_client_id
EBAY_CLIENT_SECRET=your_production_client_secret
EXCHANGE_RATE_JPY=157.50
EBAY_REQUEST_TIMEOUT=30
EBAY_MAX_RETRIES=3
EOF

# 4. 実行確認
python cli.py --category electronics --days 90 --min-sales 2
```

## 💻 利用方法

### UI から実行（推奨）
```bash
cd margin-scout-ui
npm run dev
```
ブラウザで http://localhost:5173 を開いて操作。

### CLI から実行
```bash
python cli.py --input-csv candidates.csv --output-dir ./output
```
詳細は `python cli.py --help` または `docs/CLI_USAGE.md` を参照。

### ヘルプ表示
```bash
python cli.py --help
```

### 出力ファイル
```text
output_operational_test/
├── research_results.csv        # 利益候補リスト (13列)
├── research_summary.json       # 実行サマリー
└── logs/
    ├── research_audit_*.jsonl  # 監査ログ（アイテム詳細）
    └── error_*.log             # エラーログ
```

### CSV カラム説明
| カラム | 説明 |
|---|---|
| candidate_id | 候補 ID |
| product_name | 商品名 |
| source_channel | 仕入れ元 (mercari / yahoo_flea / yahoo_auction / hardoff) |
| source_price_jpy | 仕入れ価格 (JPY) |
| source_url | 仕入れ元 URL |
| condition_text | 商品状態 |
| ebay_title | eBay 商品名 |
| ebay_price_usd | eBay 参考価格 (USD) |
| ebay_item_id | eBay アイテム ID |
| profit_jpy | 利益額 (JPY) |
| profit_margin_pct | 利益率 (%) |
| match_score | マッチングスコア (0.0～1.0) |
| status | ステータス (success / failed) |

## 💰 利益計算式
```text
eBay 参考価格 (USD) × 為替レート (157.50 JPY/USD)
  - eBay 手数料 (FVF 13.6% + $0.40)
  - 国際送料 ($20)
  - 仕入れ価格 (JPY)
= 利益額 (JPY)
```
例: 仕入れ ¥25,300、eBay 価格 $98.00

```text
$98.00 × 157.50 = ¥15,435
- eBay FVF (13.6% + $0.40) = -¥2,165.58
- 送料 ($20) = -¥3,150
- 仕入れ = -¥25,300
= 利益 -¥15,180 (赤字)
```

## 🔧 トラブルシューティング
### 401 Unauthorized エラー
**原因**: eBay クレデンシャルが無効
**対策**: `~/.marginscount/.env` の EBAY_CLIENT_ID/SECRET を確認

### eBay 検索結果 0 件
**原因**: キーワードが eBay に存在しない、または条件が厳しい
**対策**: 
  1. キーワードを簡潔に (例: "Nikon D850" → "D850")
  2. 仕入れ元でキーワード確認
  3. `docs/KEYWORD_NORMALIZATION.md` 参照

### マッチング失敗
**原因**: 日本語商品の eBay 名と大きく異なる
**対策**: 
  1. Jaccard 類似度を確認 (CSV の match_score)
  2. match_score < 0.35 は除外される
  3. `docs/MATCHING_ALGORITHM.md` 参照

### 利益率が異常に高い/低い
**原因**: 為替レート設定、送料設定の違い
**対策**: `~/.marginscount/.env` の EXCHANGE_RATE_JPY を確認
デフォルト: 157.50 JPY/USD

## 📈 Phase B+ 改善詳細
v2.1 では以下の改善を実施しました：

- **クエリ最適化強化** → eBay ヒット率 7% → 67%
- **マッチング精度向上** → 段階的マッチング・閾値緩和
- **日本語キーワード正規化** → pykakasi による自動変換
- **eBay 検索条件詳細化** → 中古品・正評価セラーに絞込み
- **CSV 出力ロジック改善** → 利益フラグ・警告フラグ追加

詳細は `docs/PHASE_B_PLUS_IMPROVEMENT_REPORT.md` を参照。

## 📚 ドキュメント
- `DEPLOYMENT_GUIDE.md` - 環境構築ガイド
- `PHASE_B_PLUS_IMPROVEMENT_REPORT.md` - v2.1 改善ログ
- `MARGINSCOUT_REDEFINED.md` - 仕様書
- `MARGINSCOUT_SCOPE.md` - スコープ定義

## 📄 ライセンス
MIT License

## 👨‍💻 開発
- 初版: 2026-01 (Phase A～D)
- v2.0: 2026-03 (eBay Browse API 本体実装)
- v2.1: 2026-06-15 (Phase B+ 精度向上)
- 最終更新: 2026-06-15 ステータス: ✅ Production Ready

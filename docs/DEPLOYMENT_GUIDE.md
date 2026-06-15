# MarginScout v2.0 – デプロイメント・運用ガイド

## 概要

MarginScout は **リサーチ専用ツール** です。1 回の実行で以下を行います：

- 仕入れ元（Mercari, Yahoo Flea, Yahoo Auction, Hardoff）から商品候補を取得
- eBay Browse API で参考価格を照合
- 商品マッチングと利益計算
- CSV/JSONL ログを出力

## 前提条件

- Python 3.11+
- eBay Browse API クレデンシャル（Sandbox または Live）
- インターネット接続

## インストール

```bash
git clone https://github.com/nario0715masa0619-create/margin-scout.git
cd margin-scout
pip install -r requirements.txt
```

## 環境変数設定
.env ファイルを以下のいずれかの場所に配置：

推奨（ユーザーホーム）：
```bash
~/.marginscount/.env
```

またはプロジェクトルート：
```bash
./margin-scout/.env
```

## 設定内容
```env
# eBay Browse API (Sandbox テスト用)
EBAY_BROWSE_CLIENT_ID=your_sandbox_client_id
EBAY_BROWSE_CLIENT_SECRET=your_sandbox_client_secret
EBAY_API_MODE=sandbox

# または Live 環境（参照市場取得用）
# EBAY_API_MODE=live
# EBAY_BROWSE_CLIENT_ID=your_live_client_id
# EBAY_BROWSE_CLIENT_SECRET=your_live_client_secret

# Exchange rate
EXCHANGE_RATE_JPY=157.50
```

## 実行方法
CLI での単一実行
```bash
python cli.py --category electronics --days 90 --min-sales 2
```
パラメータ：

- `--category`: 検索カテゴリ（electronics, camera, games, fashion, hobby）
- `--days`: 検索期間（日数）
- `--min-sales`: 最小販売数

## 出力ファイル
実行後、output/ ディレクトリに以下が生成されます：

- `research_results.csv` – 候補リスト
- `research_summary.json` – 実行サマリー
- `logs/research_audit_*.jsonl` – 監査ログ

## 出力フォーマット
`research_results.csv`

| カラム | 説明 |
| --- | --- |
| candidate_id | ユニーク ID |
| product_name | 商品名 |
| source_channel | 仕入れ元 |
| source_url | 仕入れ元の URL |
| source_price | 仕入れ価格（JPY） |
| reference_sale_price | eBay 参考価格（USD） |
| condition_text | 商品状態 |
| estimated_profit | 推定利益（JPY） |
| profit_margin_pct | 利益率（%） |

## 利益計算ロジック
利益 = eBay 売却額（JPY）- eBay 手数料 - 国際送料 - 仕入れ価格

固定費用：

- eBay Final Value Fee: 13.6% + $0.40
- 国際送料（Japan Post EMS）: $20 USD
- 梱包費: ¥0（ユーザー側で調達）
- 為替レート： 1 USD = 157.50 JPY（.env で変更可）

## トラブルシューティング
**401 Unauthorized**
eBay Browse API クレデンシャルが無効です。.env を確認してください。

```bash
python -c "from src.ebay_integration.auth_handler import EbayAuthHandler; auth = EbayAuthHandler(); print(auth.get_token()[:30] + '...' if auth.get_token() else 'Error')"
```

**タイムアウト**
ネットワーク接続を確認するか、タイムアウト値を調整してください（`src/source_adapters/config_adapters.py` の `API_REQUEST_TIMEOUT_SECONDS`）。

**マッチング失敗（Match score too low）**
商品名が曖昧だと、eBay 側と一致しない場合があります。キーワードを明確にしてください。

---
最終更新： 2026-06-15
バージョン： v2.0.0
ライセンス： MIT

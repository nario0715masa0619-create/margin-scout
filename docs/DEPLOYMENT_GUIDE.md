# MarginScout v2.0 - 運用ガイド

## 前提条件
- Python 3.11+
- eBay Browse API クレデンシャル
- インターネット接続

## インストール
```bash
git clone https://github.com/nario0715masa0619-create/margin-scout.git
cd margin-scout
pip install -r requirements.txt
```

## 環境変数設定
### .env ファイル配置
```bash
~/.marginscount/.env
```

### Sandbox 設定（テスト用）
```env
EBAY_ENV=sandbox
EBAY_CLIENT_ID=Masakazu-MarketAn-SBX-xxxxx
EBAY_CLIENT_SECRET=SBX-xxxxx
EXCHANGE_RATE_JPY=157.50
```

### Live 設定（本番用）
```env
EBAY_ENV=live
EBAY_CLIENT_ID=your_live_client_id
EBAY_CLIENT_SECRET=your_live_client_secret
EXCHANGE_RATE_JPY=157.50
```

## 実行方法

### UI から実行（推奨）
```bash
cd margin-scout-ui
npm run dev
```
ブラウザで http://localhost:5173 を開いて操作。

### 単一実行（CLI）
```bash
python cli.py --category electronics --days 90 --min-sales 2
```
詳細は `python cli.py --help` または `docs/CLI_USAGE.md` を参照。

### 出力ファイル確認
```bash
# CSV を確認
cat output/research_results.csv

# JSON サマリーを確認
cat output/research_summary.json

# 監査ログを確認
tail -f logs/research_audit_*.jsonl
```

## トラブルシューティング
### 401 Unauthorized
.env 確認：
```bash
grep EBAY_ENV ~/.marginscount/.env
```

### eBay 検索が 0 件
- Sandbox：データが限定的（既知の制限）
- Live：クエリを見直し

### マッチング失敗
キーワードをより明確にしてください

## Sandbox → Live への切り替え
### ステップ 1: クレデンシャル取得
https://developer.ebay.com で Live API クレデンシャルを申請

### ステップ 2: .env を更新
```bash
nano ~/.marginscount/.env
# EBAY_ENV=live に変更
# EBAY_CLIENT_ID / EBAY_CLIENT_SECRET を Live 用に変更
```

### ステップ 3: 確認
```bash
python test_operational_multicat_nonmock.py
```

### ステップ 4: ロールバック（問題発生時）
```bash
cp ~/.marginscount/.env.sandbox_backup ~/.marginscount/.env
```

## MarginScout の責務
✅ 仕入れ元から商品取得
✅ eBay Browse API で参考価格取得
✅ 商品マッチング
✅ 利益計算
✅ CSV/JSONL 出力

❌ メール通知
❌ スケジューラー
❌ eBay 出品（Sell API）
❌ 在庫管理

最終更新： 2026-06-15

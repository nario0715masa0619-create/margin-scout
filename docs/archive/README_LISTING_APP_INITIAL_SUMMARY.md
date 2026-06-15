# eBay Listing App

**eBay 自動出品・在庫管理エンジン** – MarginScout リサーチ結果を eBay に自動出品

![Status](https://img.shields.io/badge/Status-Listing%20Phase%203--7-blue)
![Python](https://img.shields.io/badge/Python-3.11+-green)

---

## 概要
**eBay Listing App** は、MarginScout が出力したリサーチ結果 CSV を eBay へ自動出品し、在庫・注文を一元管理するアプリケーションです。

- 📤 **自動出品**: CSV から eBay リスティングを自動生成・公開
- 🔄 **在庫同期**: MarginScout データと eBay 在庫をリアルタイム同期
- 📥 **注文管理**: eBay 受注を自動ポーリング・処理
- 🧪 **Dry-run テスト**: 本番前に動作検証

---

## クイックスタート
### 1. インストール
```bash
git clone https://github.com/user/ebay-listing-app.git
cd ebay-listing-app
pip install -r requirements.txt
```

### 2. 設定
```bash
cp .env.example .env
# .env に eBay OAuth 情報を設定
# EBAY_CLIENT_ID=...
# EBAY_CLIENT_SECRET=...
# EBAY_REFRESH_TOKEN=...
```

### 3. 実行
```bash
# Dry-run テスト
python -m src.executor.dry_run_executor listing_seed.csv

# 本番実行
python -m src.executor.live_executor listing_seed.csv
```

### 4. 出力
- `listing_execution_YYYYMMDD_HHMMSS.log` – 出品実行ログ
- `inventory_sync_YYYYMMDD_HHMMSS.log` – 在庫同期ログ
- `order_poll_YYYYMMDD_HHMMSS.log` – 注文ポーリングログ

---

## 主な機能
| 機能 | 説明 |
|---|---|
| CSV Integration | listing_seed.csv 読込・検証 |
| Payload Builder | eBay API ペイロード自動生成 |
| Dry-run Executor | Mock API でのテスト実行 |
| Live API Integration | eBay Live API への連携 |
| Inventory Sync | 在庫リアルタイム同期 |
| Order Management | 注文自動ポーリング・処理 |

---

## アーキテクチャ
```text
listing_seed.csv (MarginScout)
         ↓
  [eBay Listing App]
  Phase 3: CSV Integration
  Phase 4: Payload Builder
  Phase 5: Dry-run Executor
  Phase 6: OAuth & Live API
  Phase 7: Inventory Sync & Order Management
         ↓
eBay Live Account
  + リスティング作成
  + 在庫管理
  + 注文受信
```

---

## ドキュメント
- `LISTING_APP_SCOPE.md` – スコープ定義
- `PHASE3_CSV_INTEGRATION.md`
- `PHASE6_EBAY_API_INTEGRATION.md`
- `PHASE7_INVENTORY_SYNC_AND_ORDER_MANAGEMENT.md`
- `EBAY_OAUTH_FLOW.md`

---

## スコープ
### ✅ eBay Listing App が責務を取る
- CSV 取込・検証
- eBay Payload Builder
- OAuth 認証
- Live API 連携
- 在庫同期
- 注文管理

### ❌ eBay Listing App は責務を取らない
- 商品リサーチ
- 価格分析
- **→ これらは MarginScout で実装**

---

## MarginScout（別リポジトリ）
商品候補をリサーチし、CSV で出力します。eBay Listing App はこの CSV を入力として受け取ります。

- リポジトリ: `margin-scout`
- スコープ: `MARGINSCOUT_SCOPE.md` 参照

---

## テスト
```bash
# Unit テスト
pytest tests/ -v

# Dry-run テスト
python -m src.executor.dry_run_executor examples/listing_seed_sample.csv

# カバレッジ
pytest tests/ --cov=src
```

---

## 構成ファイル
- `.env` – eBay OAuth 情報
- `requirements.txt` – Python 依存ライブラリ
- `setup.py` – パッケージ設定

---

## セキュリティ
- OAuth トークンは `.env` に保存（Git 追跡外）
- ログファイルに機密情報を記録しない
- API レスポンスから PII をフィルタリング

---

## ライセンス
MIT License

## 関連リポジトリ
- MarginScout – リサーチエンジン
- eBay Listing App v1.0 – Listing Phase 3-7 (計画中)

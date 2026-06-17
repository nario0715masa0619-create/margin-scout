# MarginScout SaaS - Heroku デプロイメント手順書

**バージョン**: 1.0  
**作成日**: 2026-06-16

## ⚠️ スコープ明記

MarginScout は SaaS 化後もリサーチツールであり、Sell API / 出品 / 在庫 / 注文管理はスコープ外です。

---

## 1. 前提条件

✅ Heroku アカウント作成 
✅ Heroku CLI インストール 
✅ Git インストール 
✅ PostgreSQL ローカル接続確認

---

## 2. Heroku アプリ作成

### 2.1 新規アプリ作成

```bash
# ログイン
heroku login

# アプリ作成
heroku create margin-scout-api

# 確認
heroku apps
```

### 2.2 環境設定
```bash
# 環境変数設定
heroku config:set \
  SECRET_KEY="your-secret-key" \
  EBAY_ENV="live" \
  EBAY_CLIENT_ID="your-client-id" \
  EBAY_CLIENT_SECRET="your-secret" \
  STRIPE_API_KEY="your-stripe-key" \
  STRIPE_WEBHOOK_SECRET="your-webhook-secret" \
  DATABASE_URL="postgres://..." \
  DEBUG="false"

# 確認
heroku config
```

---

## 3. アプリコード準備

### 3.1 Procfile 作成
```text
# Procfile (プロジェクトルート)

web: gunicorn app.main:app --workers 3 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --timeout 120

release: alembic upgrade head
```

### 3.2 runtime.txt 作成
```text
python-3.10.12
```

### 3.3 requirements.txt 確認
```text
fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
pydantic==2.5.0
python-jose==3.3.0
passlib==1.7.4
bcrypt==4.1.1
stripe==7.0.0
python-multipart==0.0.6
alembic==1.12.1
gunicorn==21.2.0
```

---

## 4. PostgreSQL アドオン

### 4.1 Postgres 追加
```bash
# Standard プラン
heroku addons:create heroku-postgresql:standard-0

# 確認
heroku addons

# 接続情報取得
heroku pg:info
```

### 4.2 ローカルから接続確認
```bash
# Postgres URL 取得
heroku config:get DATABASE_URL

# ローカル接続テスト
psql postgresql://...@ec2-xxx.amazonaws.com:5432/...
```

---

## 5. デプロイ

### 5.1 Git 準備
```bash
# リポジトリ初期化
git init
git add .
git commit -m "Initial commit: MarginScout SaaS"

# Heroku リモート追加
heroku git:remote -a margin-scout-api
```

### 5.2 デプロイ実行
```bash
# デプロイ
git push heroku main

# ログ確認
heroku logs --tail
```

### 5.3 DB マイグレーション
```bash
# マイグレーション実行（Procfile の release で自動実行）
heroku run alembic upgrade head

# テーブル確認
heroku run python -c "
from app.models import Base
from sqlalchemy import create_engine
import os
engine = create_engine(os.getenv('DATABASE_URL'))
Base.metadata.create_all(engine)
"
```

---

## 6. ドメイン・SSL 設定

### 6.1 カスタムドメイン
```bash
# ドメイン追加
heroku domains:add margin-scout.example.com

# 確認
heroku domains

# DNS 設定
# DNS プロバイダー設定:
# margin-scout.example.com CNAME → margin-scout-api.herokuapp.com
```

### 6.2 SSL 証明書
```bash
# Heroku が自動的に Let's Encrypt 証明書を設定
# (ACM - Automated Certificate Management)

# 確認
heroku certs:info

# 手動更新（不要）
heroku certs:auto:refresh
```

---

## 7. 環境別設定

### 7.1 本番環境チェックリスト
✅ DEBUG = false
✅ ALLOWED_HOSTS = 実ドメイン
✅ CSRF トークン有効
✅ HTTPS リダイレクト有効
✅ ログレベル = info（本番）
✅ Sentry または New Relic 連携

### 7.2 スケーリング
```bash
# Web Dyno 数変更
heroku ps:scale web=2

# ワーカー追加（非同期タスク用）
heroku ps:scale worker=1

# 確認
heroku ps
```

---

## 8. ログ・監視

### 8.1 ログ確認
```bash
# リアルタイムログ
heroku logs --tail

# エラーのみ
heroku logs --tail | grep ERROR

# 過去のログ
heroku logs --num 100
```

### 8.2 メトリクス
```bash
# 実行状況確認
heroku ps

# CPU/Memory 使用率
heroku metrics
```

---

## 9. トラブルシューティング

### 9.1 デプロイ失敗
```bash
# ビルドログ確認
heroku builds

# 再デプロイ
git push heroku main --force

# コンテナリセット
heroku dyno:restart
```

### 9.2 DB 接続エラー
```bash
# DB ステータス確認
heroku pg:info

# DB ログ
heroku logs -p postgres

# 再起動
heroku addons:destroy heroku-postgresql
heroku addons:create heroku-postgresql:standard-0
```

### 9.3 メモリ不足
```bash
# Dyno サイズアップグレード
heroku ps:type Standard-1X web

# コスト確認
heroku billing:info
```

---

## 10. 監視・運用設定

### 10.1 Sentry 連携（エラー監視）
```bash
heroku config:set SENTRY_DSN="https://key@sentry.io/project-id"
```
```python
# app/main.py に追加
import sentry_sdk
sentry_sdk.init(os.getenv("SENTRY_DSN"))
```

### 10.2 New Relic 連携（APM）
```bash
heroku addons:create newrelic:wayne
```

---

## 11. 本番環境チェックリスト

前デプロイ確認:
- [ ] requirements.txt 確認
- [ ] .env (本番値) 確認
- [ ] Procfile 確認
- [ ] SSL 設定確認
- [ ] DB バックアップ設定確認

デプロイ後確認:
- [ ] https://margin-scout.example.com にアクセス可能
- [ ] ログイン画面表示
- [ ] ログイン機能動作
- [ ] API レスポンス確認（/docs）
- [ ] DB 接続確認
- [ ] ログ出力確認
- [ ] エラーハンドリング確認（故意にエラー発生）

---

## 12. 参照
- docs/SAAS_DATABASE_DESIGN.md (DB 設定)
- docs/SAAS_MONITORING_DESIGN.md (監視設定)

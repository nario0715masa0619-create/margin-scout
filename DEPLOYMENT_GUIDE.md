# MarginScout Heroku ステージングデプロイガイド

## 前提条件
- Heroku アカウントの作成が完了していること
- Heroku CLI がインストールされ、`heroku login` が済んでいること
- Git がインストールされ、各プロジェクトがGit管理下にあること

---

## 1. Backend デプロイ手順 (margin-scout-backend)

### 1-1. Heroku App の作成とDB追加
```bash
cd margin-scout-backend
# Herokuアプリ作成 (名前は一意である必要があります)
heroku create margin-scout-staging-backend

# PostgreSQL アドオンの追加
heroku addons:create heroku-postgresql:standard-0
```

### 1-2. 環境変数の設定
```bash
# JWTシークレットキーとCORS設定
heroku config:set JWT_SECRET_KEY="your-super-secret-key-for-staging"
heroku config:set JWT_ALGORITHM="HS256"
heroku config:set CORS_ORIGINS="https://margin-scout-staging-frontend.herokuapp.com"
heroku config:set DEBUG="False"
```

### 1-3. デプロイの実行
```bash
# Herokuへのプッシュ
git add .
git commit -m "chore: add heroku deployment files"
git push heroku main
```

### 1-4. 動作確認とマイグレーション確認
```bash
# ログを確認し、release dynoでマイグレーションが走ったか確認
heroku logs --tail

# 手動で現在のマイグレーション状態を確認する場合
heroku run alembic current
```

---

## 2. Frontend デプロイ手順 (margin-scout-ui)

### 2-1. APIベースURLの修正 (事前準備)
`src/services/api.ts` を開き、URLを環境変数から取得するように変更します。
```typescript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'
```

### 2-2. Heroku App の作成
```bash
cd margin-scout-ui
# Node.jsビルドパックを指定してアプリ作成
heroku create margin-scout-staging-frontend --buildpack heroku/nodejs
```

### 2-3. 環境変数の設定
```bash
# BackendのURLを設定 (末尾の /api/v1 まで含める)
heroku config:set VITE_API_BASE_URL="https://margin-scout-staging-backend.herokuapp.com/api/v1"
```

### 2-4. デプロイの実行
```bash
git add .
git commit -m "chore: add heroku deployment files"
git push heroku main

# ブラウザでアプリを開く
heroku open
```

---

## 3. ステージング統合テスト (確認チェックリスト)

- [ ] ブラウザで Frontend (https://margin-scout-staging-frontend.herokuapp.com) が表示されるか
- [ ] `/register` から新規ユーザー登録が成功するか
- [ ] 登録後、`/research` へリダイレクトされ、Backendから201レスポンスが返るか (Networkタブ確認)
- [ ] ログアウト後、`/login` で再度ログインできるか
- [ ] ジョブ作成等のAPIリクエスト時にCORSエラーが発生していないか

---

## 4. トラブルシューティング

### 🔴 アプリケーションエラー (Application Error) が出る
**対策:** `heroku logs --tail` を実行し、バックエンドの起動エラーを確認します。
- `ModuleNotFoundError: No module named 'gunicorn'` → `requirements.txt` に `gunicorn` と `uvicorn` が無いのが原因。追加して再デプロイ。

### 🔴 DB接続エラー (Connection Refused / FATAL)
**対策:** Heroku Postgres のアドオンが正しく紐付いているか確認します。
- `heroku config` を実行し、`DATABASE_URL` が存在するか確認。
- `app/db/database.py` 内で、URLの `postgres://` を `postgresql://` に置換する処理が入っているか再確認します（Heroku特有の仕様対策）。

### 🔴 CORS エラー (Cross-Origin Request Blocked)
**対策:** フロントエンドのドメインがバックエンドの `CORS_ORIGINS` に含まれていないか、末尾の `/` の有無で不一致が起きています。
- `heroku config:set CORS_ORIGINS="https://margin-scout-staging-frontend.herokuapp.com"` を見直します。

### 🔴 Frontend デプロイ成功後、リロードすると 404 になる
**対策:** SPAのルーティング問題です。Procfileの `npx serve -s dist` の `-s` フラグが正しく設定されているか確認してください。

---

## 5. ロールバック手順
デプロイに失敗し、直前の状態に戻したい場合：
```bash
# 過去のリリース一覧を確認
heroku releases

# 1つ前のバージョン(例: v10)へロールバック
heroku rollback v10
```

# 📋 MarginScout v2.1 本番デプロイメント ステップバイステップガイド

**版**: 1.0  
**作成日**: 2026-06-16  
**対象環境**: Linux サーバー (Ubuntu 20.04+ 推奨)  
**デプロイ方式**: 手動 (ステップバイステップ)  
**本番投入判定**: 初回検証後に GO/NO-GO 判定

---

## 🎯 本番デプロイメント概要

### デプロイアーキテクチャ

┌─────────────────────────────────────────────────────────────┐ 
│ クライアント (ブラウザ)                                         │ 
└────────────────────────────┬────────────────────────────────┘ 
                             │ HTTPS 
┌────────────▼────────────┐ 
│ nginx (HTTPS)               │ 
│ Port 443 / 80 (redirect)    │ 
└────┬───────────────┬────┘ 
     │               │ 
┌──────────▼──┐ ┌────────▼──────────┐ 
│ Frontend    │ │ API Proxy           │ 
│ (Vue dist/) │ │ (/api/* → :8000)   │ 
│ Port: 80/443│ │                     │ 
└──────────────┘ └────────┬──────────┘ 
                          │ HTTP 
                ┌───────▼────────┐ 
                │ FastAPI Backend │ 
                │ Port: 8000     │ 
                │ (localhost only)│ 
                └─────────────────┘

### デプロイ前提条件

- **OS**: Ubuntu 20.04 LTS 以上
- **ユーザー**: sudo 権限あり
- **メモリ**: 2GB 以上
- **ストレージ**: 5GB 以上（ログ・データ用）
- **ネットワーク**: インターネット接続（eBay API用）
- **ドメイン**: 取得済み、DNS 設定完了
- **SSL 証明書**: Let's Encrypt で無料取得予定

---

## 📦 ステップ 1: サーバー環境準備

### 1-1: OS パッケージ更新

```bash
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install -y curl wget git vim nano
```

### 1-2: Python 3.9+ インストール

```bash
sudo apt-get install -y python3.9 python3-pip python3-venv
python3 --version  # 確認: Python 3.9.x 以上

# pip も更新
pip3 install --upgrade pip
```

### 1-3: Node.js 16+ インストール

```bash
curl -fsSL https://deb.nodesource.com/setup_16.x | sudo -E bash -
sudo apt-get install -y nodejs
node --version   # 確認: v16.x 以上
npm --version    # 確認: 8.x 以上
```

### 1-4: nginx インストール

```bash
sudo apt-get install -y nginx
sudo systemctl start nginx
sudo systemctl enable nginx
nginx -v  # 確認
```

### 1-5: Certbot (Let's Encrypt) インストール

```bash
sudo apt-get install -y certbot python3-certbot-nginx
certbot --version  # 確認
```

### 1-6: ディレクトリ構造作成

```bash
# アプリケーション root
sudo mkdir -p /var/www/margin-scout
sudo mkdir -p /var/www/margin-scout/backend
sudo mkdir -p /var/www/margin-scout/frontend
sudo mkdir -p /var/www/margin-scout/logs
sudo mkdir -p /var/www/margin-scout/data

# 権限設定
sudo chown -R $USER:$USER /var/www/margin-scout
chmod -R 755 /var/www/margin-scout
```

---

## 🔧 ステップ 2: Backend (FastAPI) デプロイ

### 2-1: Backend コード配置

```bash
# ローカルマシンから本番サーバーへ転送
scp -r /path/to/margin-scout-backend/* \
    user@server:/var/www/margin-scout/backend/

# または Git
ssh user@server
cd /var/www/margin-scout/backend
git clone <repo_url> .
```

### 2-2: Python 仮想環境構築

```bash
cd /var/www/margin-scout/backend

# 仮想環境作成
python3 -m venv venv_prod

# アクティベート
source venv_prod/bin/activate

# パッケージインストール
pip install -r requirements.txt

# 確認
pip list | grep -E "fastapi|uvicorn|pydantic"
```

### 2-3: 環境変数ファイル作成 (.env)

```bash
cd /var/www/margin-scout/backend

cat > .env.prod << 'EOF'
# ===== eBay API (本番用) =====
EBAY_ENV=live
EBAY_CLIENT_ID=YOUR_EBAY_PROD_CLIENT_ID
EBAY_CLIENT_SECRET=YOUR_EBAY_PROD_CLIENT_SECRET
EBAY_RUNAME=YOUR_EBAY_PROD_RUNAME

# ===== システム設定 =====
EXCHANGE_RATE_JPY=157.50
LOG_LEVEL=info
DEBUG=false

# ===== ログ出力 =====
LOG_FILE=/var/www/margin-scout/logs/backend.log
LOG_FORMAT=json

# ===== CORS 設定 =====
ALLOWED_ORIGINS=https://margin-scout.example.com

# ===== Job 管理 =====
JOB_TIMEOUT_SECONDS=300
MAX_CONCURRENT_JOBS=5
EOF

chmod 600 .env.prod
cat .env.prod
```

### 2-4: Backend 動作確認（起動テスト）

```bash
cd /var/www/margin-scout/backend
source venv_prod/bin/activate

# 環境変数読み込み
export $(cat .env.prod | xargs)

# Backend 起動
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

---

## 🌐 ステップ 3: Frontend (Vue.js) デプロイ

### 3-1: Frontend コード配置

```bash
# ローカルマシンから本番サーバーへ転送
scp -r /path/to/margin-scout-ui/* \
    user@server:/var/www/margin-scout/frontend/
```

### 3-2: 本番用環境変数設定

```bash
cd /var/www/margin-scout/frontend

cat > .env.production << 'EOF'
VITE_API_BASE_URL=https://margin-scout.example.com/api
VITE_ENVIRONMENT=production
VITE_LOG_LEVEL=info
VITE_DEBUG=false
EOF
```

### 3-3: Frontend ビルド

```bash
cd /var/www/margin-scout/frontend

# Node モジュールインストール
npm install

# 本番ビルド実行
npm run build

ls -la dist/
```

---

## 🔐 ステップ 4: nginx 設定 + SSL 証明書

### 4-1: nginx サイト設定ファイル作成

```bash
sudo cat > /etc/nginx/sites-available/margin-scout << 'EOF'
# ===== HTTP → HTTPS リダイレクト =====
server {
    listen 80;
    listen [::]:80;
    server_name margin-scout.example.com;

    location / {
        return 301 https://$server_name$request_uri;
    }

    # Let's Encrypt 認証用
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
}

# ===== HTTPS サーバー =====
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name margin-scout.example.com;

    # SSL 証明書（後で Certbot により自動生成）
    ssl_certificate /etc/letsencrypt/live/margin-scout.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/margin-scout.example.com/privkey.pem;

    # セキュリティヘッダー
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # ロギング
    access_log /var/www/margin-scout/logs/nginx_access.log;
    error_log /var/www/margin-scout/logs/nginx_error.log warn;

    # ===== Frontend 静的ファイル配信 =====
    location / {
        root /var/www/margin-scout/frontend/dist;
        try_files $uri $uri/ /index.html;
        
        # キャッシュ設定
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # ===== API プロキシ (/api/*) =====
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        
        # ヘッダー転送
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket サポート
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # タイムアウト
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # ===== Swagger UI (/docs) =====
    location /docs {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }

    # ===== ヘルスチェック =====
    location /health {
        access_log off;
        return 200 "OK\n";
        add_header Content-Type text/plain;
    }
}
EOF

# シンボリックリンク作成（有効化）
sudo ln -s /etc/nginx/sites-available/margin-scout \
            /etc/nginx/sites-enabled/margin-scout

# nginx 設定テスト
sudo nginx -t
```

### 4-2: Let's Encrypt SSL 証明書取得

```bash
# Certbot で証明書取得・自動設定
sudo certbot --nginx -d margin-scout.example.com
```

### 4-3: nginx リロード

```bash
sudo systemctl reload nginx
sudo systemctl status nginx
```

---

## ✅ ステップ 5: 本番環境動作確認

### 5-1: Backend API 疎通確認

```bash
curl -k https://margin-scout.example.com/docs
```

### 5-2: Frontend 表示確認

```bash
# ブラウザで確認
https://margin-scout.example.com
```

### 5-3: CORS 疎通確認

ブラウザコンソールにて API にリクエストを飛ばし、CORS エラーがないか確認。

---

## 🧪 ステップ 6: 本番最小 E2E テスト

1. S01: リサーチ開始
2. S02: 実行中モニター
3. S03: 候補一覧
4. S04: 詳細表示
5. S05: CSV 出力

各画面の機能が本番環境で正常に動作することを確認します。

---

## 📊 ステップ 7: 本番環境チェックリスト確認

(別途用意した `PRODUCTION_DEPLOYMENT_CHECKLIST.md` で各項目を確認)

---

## 🎯 ステップ 8: 本番投入最終判定

全ての GO 条件をクリアできているかチェックし、投入判断を行います。

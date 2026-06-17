# 本番デプロイ実施チェックリスト

**実施日**: _____________  
**実施者**: _____________  
**サーバー環境**: Linux (Ubuntu 20.04+)

---

## ✅ ステップ 1: サーバー環境準備

- [ ] 1-1: OS パッケージ更新 (apt-get update/upgrade)
- [ ] 1-2: Python 3.9+ インストール確認
- [ ] 1-3: Node.js 16+ インストール確認
- [ ] 1-4: nginx インストール確認
- [ ] 1-5: Certbot (Let's Encrypt) インストール確認
- [ ] 1-6: ディレクトリ構造 (/var/www/margin-scout/) 作成確認

---

## ✅ ステップ 2: Backend (FastAPI) デプロイ

- [ ] 2-1: Backend コード配置 (/var/www/margin-scout/backend/)
- [ ] 2-2: Python 仮想環境構築 (venv_prod)
- [ ] 2-3: .env.prod 作成・設定確認
  - EBAY_ENV=live ✓
  - EBAY_CLIENT_ID (本番用) ✓
  - EBAY_CLIENT_SECRET (本番用) ✓
  - EXCHANGE_RATE_JPY=157.50 ✓
  - LOG_LEVEL=info ✓
  - DEBUG=false ✓
  - chmod 600 .env.prod ✓
- [ ] 2-4: Backend 起動テスト
  - Application startup complete ✓
  - Swagger UI (/docs) 表示可能 ✓
  - 7 API エンドポイント表示 ✓

---

## ✅ ステップ 3: Frontend (Vue.js) デプロイ

- [ ] 3-1: Frontend コード配置 (/var/www/margin-scout/frontend/)
- [ ] 3-2: .env.production 作成・設定確認
  - VITE_API_BASE_URL=https://margin-scout.example.com/api ✓
  - VITE_ENVIRONMENT=production ✓
  - VITE_LOG_LEVEL=info ✓
  - VITE_DEBUG=false ✓
- [ ] 3-3: Frontend ビルド実行
  - ビルドエラーなし ✓
  - dist/ ディレクトリ作成 ✓
  - dist/index.html 存在 ✓
  - dist/assets/*.js 存在 ✓

---

## ✅ ステップ 4: nginx 設定 + SSL 証明書

- [ ] 4-1: nginx サイト設定ファイル作成
  - HTTP → HTTPS リダイレクト設定 ✓
  - Frontend 静的配信設定 ✓
  - API プロキシ設定 (/api/* → :8000) ✓
  - セキュリティヘッダー設定 ✓
- [ ] 4-2: nginx 設定 テスト
  - 期待出力: configuration file test is successful ✓
- [ ] 4-3: nginx 設定を有効化
- [ ] 4-4: Let's Encrypt SSL 証明書取得
  - Certificate successfully installed ✓
  - /etc/letsencrypt/live/margin-scout.example.com/ ✓
  - fullchain.pem 存在 ✓
  - privkey.pem 存在 ✓
- [ ] 4-5: nginx リロード
  - nginx status: active (running) ✓

---

## ✅ ステップ 5: 本番環境動作確認

- [ ] 5-1: Backend API 疎通確認
  - 期待: Swagger UI HTML 返却 ✓
- [ ] 5-2: Frontend 表示確認
  - HTTPS 接続 (鍵アイコン) ✓
  - MarginScout v2.1 UI 表示 ✓
  - S01 (リサーチ開始) 画面表示 ✓
- [ ] 5-3: ブラウザコンソール確認 (F12)
  - 致命的エラーなし ✓
  - CORS エラーなし ✓
  - Network タブ: API リクエスト 200 OK ✓
- [ ] 5-4: CORS 疎通確認 (コンソール実行)
  - 期待: Success オブジェクトに job_id ✓

---

## ✅ ステップ 6: 本番最小 E2E テスト

- **【S01: リサーチ開始】** 判定: ✓ OK / ✗ NG
- **【S02: 実行中モニター】** 判定: ✓ OK / ✗ NG
- **【S03: 候補一覧】** 判定: ✓ OK / ✗ NG
- **【S04: 詳細表示】** 判定: ✓ OK / ✗ NG
- **【S05: CSV 出力】** 判定: ✓ OK / ✗ NG
- **【ログ記録確認】** 判定: ✓ OK / ✗ NG

---

## ✅ ステップ 7: エラーハンドリング確認

- **【Backend 停止時】** 判定: ✓ OK / ✗ NG
- **【API タイムアウト】** 判定: ✓ OK / ✗ NG
- **【ErrorModal / LogPanel】** 判定: ✓ OK / ✗ NG

---

## ✅ ステップ 8: 本番環境チェックリスト

- [ ] 【環境変数確認】
- [ ] 【Backend プロセス確認】
- [ ] 【Frontend ビルド確認】
- [ ] 【nginx / SSL 確認】
- [ ] 【API プロキシ疎通確認】
- [ ] 【ログファイル確認】

---

## 🎯 最終判定

【GO 条件チェック】
- [ ] 全ステップ 1-8 完了
- [ ] 全チェックリスト項目 ✓ OK
- [ ] E2E フロー 5/5 成功
- [ ] エラーハンドリング 全確認
- [ ] ログ出力・監視体制 確認

【最終判定】
- [ ] **GO**: 本番環境への投入可能
- [ ] **NO-GO**: [理由を記入]

**投入日時**: _____________

# MarginScout Deployment Guide

## 1. 概要

本ドキュメントは MarginScout の本番環境 (Production) およびステージング環境 (Staging) へのデプロイ設計を定義します。
旧来の Heroku アーキテクチャから、コストパフォーマンスと可用性に優れた **Vercel + Railway** 構成へ移行しました。

## 2. インフラ基盤とコンポーネント

| コンポーネント | ホスティングサービス | 役割 |
| :--- | :--- | :--- |
| **Frontend (Dashboard)** | **Vercel** | Next.js / Vue によるユーザー向けダッシュボードと LP の配信。Edge Network による高速化。 |
| **Browser Extension** | **Chrome Web Store** | ユーザーのブラウザ上で動作する DOM 抽出・UI 補助アプリケーション。 |
| **Backend API** | **Railway** | FastAPI による認証・課金・データ処理・eBay 照合の提供。 |
| **Worker** | **Railway** | Celery による非同期処理（Browserless連携、バッチ処理等）。 |
| **Database** | **Railway Postgres** | `users`, `captures`, `ebay_matches` 等の永続化データの保存。 |
| **Cache / Queue** | **Upstash Redis** | Rate Limit の管理、Celery Message Broker、高速キャッシュ。 |
| **Browser Execution** | **Browserless.io** | Worker からバックグラウンドスクレイピングを行う際のブラウザ実行環境。 |

---

## 3. 環境分離戦略 (Staging vs Production)

Railway および Vercel では、環境 (Environment) 機能を利用して分離します。

### Staging 環境
- **Vercel**: `preview` ブランチ（または PR プレビュー）に紐づく。
- **Railway**: `staging` 環境 (Environment) として API と Worker をデプロイ。
- **DB**: Staging 専用の Railway Postgres インスタンス。
- **用途**: 新機能の結合テスト、QA検証。

### Production 環境
- **Vercel**: `main` ブランチに紐づき、カスタムドメインで稼働。
- **Railway**: `production` 環境 (Environment) にデプロイ。リソース制限（メモリ/CPU）をスケールアップ。
- **DB**: Production 用の堅牢な Railway Postgres インスタンス（バックアップ有効化）。
- **用途**: 実際の顧客へのサービス提供。

---

## 4. CI/CD デプロイパイプライン

### 4.1 Frontend (Vercel)
GitHub レポジトリの対象ブランチに変更が Push されると、Vercel の自動デプロイがトリガーされます。
- **トリガー**: `main` ブランチへの Push または PR
- **ビルドコマンド**: `npm run build`
- **環境変数**: Vercel の Environment Variables メニューで管理。

### 4.2 Backend & Worker (Railway)
Railway も GitHub 連携により自動ビルド＆デプロイをサポートしています。
- **トリガー**: `main` (Production) または `preview` (Staging) への Push
- **ビルド定義**: リポジトリルートの `Dockerfile` などを元にビルド、または Nixpacks による自動検知。
- **プロセス構成**: 
  - `web` プロセス: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
  - `worker` プロセス: `celery -A app.core.celery_app worker --loglevel=info`

### 4.3 Browser Extension
Extension は Chrome Web Store の審査プロセスを通す必要があるため、GitHub Actions 等でビルド成果物 (ZIP) を生成し、審査フローへ手動・自動で投入します。

---

## 5. 環境変数 (Environment Variables)

デプロイにあたり、以下の環境変数を Vercel および Railway に設定する必要があります。

**Backend (Railway)**
- `DATABASE_URL`: PostgreSQL 接続文字列
- `REDIS_URL`: Upstash Redis 接続文字列
- `SECRET_KEY`: JWT 暗号化用キー
- `EBAY_API_KEY`: eBay Browse API クレデンシャル
- `STRIPE_SECRET_KEY`: Stripe API キー
- `BROWSERLESS_API_KEY`: Browserless.io 接続トークン

**Frontend (Vercel)**
- `NEXT_PUBLIC_API_BASE_URL`: Railway API のドメイン
- `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY`: Stripe の公開キー

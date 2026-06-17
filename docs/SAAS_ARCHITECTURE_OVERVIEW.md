# MarginScout SaaS - アーキテクチャ概要設計書

**バージョン**: 1.0  
**作成日**: 2026-06-16  
**対象範囲**: MarginScout v2.1 SaaS 化（eBay リサーチ機能）

## ⚠️ スコープ明記

MarginScout は SaaS 化後もリサーチツールであり、Sell API / 出品 / 在庫 / 注文管理はスコープ外です。

---

## 1. SaaS 化の位置づけ

### 1.1 現在の状態
- ローカルアプリケーション（in-memory）
- シングルユーザー前提
- 起動時のみ動作

### 1.2 SaaS 化後の状態
- クラウドサーバー（Heroku）上で 24/7 稼働
- マルチテナント対応
- ユーザー認証・課金システム完備

### 1.3 SaaS の価値提案
ユーザーメリット: ✅ インストール不要（ブラウザアクセス） ✅ データはクラウド保存（複数デバイス対応） ✅ 常に最新版（アップデート自動） ✅ 24/7 サポート体制

ビジネスメリット: ✅ 継続課金（ARR 拡大） ✅ ユーザーデータ活用（分析・改善） ✅ スケーラビリティ（ユーザー増加対応）

---

## 2. SaaS 全体アーキテクチャ

### 2.1 システム構成図

┌─────────────────────────────────────────────────────┐ 
│ Internet                                            │ 
└────────────────────┬────────────────────────────────┘ 
                     │ HTTPS 
┌────────────▼────────────┐ 
│ Heroku Platform         │ 
│ (Production Tier)       │ 
│                         │ 
├─────────┬─────────┐     │ 
│         │         │     │ 
┌───▼──┐ ┌──▼───┐ ┌───▼──┐  │ 
│ Web  │ │ API  │ │Worker│  │ 
│Server│ │Server│ │Task  │  │ 
└───┬──┘ └──┬───┘ └───┬──┘  │ 
    │       │         │     │ 
└───┬───┴────┬────┘     │ 
    │        │          │ 
┌───▼──┐ ┌──▼───┐       │ 
│Redis │ │ Postgres │       │ 
│Cache │ │ Database │       │ 
└──────┘ └────────┘       │ 
│                         │ 
└─────────────────────────┘ 
             │ 
┌─────────▼────────┐ 
│ External Service │ 
│ - Stripe (Payment)│ 
│ - eBay API       │ 
│ - Sentry (Logs)  │ 
└──────────────────┘

### 2.2 コンポーネント

| コンポーネント | 役割 | 技術 |
|---|---|---|
| Web Server | Frontend 静的配信 | nginx (Heroku) |
| API Server | Backend ロジック | FastAPI + uvicorn |
| Database | 永続データ | PostgreSQL |
| Cache | セッション・キャッシュ | Redis |
| Worker | 非同期タスク | Celery (オプション) |
| 決済 | サブスク管理 | Stripe / Paddle |

---

## 3. データフロー

### 3.1 ユーザーリサーチフロー

ユーザーログイン 
↓
リサーチ条件入力 (S01) 
↓
Backend API 呼び出し POST /api/research/jobs (with user_id) 
↓
Backend: job_id 生成・DB 保存 
↓
Frontend: 進捗表示 (S02) ポーリング: GET /api/research/jobs/{job_id} 
↓
Backend: eBay API 呼び出し・データ取得 
↓
Backend: 候補データ DB 保存 
↓
Frontend: 候補一覧表示 (S03) 
↓
ユーザー: CSV 出力 POST /api/research/jobs/{job_id}/export/csv 
↓
Backend: CSV 生成・ダウンロード

### 3.2 認証フロー

ユーザー登録 POST /auth/register (email, password) 
↓
Backend: password hash・DB 保存 
↓
ユーザーログイン POST /auth/login (email, password) 
↓
Backend: JWT トークン発行 
↓
Frontend: token 保存（localStorage / SessionStorage） 
↓
以降の API リクエスト Authorization: Bearer {token} 
↓
Backend: token 検証・user_id 抽出

### 3.3 課金フロー

ユーザー: プラン選択画面 
↓
Frontend: Stripe iframe 表示 
↓
ユーザー: クレジットカード入力 
↓
Stripe: 決済処理 
↓
Stripe Webhook: Backend に通知 
↓
Backend: subscription テーブル更新 
↓
Frontend: プラン表示更新

---

## 4. マルチテナント設計

### 4.1 テナント分離戦略

**Row-level Security (RLS)**:
- user_id を主キーの一部にする
- すべての Query に WHERE user_id = current_user_id を付与
- DB レベルで enforced

### 4.2 テーブル構造

users テーブル 
├─ user_id (PK) 
├─ email 
└─ password_hash

research_jobs テーブル 
├─ job_id (PK) 
├─ user_id (FK) ← テナント分離用 
└─ ...

candidates テーブル 
├─ candidate_id (PK) 
├─ job_id (FK) 
├─ user_id (FK) ← テナント分離用 
└─ ...

---

## 5. 運用体制

### 5.1 監視・アラート

監視項目: 
✅ API レレスポンス時間 (SLA: < 1000ms) 
✅ エラー率 (SLA: < 0.1%) 
✅ DB 接続数 
✅ ディスク容量 
✅ eBay API 制限

### 5.2 バックアップ・復旧

頻度: 日次 
保持期間: 30日 
RPO (Recovery Point Objective): 24時間 
RTO (Recovery Time Objective): 1時間

---

## 6. セキュリティ要件

✅ HTTPS/TLS (Heroku 自動) 
✅ パスワードハッシング (bcrypt) 
✅ JWT トークン認証 
✅ CORS 設定（ドメイン限定） 
✅ Rate Limiting 
✅ SQL Injection 対策 (ORM 使用) 
✅ CSRF トークン

---

## 7. スケーラビリティ計画

### 7.1 ユーザー数増加時

100 users → Standard 構成で対応 
1,000 users → Standard-2X + Read Replica 検討 
10,000+ users → Kubernetes / ECS 検討

### 7.2 リソース管理

ユーザーあたりの quota:

月間リサーチ数: 50（Basic）/ 無制限（Pro）
ジョブデータ保持期間: 30日（Basic）/ 90日（Pro）
同時ジョブ数: 1

---

## 8. 参照ドキュメント

詳細設計:

- docs/SAAS_MULTITENANCY_DESIGN.md
- docs/SAAS_AUTHENTICATION_DESIGN.md
- docs/SAAS_BILLING_DESIGN.md
- docs/SAAS_DATABASE_DESIGN.md
- docs/SAAS_API_CHANGE_SPEC.md

運用:

- docs/SAAS_HEROKU_DEPLOYMENT.md
- docs/SAAS_MONITORING_DESIGN.md
- docs/SAAS_SECURITY_CHECKLIST.md

実装:

- docs/SAAS_IMPLEMENTATION_ROADMAP.md

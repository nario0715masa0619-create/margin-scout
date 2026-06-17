# MarginScout SaaS Phase 1 - Genspark Super Agent ハンドオフドキュメント

**バージョン**: 1.0  
**作成日**: 2026-06-16

---

## 1. ドキュメント概要

### 目的
MarginScout の SaaS化 Phase 1（認証・マルチテナント基盤）を Genspark Super Agent が実装するための完全なハンドオフドキュメント。Backend + Frontend の統合的な認証フローを 5営業日で完成させる。

### 成果物
- [ ] FastAPI Backend（JWT認証 + SQLAlchemy モデル）
- [ ] Vue 3 Frontend（Pinia ストア + ルーターガード）
- [ ] Heroku ステージング環境デプロイ
- [ ] E2E テスト（pytest + Playwright）
- [ ] 多テナント分離（user_id ベース）

### 実装期間
- **期間**: 5営業日（Week 1-2 の前半）
- **タイムゾーン**: UTC/JST（別途調整）
- **デリバリー**: 毎日 EOD (18:00) にプログレスレポート

---

## 2. スコープ・前提条件

### 2.1 スコープ（対象）
| 領域 | 対象 | 詳細 |
|---|---|---|
| Backend | ✅ 実装 | FastAPI + SQLAlchemy 2.0（同期）, JWT認証, PostgreSQL, Alembic |
| Frontend | ✅ 実装 | Vue 3 + TypeScript + Pinia, 認証コンポーネント, E2E テスト |
| MultiTenant | ✅ 実装 | app-layer の `user_id` 制御, Repository/Service での分離 |
| Infra | ✅ 実装 | Heroku ステージング環境デプロイ, PostgreSQL 接続 |
| QA | ✅ 実装 | pytest テスト（Backend）, Playwright E2E テスト（Frontend） |

### 2.2 Out of Scope（対象外）
| 領域 | 理由 |
|---|---|
| Sell API / Inventory / Order Management | Phase 2+ |
| RLS (Row Level Security) | 設計のみ, 実装は Phase 2 |
| Stripe 請求統合 | Phase 2 |
| パスワードリセット | Phase 2 |
| 2FA / MFA | Phase 2 |
| OAuth (Google/GitHub) | Phase 2 |
| 本番環境デプロイ | Task 6 で判定, 実施は別途 |
| メール認証 | Phase 2 |
| 監査ログ | Phase 2 |
| API Rate Limiting | Phase 2 |

### 2.3 前提条件
**開発環境**
- [x] Python 3.11+ インストール済み
- [x] Node.js 18+ インストール済み
- [x] PostgreSQL 14+ インストール（ローカル開発用）
- [x] Git クローン済み（margin-scout リポジトリ）

**Heroku**
- [x] Heroku アカウント作成済み
- [x] Heroku CLI インストール済み
- [x] `heroku login` 実行済み

**ドキュメント**
- [x] `PHASE_1_BACKEND_IMPLEMENTATION_GUIDE.md` 確認済み
- [x] `PHASE_1_FRONTEND_IMPLEMENTATION_GUIDE.md` 確認済み
- [x] `SAAS_ARCHITECTURE_OVERVIEW.md` 確認済み

**既存コード**
- [x] MarginScout v2.1 のローカル環境が動作中
- [x] 既存 Frontend（Vue 3）の構成把握済み
- [x] 既存 Backend の API 仕様書確認済み

---

## 3. Phase 1 実装タスクリスト

### 📊 全体進捗（5営業日）
```text
Day 1 (Mon)       │ Task 1: 環境・初期化
──────────────────┼─────────────────────────────────────
Day 2-3 (Tue-Wed) │ Task 2: Backend 実装 + Task 3: Frontend 実装（並列）
──────────────────┼─────────────────────────────────────
Day 4 (Thu)       │ Task 4: 統合テスト
──────────────────┼─────────────────────────────────────
Day 5 (Fri)       │ Task 5: Heroku ステージングデプロイ
──────────────────┼─────────────────────────────────────
Task 6 (任意)     │ 本番デプロイ判定（別途スケジュール）
```

---

## 4. タスク詳細（Task 1-6）

### Task 1: 環境・初期化（Day 1, 8 hours）
- **担当**: Infra / Backend / Frontend
- **目的**: 開発環境の完全セットアップと依存関係の整備
- **主要サブタスク**:
  - [ ] **Backend 初期化**: `.env` ファイル作成, `requirements.txt` インストール, Alembic 初期化, PostgreSQL 接続確認, 初期マイグレーション実行
  - [ ] **Frontend 初期化**: `package.json` 依存関係インストール, `.env` ファイル作成, TypeScript `tsconfig.json` 調整, Pinia/Vue Router プラグイン登録
  - [ ] **Heroku ステージング環境準備**: Heroku アプリ作成, PostgreSQL アドオン追加, 環境変数設定, Procfile 作成
  - [ ] **リポジトリ構成確認**: 必要なディレクトリ構造の作成, `.gitignore` 更新
- **完了条件**:
  - [ ] `python app/main.py` で uvicorn 起動確認
  - [ ] `npm run dev` 実行確認
  - [ ] Heroku アプリ・DB 作成完了
  - [ ] 全設定ファイルがリポジトリに commit 済み
- **参照ドキュメント**: `PHASE_1_BACKEND_IMPLEMENTATION_GUIDE.md` § 1-2, `PHASE_1_FRONTEND_IMPLEMENTATION_GUIDE.md` § 1
- **リスク**: PostgreSQL 接続エラー（DATABASE_URL フォーマット確認）

### Task 2: Backend 実装（Day 2-3, 16 hours）
- **担当**: Backend
- **目的**: FastAPI + SQLAlchemy + JWT 認証の完全実装
- **主要サブタスク**:
  - [ ] **SQLAlchemy モデル定義**: User, Subscription, ResearchJob などの実装とリレーション設定
  - [ ] **Alembic マイグレーション**: `env.py` 修正とマイグレーションの生成・実行
  - [ ] **JWT 認証実装**: `JWTHandler` クラスの実装（Access 15分, Refresh 7日）
  - [ ] **Service レイヤー**: AuthService, UserService の実装とパスワードハッシュ設定
  - [ ] **Repository レイヤー**: `BaseRepository`, `ResearchJobRepository` の実装（必ず `user_id` フィルタ）
  - [ ] **ルーター・エンドポイント**: `/auth`, `/research-jobs` などのAPIエンドポイント実装
  - [ ] **依存性注入**: `get_current_user_id`, `get_current_user` の実装
  - [ ] **データベースセッション管理**: `get_db` 実装と Heroku `postgres://` 対応
  - [ ] **FastAPI アプリケーション本体**: CORS設定とルーター登録
  - [ ] **テスト実装**: pytest による認証とアクセス制御のテスト実装
- **完了条件**:
  - [ ] pytest カバレッジ >= 80% で全テスト成功
  - [ ] `user_id` フィルタ（他テナントへのアクセス拒否）の動作確認
  - [ ] JWTトークンの検証確認
- **参照ドキュメント**: `PHASE_1_BACKEND_IMPLEMENTATION_GUIDE.md` § 1-12
- **リスク**: JWT トークン有効期限ミス, `user_id` フィルタ漏れ, PostgreSQL 接続エラー

### Task 3: Frontend 実装（Day 2-3, 16 hours, Task 2 と並列）
- **担当**: Frontend
- **目的**: Vue 3 + Pinia + ルーターガード による認証導線の完全実装
- **主要サブタスク**:
  - [ ] **TypeScript 型定義**: AuthState, User 等の型定義
  - [ ] **Pinia ストア実装**: AuthStore, UserStore と トークン管理
  - [ ] **Axios インターセプター**: JWT Bearer 自動付与と 401 自動リフレッシュロジック
  - [ ] **Vue Router ガード**: `requiresAuth`, `requiresGuest` ガード実装
  - [ ] **認証コンポーネント**: LoginForm.vue, RegisterForm.vue 等の実装
  - [ ] **既存画面認証前提化**: Dashboard や ResearchJobs にユーザー情報・ログアウトを組み込む
  - [ ] **Composable**: `useAuth.ts`, `useUser.ts`
  - [ ] **E2E テスト**: Playwright による認証フロー・アクセス制御テスト
- **完了条件**:
  - [ ] ユーザー登録 → ログイン → Dashboard フローが正常動作
  - [ ] Playwright E2E テスト成功
  - [ ] TypeScript エラーなし
- **参照ドキュメント**: `PHASE_1_FRONTEND_IMPLEMENTATION_GUIDE.md` § 1-8
- **リスク**: Token 失効時のUX不具合, ページリロード時セッション喪失, CORS エラー

### Task 4: 統合テスト（Day 4, 8 hours）
- **担当**: QA / Backend / Frontend
- **目的**: Backend API と Frontend 統合動作確認、E2E テスト実行
- **主要サブタスク**:
  - [ ] Backend API 動作確認（curl, Postman）
  - [ ] Frontend からの API 呼び出し確認
  - [ ] 認証フローの統合 E2E 確認
  - [ ] 複数ユーザーによる `user_id` 分離確認
  - [ ] Playwright E2E テストの実行
  - [ ] セキュリティ脆弱性確認（SQL インジェクション, JWT 改竄等）
- **完了条件**:
  - [ ] 全エンドポイント正常応答
  - [ ] 複数テナントでのデータ分離が確認できること
  - [ ] Token の自動リフレッシュが成功すること
  - [ ] Playwright 成功, pytest >= 80%
- **参照ドキュメント**: バックエンド/フロントエンド ガイドの該当セクション
- **リスク**: CORS エラー, Token リフレッシュ タイミングの不整合, E2E タイムアウト

### Task 5: Heroku ステージングデプロイ（Day 5, 8 hours）
- **担当**: Infra / Backend / Frontend
- **目的**: Heroku ステージング環境で Backend + Frontend 完全動作
- **主要サブタスク**:
  - [ ] Backend デプロイ準備（Procfile, runtime.txt）
  - [ ] Frontend デプロイ準備（Procfile, .env.production）
  - [ ] Heroku 環境変数設定
  - [ ] `git push heroku main` によるデプロイ
  - [ ] PostgreSQL マイグレーションと接続確認
  - [ ] Heroku 上での API および Frontend の E2E テスト
  - [ ] ログ監視とトラブルシューティング
- **完了条件**:
  - [ ] Backend / Frontend ともに Dyno status が green
  - [ ] API 正常動作、Frontend 表示確認
  - [ ] `heroku logs --tail` に致命的なエラーがないこと
- **参照ドキュメント**: `SAAS_HEROKU_DEPLOYMENT.md`
- **リスク**: DATABASE_URL フォーマット違い, Port バインディング失敗, 依存バージョン不整合

### Task 6: 本番デプロイ判定（任意 / 次フェーズ, 4 hours）
- **担当**: Product / Infra / Backend / Frontend
- **目的**: 本番デプロイの GO/NO-GO 判定と準備
- **主要サブタスク**:
  - [ ] GO/NO-GO チェックリスト実行
  - [ ] 本番前提条件確認（強力キー生成, SSL確認 等）
  - [ ] リリース手順確認（ロールバック, インシデント計画）
  - [ ] ドキュメント整備（運用ガイド等）
- **完了条件**:
  - [ ] GO/NO-GO 判定クリア
  - [ ] 本番運用計画およびガイドが完成
- **参照ドキュメント**: `SAAS_SECURITY_CHECKLIST.md`

---

## 5. タスク依存関係図

```text
Task 1 (環境初期化) 
  ├──> Task 2 (Backend 実装)
  └──> Task 3 (Frontend 実装)
         └──> Task 4 (統合テスト)
                └──> Task 5 (Heroku デプロイ)
                       └──> Task 6 (本番デプロイ判定)
```

---

## 6. 完了条件・Definition of Done（DoD）

- **Backend DoD**: モデル実装, マイグレーション成功, JWT API完成, user_id制御, pytest>=80%, エラーハンドリング完備
- **Frontend DoD**: Pinia ストア, Axios インターセプター, Router ガード, コンポーネント完成, 既存画面対応, Playwright成功, TS エラーなし
- **Heroku DoD**: Backend/Frontend Dyno green, PostgreSQL成功, API確認, Frontend確認, ログ エラーなし
- **統合 DoD**: ユーザー登録→ログイン→Dashboard フロー成功, user_id分離確認, Token自動リフレッシュ, CORS エラーなし
- **ドキュメント DoD**: Backend/Frontend ガイド確認, ハンドオフドキュメント確認, デプロイガイド完成

---

## 7. 既知リスク・ボトルネック

- 🔴 **Critical**: PostgreSQL接続エラー, JWT検証失敗, CORS エラー, `user_id` フィルタ漏れ, Token自動リフレッシュ失敗
- 🟡 **High**: ページリロード時セッション喪失, Heroku Port バインディング, Node/Python バージョン, HTTPS混在
- 🟢 **Low**: npm依存関係競合, Python仮想環境

---

## 8. 参照ドキュメント

- **生成済みガイド**
  - `PHASE_1_BACKEND_IMPLEMENTATION_GUIDE.md`
  - `PHASE_1_FRONTEND_IMPLEMENTATION_GUIDE.md`
- **SaaS アーキテクチャ**
  - `SAAS_ARCHITECTURE_OVERVIEW.md`
  - `SAAS_AUTHENTICATION_DESIGN.md`
  - `SAAS_MULTITENANCY_DESIGN.md`
  - `SAAS_HEROKU_DEPLOYMENT.md`
  - `SAAS_SECURITY_CHECKLIST.md`
- **外部ドキュメント**
  - FastAPI, SQLAlchemy, Vue3, Pinia, Heroku DevCenter 各公式ドキュメント

---

## 9. 進捗追跡メトリクス

- **日次進捗レポート テンプレート**: (Task進捗バー, 完了項目, 実施中項目, ブロッカー, 次の24h予定)
- **全体メトリクス表**: pytest カバレッジ, Playwright E2E, TypeScript エラー数, API応答時間, ページロード時間, JWT/user_id/CORS制御の健全性

---

## 10. 最終受け入れ条件（Acceptance Criteria）

- **Backend 受け入れ条件**: pytest成功, curl各エンドポイント確認, Access Control確認, ログ エラーなし, テーブル構造確認
- **Frontend 受け入れ条件**: npm run dev確認, ログインページ表示, 登録→Dashboard フロー, API リクエスト確認, LocalStorage動作, Playwright成功, TS エラーなし
- **Heroku 受け入れ条件**: Dyno green, PostgreSQL active, `/health` OK, フロー成功, ログ エラーなし
- **統合受け入れ条件**: 複数ユーザー完全分離, Token自動リフレッシュ, 無効JWTでのログアウト, エラーメッセージ正常表示, JSコンソール エラーなし
- **ドキュメント受け入れ条件**: 各ガイド承認, デプロイガイド完成, トラブルシューティング完成
- **最終ゴール**: Phase 1 完全実装 + Heroku ステージング 24h安定稼働 + 全テスト成功 + セキュリティチェック完了 + ドキュメント完備 → **Phase 2 移行可能**

---

## 11. 付録：よくある実装ミス・注意点

- **Backend ミス**:
  - `user_id` フィルタ漏れ（他テナント情報漏洩）
  - JWT有効期限の設定ミス
  - Heroku での `DATABASE_URL` フォーマット非互換 (`postgres://` 修正忘れ)
  - CORS の設定漏れ
  - エラーハンドリング不備 (生のスタックトレースが返却される)
- **Frontend ミス**:
  - Token保存先の混在（ロジックの散在）
  - リトライロジックの無限ループ（401 ハンドリング時）
  - ルーターガードのチェック漏れ（未ログインでの保護ページアクセス）
  - CORSプリフライトエラー
  - TypeScript `any` 型の濫用
- **デプロイミス**:
  - 本番用環境変数の未設定
  - `Procfile` のパス指定・コマンド誤り
  - 本番データベースへの Alembic マイグレーション実行漏れ
  - ログレベル設定ミス (DEBUG が出力されたまま)
  - Dynoの起動失敗 (Port Binding タイムアウト等)

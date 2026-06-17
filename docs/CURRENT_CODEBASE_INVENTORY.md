# MarginScout v2.1 現行コードベース 棚卸しレポート

## 1. リポジトリ構成

### Backend (`margin-scout-backend/`)
- エントリポイント: `app/main.py`
- ルーター: 実ファイルなし（すべてのエンドポイントが `app/main.py` 内に定義されているモノリス構成）
- モデル: SQLAlchemy モデルなし（Pydantic スキーマとして `ResearchConditions`, `JobResponse`, `JobStatusResponse` が `app/main.py` に存在）
- スキーマ: `app/main.py` 内に Pydantic モデルとして存在
- DB設定: 実ファイルなし（インメモリの `active_jobs` ディクショナリでジョブを管理）
- マイグレーション: なし

### Frontend (`margin-scout-ui/`)
- ルートディレクトリ: `src/`
- ルーター: `src/router/index.ts`
- ストア: `src/stores/error.ts`, `src/stores/research.ts` (Pinia を使用)
- ページ: 
  - `src/views/S01_ResearchStart.vue`
  - `src/views/S02_ExecutionMonitor.vue`
  - `src/views/S03_CandidateList.vue`
  - `src/views/S04_CandidateDetail.vue`
  - `src/views/S05_CsvExport.vue`
- コンポーネント: 
  - `src/components/ErrorModal.vue`
  - `src/components/LogPanel.vue`
  - `src/components/HelloWorld.vue`

---

## 2. 既存モデル分類

### 再利用対象
- **Research関連モデル** (`app/main.py` 内のデータ構造および Pydantic スキーマ):
  - 判定: [再利用] `user_id` 追加予定。インメモリ管理を廃止し、SQLAlchemy の `ResearchJob` モデルおよび `Candidate` モデルへと再設計して移行する。

### 置換対象
- **User関連モデル**:
  - 現在の実装にはユーザー概念が一切存在しない。
  - 判定: [新規] `User`, `Subscription` などのマルチテナントに必要な SQLAlchemy モデルを新規作成。

### 廃止候補
- **In-memory Store (`active_jobs`)**:
  - `app/main.py` 内の `create_job_record` および `active_jobs` 辞書。
  - 判定: [廃止候補] PostgreSQL (SQLAlchemy) による永続化へ完全置換。

---

## 3. 既存ルーター分析

現在、ルーターはすべて `app/main.py` にベタ書きされています。

- **`POST /api/research/jobs`**: リサーチ開始, 依存モデルなし (Service層でUUID生成)
- **`GET /api/research/jobs/{job_id}`**: ジョブ状態取得
- **`GET /api/research/jobs/{job_id}/results`**: 候補一覧取得
- **`GET /api/research/jobs/{job_id}/results/{candidate_id}`**: 候補詳細取得
- **`POST /api/research/jobs/{job_id}/export/csv`**: CSV 出力
- **`POST /api/research/jobs/{job_id}/cancel`**: ジョブキャンセル
- **`GET /api/research/jobs/{job_id}/logs/summary`**: ログ要約取得

- **認証対応状況**: [なし]
- **user_id フィルタ**: [なし]

---

## 4. 実装影響分析

### 修正必須ファイル
- **Backend**:
  - `margin-scout-backend/app/main.py` (エンドポイントとロジックをルーターやサービスに分離する必要あり)
- **Frontend**:
  - `margin-scout-ui/src/router/index.ts` (ナビゲーションガードの追加)
  - `margin-scout-ui/src/services/api.ts` (Axios インターセプターでの JWT 対応)
  - `margin-scout-ui/src/App.vue` または ヘッダー要素 (ログアウト導線やユーザー情報表示の追加)

### 新規作成ファイル
- **Backend**:
  - `app/database.py` (DB接続設定)
  - `app/models/user.py`, `app/models/research.py` (SQLAlchemy モデル)
  - `app/repositories/base.py`, `user.py`, `research.py` (データアクセス層)
  - `app/services/auth.py` (認証ロジック)
  - `app/core/security.py`, `app/core/jwt.py` (ハッシュ化・トークン生成)
  - `app/api/deps.py` (依存性注入: user_id 検証)
  - `app/api/v1/auth.py`, `app/api/v1/research.py` (分割ルーター)
  - `alembic/` 関連ファイル
- **Frontend**:
  - `src/stores/auth.ts`, `src/stores/user.ts`
  - `src/views/LoginView.vue`, `src/views/RegisterView.vue`
  - `src/components/auth/LoginForm.vue`, `src/components/auth/RegisterForm.vue`
  - `src/composables/useAuth.ts`

### 削除候補
- `app/main.py` 内の `active_jobs` およびそれに依存するモックデータ管理用関数。

---

## 5. Phase 1 実装順序

- **Step B0**: DB基盤セットアップ (PostgreSQL 接続, Alembic 初期化)
- **Step B1**: SQLAlchemy モデル定義 (User, Subscription, ResearchJob, Candidate)
- **Step B2**: JWT認証・依存性注入 (Passlib, JWT, `get_current_user_id` 作成)
- **Step B3**: Repository / Service 実装 (テナント分離対応の CRUD)
- **Step B4**: API ルーターのリファクタリング (既存 `main.py` のモノリスを `/api/v1/research` に分割移行)
- **Step F1**: Frontend Pinia ストア & Axios インターセプター実装
- **Step F2**: Vue Router ガード & 認証画面コンポーネント作成
- **Step F3**: 既存 UI (S01〜S05) の改修 (currentUser 連携、エラー対応)
- **Step T1**: 統合テスト (E2E) と Heroku ステージングへのデプロイ

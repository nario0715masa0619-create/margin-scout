# MarginScout SaaS - データベース設計書

**バージョン**: 1.0  
**作成日**: 2026-06-16

## ⚠️ スコープ明記

MarginScout は SaaS 化後もリサーチツールであり、Sell API / 出品 / 在庫 / 注文管理はスコープ外です。

---

## 1. DB 全体設計

### 1.1 テーブル一覧

Core Tables:
- users (ユーザー情報)
- subscriptions (課金情報)

Research Tables:
- research_jobs (リサーチジョブ)
- candidates (候補データ)
- job_logs (ジョブログ)

### 1.2 ER 図

users 
├─ subscriptions (1:1) 
└─ research_jobs (1:N) 
   └─ candidates (1:N) 
   └─ job_logs (1:N)

---

## 2. テーブル定義

### 2.1 users

```sql
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    
    -- プロフィール
    display_name VARCHAR(255),
    
    -- 課金情報（冗長化）
    plan_type VARCHAR(50) DEFAULT 'free',
    stripe_customer_id VARCHAR(255),
    
    -- 統計
    total_jobs INT DEFAULT 0,
    
    -- タイムスタンプ
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_login_at TIMESTAMP,
    
    -- インデックス
    INDEX idx_email (email),
    INDEX idx_stripe_customer (stripe_customer_id)
);
```

### 2.2 subscriptions
```sql
CREATE TABLE subscriptions (
    subscription_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES users(user_id) ON DELETE CASCADE,
    
    -- Stripe 情報
    stripe_subscription_id VARCHAR(255) UNIQUE,
    stripe_customer_id VARCHAR(255),
    
    -- プラン
    plan_type VARCHAR(50) NOT NULL,  -- free / basic / pro
    
    -- ステータス
    status VARCHAR(50) DEFAULT 'active',  -- active / past_due / cancelled / expired
    
    -- 課金期間
    current_period_start DATE,
    current_period_end DATE,
    
    -- 月間使用量（リセット対象）
    monthly_job_count INT DEFAULT 0,
    monthly_reset_at DATE,
    
    -- タイムスタンプ
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    cancelled_at TIMESTAMP,
    
    INDEX idx_user_status (user_id, status)
);
```

### 2.3 research_jobs
```sql
CREATE TABLE research_jobs (
    job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    
    -- リサーチ条件
    keywords TEXT[],           -- ['iPhone', 'iPad']
    sources TEXT[],            -- ['mercari', 'ebay', 'amazon']
    days_back INT,             -- 30
    min_sales INT,             -- 1
    
    -- 実行状態
    status VARCHAR(50) DEFAULT 'running',  -- running / completed / failed
    error_message TEXT,
    
    -- 結果統計
    total_candidates INT DEFAULT 0,
    matched_candidates INT DEFAULT 0,
    
    -- タイムスタンプ
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    
    -- インデックス
    INDEX idx_user_created (user_id, created_at),
    INDEX idx_status (status),
    CONSTRAINT check_status CHECK (status IN ('running', 'completed', 'failed'))
);
```

### 2.4 candidates
```sql
CREATE TABLE candidates (
    candidate_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES research_jobs(job_id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    
    -- 商品情報
    product_name VARCHAR(500),
    source VARCHAR(50),           -- mercari / ebay / amazon
    source_url TEXT,
    
    -- 価格情報
    price_min NUMERIC(10, 2),
    price_max NUMERIC(10, 2),
    
    -- 利益計算
    profit NUMERIC(10, 2),        -- 計算済み利益
    margin NUMERIC(5, 2),         -- 利益率 %
    
    -- メタデータ
    ebay_item_id VARCHAR(50),
    condition_text VARCHAR(255),
    
    -- タイムスタンプ
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- インデックス
    INDEX idx_job_user (job_id, user_id),
    INDEX idx_margin (margin)  -- 利益率でソート用
);
```

### 2.5 job_logs (運用用)
```sql
CREATE TABLE job_logs (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES research_jobs(job_id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    
    -- ログ内容
    log_level VARCHAR(50),    -- info / warning / error
    message TEXT,
    context JSONB,            -- 追加情報
    
    -- タイムスタンプ
    created_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_job_created (job_id, created_at)
);
```

---

## 3. マイグレーション戦略

### 3.1 初期化（v1.0 → SaaS）
```sql
-- Step 1: 新テーブル作成
CREATE TABLE users (...);
CREATE TABLE subscriptions (...);
CREATE TABLE research_jobs (...);
CREATE TABLE candidates (...);

-- Step 2: インデックス作成
CREATE INDEX idx_user_email ON users(email);
CREATE INDEX idx_job_user ON research_jobs(user_id, created_at);

-- Step 3: 権限設定
GRANT SELECT, INSERT, UPDATE, DELETE ON research_jobs TO app_user;
```

### 3.2 スキーマバージョン管理
```python
# alembic を使用
# alembic/versions/001_initial.py

def upgrade():
    op.create_table(
        'users',
        sa.Column('user_id', sa.UUID, primary_key=True),
        sa.Column('email', sa.VARCHAR(255), unique=True),
        # ...
    )

def downgrade():
    op.drop_table('users')
```

---

## 4. クエリ例

### 4.1 ユーザーの全リサーチ取得
```sql
SELECT 
    j.job_id,
    j.keywords,
    j.sources,
    j.status,
    j.total_candidates,
    j.created_at
FROM research_jobs j
WHERE j.user_id = $1
ORDER BY j.created_at DESC
LIMIT 10;
```

### 4.2 リサーチの候補一覧（利益率でソート）
```sql
SELECT 
    c.candidate_id,
    c.product_name,
    c.source,
    c.price_min,
    c.price_max,
    c.profit,
    c.margin
FROM candidates c
WHERE c.job_id = $1 AND c.user_id = $2
ORDER BY c.margin DESC;
```

### 4.3 月間使用量チェック
```sql
SELECT COUNT(*) as monthly_jobs
FROM research_jobs
WHERE user_id = $1
  AND created_at >= DATE_TRUNC('month', NOW());
```

---

## 5. パフォーマンス最適化

### 5.1 インデックス戦略
頻繁なクエリ:
✅ (user_id, created_at) - ユーザーの最近のジョブ
✅ (status) - 実行中のジョブ検索
✅ (job_id, user_id) - 候補の取得

避けるべき:
❌ 全カラムのインデックス

### 5.2 クエリ最適化
```python
# ❌ N+1
for job in jobs:
    candidates = db.query(Candidate).filter(Candidate.job_id == job.id).all()

# ✅ JOIN
SELECT * FROM research_jobs j
LEFT JOIN candidates c ON j.job_id = c.job_id
WHERE j.user_id = $1;
```

### 5.3 バッチ処理
```python
# 候補データ一括挿入
from sqlalchemy import insert

stmt = insert(Candidate).values([
    {"job_id": job_id, "product_name": name, ...},
    {"job_id": job_id, "product_name": name2, ...},
    # ... 1000件
])
db.execute(stmt)
db.commit()
```

---

## 6. バックアップ・復旧

### 6.1 自動バックアップ
Heroku PostgreSQL Backup:
- 頻度: 日次
- 保持: 30日
- コマンド: `heroku pg:backups:schedule DATABASE_URL`

### 6.2 復旧手順
```bash
# バックアップ一覧
heroku pg:backups

# 復旧
heroku pg:backups:restore b001 DATABASE_URL
```

---

## 7. テスト項目
✅ マイグレーション: up/down
✅ インデックス: 実行計画確認
✅ 制約: 違反データ拒否
✅ マルチテナント分離: user_id フィルタ確認

---

## 8. 参照
- docs/SAAS_MULTITENANCY_DESIGN.md
- docs/SAAS_BILLING_DESIGN.md

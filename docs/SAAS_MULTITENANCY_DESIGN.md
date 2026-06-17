# MarginScout SaaS - マルチテナント設計書

**バージョン**: 1.0  
**作成日**: 2026-06-16

## ⚠️ スコープ明記

MarginScout は SaaS 化後もリサーチツールであり、Sell API / 出品 / 在庫 / 注文管理はスコープ外です。

---

## 1. マルチテナント概要

### 1.1 定義

**マルチテナント = 複数ユーザーが同一のサーバーリソースを共有**

- ユーザー A のデータ ≠ ユーザー B のデータ
- DB に同じテーブルに両者のデータが存在
- ただし、相互アクセス不可

### 1.2 現在との違い

【ローカル版（シングルユーザー）】 
ユーザー: 1人 
データ: メモリ上（起動時のみ有効） 
永続性: なし

【SaaS 版（マルチテナント）】 
ユーザー: 複数 
データ: DB（永続保存） 
分離: user_id ベース

---

## 2. テナント分離戦略

### 2.1 Row-Level Security (RLS)

**全テーブルに user_id を含める**

```sql
CREATE TABLE research_jobs (
    job_id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(user_id),
    status VARCHAR,
    created_at TIMESTAMP,
    -- 重要: job_id のみでは行を特定しない
    -- 必ず (job_id, user_id) で特定する
    UNIQUE(job_id, user_id)
);

-- クエリ例
SELECT * FROM research_jobs
WHERE job_id = 'abc123' AND user_id = 'user_456';
```

### 2.2 API レイヤーでの検証
Backend は全リクエストで user_id を検証

```python
# FastAPI: 認証トークンから user_id を抽出
@app.get("/api/research/jobs/{job_id}")
async def get_job_status(job_id: str, token: str = Header()):
    # 1. トークンから user_id 抽出
    user_id = decode_token(token)
    
    # 2. DB クエリ
    job = db.query(ResearchJob).filter(
        ResearchJob.job_id == job_id,
        ResearchJob.user_id == user_id  # ← 必須
    ).first()
    
    # 3. データなし = 404 (or Forbidden)
    if not job:
        raise HTTPException(status_code=404)
    
    return job
```

### 2.3 アクセス制御マトリックス
| リソース | ユーザーA | ユーザーB | Admin |
|---|---|---|---|
| ユーザーA の job | ✅ 読み書き | ❌ | ✅ |
| ユーザーB の job | ❌ | ✅ 読み書き | ✅ |
| 全体の統計 | ❌ | ❌ | ✅ |

---

## 3. テーブル設計

### 3.1 users テーブル
```sql
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    plan_type VARCHAR(50) DEFAULT 'free',  -- free / basic / pro
    subscription_status VARCHAR(50),         -- active / cancelled / expired
    stripe_customer_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### 3.2 research_jobs テーブル
```sql
CREATE TABLE research_jobs (
    job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    
    -- リサーチ条件
    keywords TEXT[],
    sources TEXT[],
    days_back INT,
    min_sales INT,
    
    -- ステータス・結果
    status VARCHAR(50) DEFAULT 'running',  -- running / completed / failed
    total_candidates INT,
    matched_candidates INT,
    
    -- タイムスタンプ
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    
    INDEX idx_user_job (user_id, created_at)
);
```

### 3.3 candidates テーブル
```sql
CREATE TABLE candidates (
    candidate_id UUID PRIMARY KEY,
    job_id UUID NOT NULL REFERENCES research_jobs(job_id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    
    -- 商品情報
    product_name VARCHAR(500),
    source_url TEXT,
    price_min DECIMAL(10, 2),
    price_max DECIMAL(10, 2),
    profit DECIMAL(10, 2),
    margin DECIMAL(5, 2),
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_job_user (job_id, user_id)
);
```

### 3.4 subscriptions テーブル
```sql
CREATE TABLE subscriptions (
    subscription_id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    
    plan_type VARCHAR(50),  -- free / basic / pro
    stripe_subscription_id VARCHAR(255),
    stripe_customer_id VARCHAR(255),
    
    -- ステータス
    status VARCHAR(50),  -- active / cancelled / expired
    
    -- 課金期間
    current_period_start DATE,
    current_period_end DATE,
    
    -- メタデータ
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    cancelled_at TIMESTAMP
);
```

---

## 4. クエリパターン

### 4.1 リサーチジョブ一覧取得
```python
# Bad: user_id チェックなし
jobs = db.query(ResearchJob).filter(
    ResearchJob.status == 'completed'
).all()  # 全ユーザーのデータ返却 ❌

# Good: user_id フィルタ付き
jobs = db.query(ResearchJob).filter(
    ResearchJob.user_id == current_user_id,
    ResearchJob.status == 'completed'
).all()  # 現在ユーザーのみ ✅
```

### 4.2 候補データ取得
```python
# Good: 複合キー確認
candidates = db.query(Candidate).filter(
    Candidate.job_id == job_id,
    Candidate.user_id == current_user_id
).all()
```

---

## 5. セキュリティチェックポイント
✅ 全 API エンドポイントで user_id 検証
✅ SELECT / UPDATE / DELETE に WHERE user_id フィルタ
✅ インデックスに (user_id, ...) を含める
✅ ユーザー B が ユーザー A の job_id を直接指定しても 404
✅ 管理者画面で全テナント表示（別途認可）

---

## 6. テスト戦略

### 6.1 マルチテナント分離テスト
```python
def test_user_cannot_access_other_user_data():
    # User A: ジョブ作成
    job_a = create_job(user_id="user_a")
    
    # User B: User A のジョブアクセス試行
    response = get_job(
        job_id=job_a.id,
        token=get_token("user_b")
    )
    
    # 結果: 404
    assert response.status_code == 404
```

---

## 7. 参照
- docs/SAAS_AUTHENTICATION_DESIGN.md (ユーザー検証)
- docs/SAAS_API_CHANGE_SPEC.md (API 変更)
- docs/SAAS_SECURITY_CHECKLIST.md (セキュリティ)

# MarginScout SaaS - 監視・運用設計書

**バージョン**: 1.0  
**作成日**: 2026-06-16

## ⚠️ スコープ明記

MarginScout は SaaS 化後もリサーチツールであり、Sell API / 出品 / 在庫 / 注文管理はスコープ外です。

---

## 1. 監視戦略

### 1.1 監視対象

インフラ: 
✅ CPU 使用率 
✅ メモリ使用率 
✅ ディスク容量 
✅ DB 接続数

アプリケーション: 
✅ API レスポンス時間 
✅ エラー率 
✅ ユーザーセッション数 
✅ eBay API レート制限

### 1.2 SLA 定義

- 可用性: 99.5%（月内 99.5% 以上稼働） 
- レスポンスタイム: 1秒以下（p95） 
- エラー率: 0.1% 以下

---

## 2. ログ戦略

### 2.1 ログレベル

- DEBUG: 開発時のみ 
- INFO: リサーチ開始・完了・重要イベント 
- WARNING: API エラー・リトライ 
- ERROR: 予期しないエラー・クラッシュ 
- CRITICAL: システムダウン

### 2.2 ログ出力

```python
import logging

logger = logging.getLogger(__name__)

# リサーチ開始
logger.info(f"Job started: {job_id} by user {user_id}")

# API エラー
logger.warning(f"eBay API error: {error_code}")

# 予期しないエラー
logger.error(f"Database connection failed: {e}")
```

---

## 3. エラーハンドリング

### 3.1 エラー分類

| エラー | 対応 | ユーザー通知 |
|---|---|---|
| eBay API タイムアウト | リトライ（最大3回） | 進捗表示 |
| DB 接続エラー | Fallback (キャッシュ) | "一時的に遅い" |
| ユーザーデータ不正 | ログ・アラート | 400 Bad Request |
| 不認証 | 拒否 | 401 Unauthorized |

### 3.2 実装例
```python
from fastapi import HTTPException

@app.get("/api/research/jobs/{job_id}")
async def get_job(job_id: str, token: str = Header(...)):
    try:
        user_id = verify_token(token)
    except:
        raise HTTPException(status_code=401)
    
    try:
        job = db.query(ResearchJob).filter(...).first()
        if not job:
            raise HTTPException(status_code=404)
        return job
    except SQLAlchemyError as e:
        logger.error(f"DB error: {e}")
        raise HTTPException(status_code=500, detail="Service unavailable")
```

---

## 4. アラート設定

### 4.1 アラート条件
High Priority:
- エラー率 > 1%
- API レスポンス > 5秒
- DB 接続失敗
- ディスク容量 < 10%

Medium Priority:
- エラー率 > 0.5%
- API レスポンス > 2秒
- eBay API レート制限

Low Priority:
- CPU 使用率 > 80%
- メモリ使用率 > 80%

### 4.2 通知先
- High: Slack #alerts + SMS
- Medium: Slack #alerts
- Low: Email daily digest

---

## 5. メトリクス収集

### 5.1 Prometheus（推奨）
```python
from prometheus_client import Counter, Histogram, generate_latest

# カウンター
request_count = Counter(
    'request_total',
    'Total requests',
    ['method', 'endpoint', 'status']
)

# ヒストグラム
request_duration = Histogram(
    'request_duration_seconds',
    'Request duration'
)

@app.get("/api/research/jobs")
async def get_jobs():
    request_count.labels('GET', '/api/research/jobs', '200').inc()
    # ...
```

### 5.2 Heroku Metrics
```bash
# CLI で確認
heroku metrics

# ダッシュボード: Heroku CLI から
heroku log --ps web
```

---

## 6. バックアップ・復旧

### 6.1 自動バックアップ
```bash
# Heroku PostgreSQL 自動バックアップ
heroku pg:backups:schedule DATABASE_URL --at "02:00 UTC"
```

### 6.2 復旧テスト
```bash
# 月1回、バックアップから復旧テスト
heroku pg:backups:restore b001 RECOVERY_DATABASE_URL
```

---

## 7. パフォーマンス最適化

### 7.1 キャッシング戦略
```python
# Redis キャッシュ
from redis import Redis
cache = Redis(host='localhost', port=6379)

@app.get("/api/user/stats")
async def get_stats(user_id: str):
    # キャッシュ確認
    cached = cache.get(f"stats:{user_id}")
    if cached:
        return json.loads(cached)
    
    # DB クエリ
    stats = db.query(...).all()
    
    # キャッシュ保存（1時間）
    cache.setex(f"stats:{user_id}", 3600, json.dumps(stats))
    
    return stats
```

### 7.2 DB クエリ最適化
```python
# ❌ N+1
for job in jobs:
    candidates = db.query(Candidate).filter(Candidate.job_id == job.id).all()

# ✅ JOIN
jobs_with_candidates = db.query(ResearchJob).join(Candidate).all()
```

---

## 8. 定期メンテナンス

### 8.1 スケジュール

毎日 02:00 UTC:
- DB バックアップ
- ログローテーション
- キャッシュクリア

毎週 日曜 03:00 UTC:
- パフォーマンス分析
- インデックス最適化

毎月 1日:
- セキュリティ監査
- 依存ライブラリ更新確認

### 8.2 実装例
```python
# APScheduler
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()

@scheduler.scheduled_job('cron', hour=2, minute=0)
def daily_backup():
    logger.info("Running daily backup...")
    # バックアップ実行

scheduler.start()
```

---

## 9. 参照
- docs/SAAS_HEROKU_DEPLOYMENT.md (デプロイ)
- docs/SAAS_SECURITY_CHECKLIST.md (セキュリティ)

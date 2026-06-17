# 非同期スクレイピング処理の実装計画

## 1. 概要と現状分析
ユーザーからの報告の通り、現在ダッシュボードでジョブを作成してもステータスが `pending` から進行しません。

**原因分析:**
1. `app/routers/research_jobs.py` の `create_job` エンドポイントでは、`ResearchJobService.create_job()` を呼び出していますが、これはDBにレコードを作成するのみです。
2. `ResearchJobService.create_job()` 内でも非同期タスクのキックは行われていません。
3. プロジェクト内に Celery の設定や FastAPI の `BackgroundTasks` の記述は存在せず、**実際にスクレイピングを実行する機構が未実装**です。

## 2. 修正方針の提案

スクレイピング処理のような時間のかかるタスクは非同期で実行する必要があります。実装アプローチとして2つの選択肢がありますが、アーキテクチャの複雑さを抑えるため **FastAPI BackgroundTasks**（Option A）を推奨します。

### Option A: FastAPI BackgroundTasks (推奨)
FastAPI に標準搭載されている軽量な非同期タスク機能を使用します。
- **メリット**: 追加のインフラ（RedisやWorker Dyno）が不要。すぐに実装でき、ローカル・Heroku 共に変更なしで動く。
- **デメリット**: サーバー再起動時に実行中のタスクが失われる（ただし、現状の要件スコープでは十分）。

### Option B: Celery + Redis
本格的なタスクキューシステム。
- **メリット**: スケーラブルで、再試行やタスク管理が容易。
- **デメリット**: Heroku に Redis アドオンの追加と、Worker プロセス用の `Procfile` 追加設定が必要。

## 3. 具体的な実装ステップ（Option A を前提）

### 3.1 タスク処理の実装 (`app/tasks/scraper_task.py`)
非同期で実行されるバックグラウンド関数を作成します。

```python
import asyncio
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.repositories.research_job_repository import research_job_repo
from app.models.research_job import JobStatus

async def run_research_job(job_id: str):
    db: Session = SessionLocal()
    try:
        # 1. Status を running に変更
        job = research_job_repo.get(db, id=job_id)
        if not job:
            return
            
        job.status = JobStatus.running
        db.commit()

        # 2. ここで各 Adapter (Mercari, YahooFlea等) を呼び出して処理
        # (Phase 1 モック処理: 数秒待機して完了とする)
        await asyncio.sleep(5)

        # 3. 完了処理
        job.status = JobStatus.completed
        job.progress = 100
        job.total_items = 10 # モック
        db.commit()

    except Exception as e:
        job.status = JobStatus.failed
        db.commit()
    finally:
        db.close()
```

### 3.2 ルーターへの組み込み (`app/routers/research_jobs.py`)
`BackgroundTasks` を依存性注入し、DBレコード作成後にタスクをエンキューします。

```python
from fastapi import BackgroundTasks
from app.tasks.scraper_task import run_research_job

@router.post("/", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_job(
    req: JobRequest, 
    background_tasks: BackgroundTasks, 
    db: Session = Depends(get_db), 
    current_user_id: str = Depends(get_current_user_id)
):
    # DBに pending で登録
    job = ResearchJobService.create_job(db, user_id=current_user_id, req=req)
    
    # バックグラウンドでスクレイピング処理をキック
    background_tasks.add_task(run_research_job, job.id)
    
    return job
```

## User Review Required
> [!IMPORTANT]
> 非同期処理のアーキテクチャとして、追加のインフラ（Redis）を必要としない **FastAPI BackgroundTasks** で実装を進めてよろしいでしょうか？ 
> 大規模化を見据えてすぐに Celery にしたい場合はお知らせください。承認いただければ、BackgroundTasks での実装をすぐに開始します。

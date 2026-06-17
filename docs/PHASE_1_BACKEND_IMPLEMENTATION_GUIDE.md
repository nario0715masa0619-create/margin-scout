# MarginScout SaaS - Phase 1 Backend 実装ガイド

**バージョン**: 1.0  
**作成日**: 2026-06-16  
**対象アーキテクチャ**: FastAPI + SQLAlchemy 2.0 (同期) + PostgreSQL (Heroku) + Alembic

---

## 1. ディレクトリ構造

```text
margin-scout-backend/
├── app/
│   ├── api/
│   │   ├── deps.py          # 依存性注入 (DBセッション, 現在のユーザー)
│   │   └── v1/
│   │       ├── auth.py      # /auth ルーター
│   │       └── research.py  # /research-jobs ルーター
│   ├── core/
│   │   ├── config.py        # Pydantic Settings
│   │   ├── security.py      # パスワードハッシュ化
│   │   └── jwt.py           # JWTHandler
│   ├── models/
│   │   ├── base.py          # SQLAlchemy Declarative Base
│   │   ├── user.py          # User, Subscription モデル
│   │   └── research.py      # ResearchJob, Candidate モデル
│   ├── repositories/
│   │   ├── base.py          # CRUD Base
│   │   ├── user.py          # UserRepository
│   │   └── research.py      # ResearchJobRepository
│   ├── schemas/             # Pydantic スキーマ
│   ├── services/            # ビジネスロジック
│   │   ├── auth.py          # AuthService
│   │   └── research.py      # ResearchService
│   ├── database.py          # DB 接続管理
│   └── main.py              # FastAPI アプリ初期化
├── tests/                   # Pytest
├── alembic/                 # DB マイグレーション
├── requirements.txt
└── alembic.ini
```

---

## 2. 依存パッケージ (`requirements.txt`)

```text
fastapi>=0.104.1
uvicorn>=0.24.0
sqlalchemy>=2.0.23
psycopg2-binary>=2.9.9
pydantic>=2.5.0
pydantic-settings>=2.1.0
python-jose>=3.3.0
passlib>=1.7.4
bcrypt==4.0.1
python-multipart>=0.0.6
alembic>=1.12.1
pytest>=7.4.3
httpx>=0.25.1
```

---

## 3. コア設定とデータベース (`app/core/config.py`, `app/database.py`)

### 3.1 設定管理 (Pydantic Settings)

```python
# app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "MarginScout SaaS"
    # Heroku では DATABASE_URL が自動付与される
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    class Config:
        env_file = ".env"

settings = Settings()
```

### 3.2 データベース接続 (Heroku 互換)

⚠️ **注意 (Heroku PostgreSQL):** Heroku の `DATABASE_URL` は `postgres://` から始まりますが、SQLAlchemy 1.4+ では `postgresql://` である必要があります。

```python
# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# Heroku の postgres:// を postgresql:// に置換
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,  # 接続切れ対策
    pool_size=5,
    max_overflow=10
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
```

---

## 4. モデル定義 (SQLAlchemy 2.0)

### 4.1 User / Subscription モデル (`app/models/user.py`)

マルチテナントの軸となるテーブルです。

```python
# app/models/user.py
import uuid
from sqlalchemy import Column, String, DateTime, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    plan_type = Column(String(50), default="free")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    jobs = relationship("ResearchJob", back_populates="user", cascade="all, delete-orphan")
```

### 4.2 ResearchJob モデル (`app/models/research.py`)

⚠️ **注意 (テナント分離):** `user_id` を必ず ForeignKey として持たせます。

```python
# app/models/research.py
import uuid
from sqlalchemy import Column, String, DateTime, Integer, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from app.database import Base

class ResearchJob(Base):
    __tablename__ = "research_jobs"

    job_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    
    status = Column(String(50), default="running")
    total_candidates = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="jobs")
```

---

## 5. セキュリティと JWT

### 5.1 パスワードハッシング (`app/core/security.py`)

```python
# app/core/security.py
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
```

### 5.2 JWT ハンドラー (`app/core/jwt.py`)

Access Token (15分) と Refresh Token (7日) の2種類を生成します。

```python
# app/core/jwt.py
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from app.core.config import settings

def create_token(subject: str, expires_delta: timedelta) -> str:
    expire = datetime.utcnow() + expires_delta
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_access_token(user_id: str) -> str:
    return create_token(user_id, timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))

def create_refresh_token(user_id: str) -> str:
    return create_token(user_id, timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))

def verify_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        return user_id
    except JWTError:
        return None
```

---

## 6. 依存性注入 (Dependencies)

⚠️ **注意:** ここで全ての API リクエストに対してテナント（`user_id`）の制約を課します。

```python
# app/api/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.core.jwt import verify_token
from app.repositories.user import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user_id(token: str = Depends(oauth2_scheme)) -> str:
    user_id = verify_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_id

def get_current_user(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```

---

## 7. リポジトリパターン

データアクセスのロジックを分離します。マルチテナントの肝です。

### 7.1 Base Repository (`app/repositories/base.py`)

```python
# app/repositories/base.py
from typing import Generic, TypeVar, Type, Optional
from sqlalchemy.orm import Session

ModelType = TypeVar("ModelType")

class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db

    def get_by_id(self, id: any) -> Optional[ModelType]:
        # 単純なID検索 (テナントに依存しないモデル用)
        return self.db.query(self.model).filter(self.model.id == id).first()

    def create(self, obj_in: dict) -> ModelType:
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
```

### 7.2 ResearchJob Repository (`app/repositories/research.py`)

⚠️ **注意:** `get_by_id_and_user` のように必ず `user_id` で絞り込むメソッドを用意します。

```python
# app/repositories/research.py
from typing import Optional, List
from app.repositories.base import BaseRepository
from app.models.research import ResearchJob

class ResearchJobRepository(BaseRepository[ResearchJob]):
    def __init__(self, db):
        super().__init__(ResearchJob, db)

    def get_by_id_and_user(self, job_id: str, user_id: str) -> Optional[ResearchJob]:
        return self.db.query(self.model).filter(
            self.model.job_id == job_id,
            self.model.user_id == user_id
        ).first()

    def get_multi_by_user(self, user_id: str, skip: int = 0, limit: int = 100) -> List[ResearchJob]:
        return self.db.query(self.model).filter(
            self.model.user_id == user_id
        ).order_by(self.model.created_at.desc()).offset(skip).limit(limit).all()
```

---

## 8. ルーター (Endpoints)

### 8.1 Research ルーター (`app/api/v1/research.py`)

```python
# app/api/v1/research.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user_id
from app.repositories.research import ResearchJobRepository

router = APIRouter()

@router.get("/jobs")
def get_jobs(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    repo = ResearchJobRepository(db)
    jobs = repo.get_multi_by_user(user_id=user_id)
    return jobs

@router.get("/jobs/{job_id}")
def get_job(
    job_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    repo = ResearchJobRepository(db)
    # ⚠️ 必ず user_id と組み合わせてクエリする
    job = repo.get_by_id_and_user(job_id=job_id, user_id=user_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
```

---

## 9. FastAPI 初期化 (`app/main.py`)

```python
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import auth, research

app = FastAPI(title="MarginScout SaaS API")

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://margin-scout.example.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(research.router, prefix="/api/v1/research", tags=["Research"])

@app.get("/health")
def health_check():
    return {"status": "ok"}
```

---

## 10. Alembic マイグレーション

Heroku 環境やローカルでスキーマを同期します。

### 10.1 初期化と設定

```bash
alembic init alembic
```

`alembic/env.py` を編集してモデルを読み込ませます:
```python
from app.database import Base
from app.models import user, research  # モデルをインポート
from app.core.config import settings

target_metadata = Base.metadata

# DB URL を Heroku 対応させる
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL.replace("postgres://", "postgresql://", 1))
```

### 10.2 自動生成と適用

```bash
# マイグレーションファイルの自動生成
alembic revision --autogenerate -m "Initial tables"

# DB に適用
alembic upgrade head
```

---

## 11. Pytest 例

エッジケース (別ユーザーのジョブにアクセスできないこと) をテストします。

```python
# tests/test_research_jobs.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_user_cannot_access_other_users_job(test_db):
    # 1. ユーザー A と B を作成し、それぞれのトークンを取得
    token_a = create_test_user_and_token(test_db, "userA@example.com")
    token_b = create_test_user_and_token(test_db, "userB@example.com")

    # 2. ユーザー A でジョブを作成
    response = client.post("/api/v1/research/jobs", headers={"Authorization": f"Bearer {token_a}"})
    job_id = response.json()["job_id"]

    # 3. ユーザー B のトークンで、ユーザー A のジョブ取得を試みる
    response_b = client.get(f"/api/v1/research/jobs/{job_id}", headers={"Authorization": f"Bearer {token_b}"})
    
    # 4. 検証: 404 (または 403) になること
    assert response_b.status_code == 404
```

---

## ⚠️ チェックリストと実装の注意点

- [x] **PostgreSQL 互換性**: SQLAlchemy で URL を `postgresql://` に変換する処理を入れているか？
- [x] **パスワード管理**: `bcrypt` のコスト係数が適切に設定されているか？平文ログを出していないか？
- [x] **マルチテナント保護**: リポジトリ層のメソッドで、必ず `user_id` を WHERE 句に含めているか？
- [x] **JWT トークン検証**: `get_current_user_id` で、有効期限切れ (ExpiredSignatureError) などの例外を正しく捕捉し、401 を返しているか？
- [x] **Alembic**: 全てのモデルクラスが `env.py` でインポートされ、`Base.metadata` に登録されているか？

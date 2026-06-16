# margin-scout-backend/app/db/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Heroku PostgreSQL 対応 (postgres:// を postgresql:// に置換)
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

# SQLAlchemy エンジンの作成
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,  # 接続切れ対策
    pool_size=5,
    max_overflow=10
)

# セッションファクトリ
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 依存性注入(DI)用の関数
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# margin-scout-backend/app/db/base.py
from sqlalchemy.orm import declarative_base

# 全ての SQLAlchemy モデルの基底クラス
Base = declarative_base()

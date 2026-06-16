# margin-scout-backend/app/security/jwt.py
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from app.config import settings

class JWTHandler:
    @staticmethod
    def _create_token(subject: str, expires_delta: timedelta) -> str:
        expire = datetime.now(timezone.utc) + expires_delta
        to_encode = {"exp": expire, "sub": str(subject)}
        encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        return encoded_jwt

    @staticmethod
    def create_access_token(user_id: str) -> str:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        return JWTHandler._create_token(user_id, expires_delta)

    @staticmethod
    def create_refresh_token(user_id: str) -> str:
        expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        return JWTHandler._create_token(user_id, expires_delta)

    @staticmethod
    def verify_token(token: str) -> Optional[str]:
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            user_id: str = payload.get("sub")
            if not user_id:
                return None
            return user_id
        except jwt.ExpiredSignatureError:
            return None  # トークン有効期限切れ
        except jwt.InvalidTokenError:
            return None  # トークン改ざん・無効

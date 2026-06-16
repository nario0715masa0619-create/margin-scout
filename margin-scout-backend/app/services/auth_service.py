from sqlalchemy.orm import Session
import passlib.handlers.bcrypt
passlib.handlers.bcrypt.detect_wrap_bug = lambda *args, **kwargs: False
from passlib.context import CryptContext
from app.models.user import User
from app.models.subscription import Subscription, SubscriptionTier
from app.security.jwt import JWTHandler

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    @staticmethod
    def get_password_hash(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def register_user(db: Session, email: str, username: str, password: str):
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            return None, {"error": "Email already registered"}

        hashed_password = AuthService.get_password_hash(password)
        new_user = User(email=email, username=username, hashed_password=hashed_password)
        db.add(new_user)
        db.flush()

        subscription = Subscription(user_id=new_user.id, tier=SubscriptionTier.free)
        db.add(subscription)
        
        db.commit()
        db.refresh(new_user)

        tokens = {
            "access_token": JWTHandler.create_access_token(new_user.id),
            "refresh_token": JWTHandler.create_refresh_token(new_user.id)
        }
        return new_user, tokens

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str):
        user = db.query(User).filter(User.email == email).first()
        if not user or not AuthService.verify_password(password, user.hashed_password):
            return None, None
        
        tokens = {
            "access_token": JWTHandler.create_access_token(user.id),
            "refresh_token": JWTHandler.create_refresh_token(user.id)
        }
        return user, tokens

    @staticmethod
    def refresh_access_token(refresh_token: str):
        user_id = JWTHandler.verify_token(refresh_token)
        if not user_id:
            return None
        return JWTHandler.create_access_token(user_id)

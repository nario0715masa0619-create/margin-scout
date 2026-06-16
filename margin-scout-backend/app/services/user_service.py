from sqlalchemy.orm import Session
from app.models.user import User
from app.models.subscription import Subscription

class UserService:
    @staticmethod
    def get_user_by_id(db: Session, user_id: str) -> User | None:
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_user_subscription(db: Session, user_id: str) -> Subscription | None:
        return db.query(Subscription).filter(Subscription.user_id == user_id).first()

    @staticmethod
    def update_user_profile(db: Session, user_id: str, new_username: str) -> User | None:
        user = UserService.get_user_by_id(db, user_id)
        if user:
            user.username = new_username
            db.commit()
            db.refresh(user)
        return user

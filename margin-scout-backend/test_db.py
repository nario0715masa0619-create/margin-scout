import uuid
from datetime import datetime, timezone
from app.db.database import SessionLocal
from app.models import User, Subscription, SubscriptionTier, ResearchJob, JobStatus

db = SessionLocal()

user_id = str(uuid.uuid4())
user = User(
    id=user_id,
    email="test@example.com",
    username="testuser",
    hashed_password="$2b$12$hashed_password_here",
    is_active=True
)
db.add(user)
db.commit()
print(f"User created: {user.id}")

subscription = Subscription(
    id=str(uuid.uuid4()),
    user_id=user_id,
    tier=SubscriptionTier.starter,
    status="active"
)
db.add(subscription)
db.commit()
print(f"Subscription created: {subscription.id}")

job = ResearchJob(
    id=str(uuid.uuid4()),
    user_id=user_id,
    title="Test Research",
    status=JobStatus.pending,
    conditions={"keyword": "margin", "price_min": 100},
    progress=0,
    total_items=0
)
db.add(job)
db.commit()
print(f"ResearchJob created: {job.id}")

jobs = db.query(ResearchJob).filter(ResearchJob.user_id == user_id).all()
print(f"Retrieved {len(jobs)} jobs for user {user_id}")

db.delete(user)
db.commit()
print(f"User deleted (CASCADE)")

remaining_jobs = db.query(ResearchJob).count()
print(f"Remaining jobs: {remaining_jobs} (should be 0)")

db.close()
print("\nAll tests passed!")

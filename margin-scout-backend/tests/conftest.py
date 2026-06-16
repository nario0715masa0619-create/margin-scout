import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.base import Base
from app.db.database import get_db
from app.security.jwt import JWTHandler

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def user_a(db_session):
    from app.services.auth_service import AuthService
    user, _ = AuthService.register_user(db_session, "user_a@example.com", "usera", "password123")
    return user

@pytest.fixture(scope="function")
def user_b(db_session):
    from app.services.auth_service import AuthService
    user, _ = AuthService.register_user(db_session, "user_b@example.com", "userb", "password123")
    return user

@pytest.fixture(scope="function")
def token_a(user_a):
    return JWTHandler.create_access_token(user_a.id)

@pytest.fixture(scope="function")
def token_b(user_b):
    return JWTHandler.create_access_token(user_b.id)

@pytest.fixture(scope="function")
def auth_headers_a(token_a):
    return {"Authorization": f"Bearer {token_a}"}

@pytest.fixture(scope="function")
def auth_headers_b(token_b):
    return {"Authorization": f"Bearer {token_b}"}

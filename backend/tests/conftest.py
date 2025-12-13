"""
Pytest 설정 및 공통 Fixture
"""

import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# 테스트 환경변수 설정 (import 전에 설정해야 함)
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only-32chars!")
os.environ.setdefault("DB_USER", "test")
os.environ.setdefault("DB_PASSWORD", "test")
os.environ.setdefault("DB_NAME", "test_db")
os.environ.setdefault("ENVIRONMENT", "testing")

from app.database import Base, get_db
from app.main import app
from app.models import User
from app.security import get_password_hash, create_access_token


# SQLite In-Memory 테스트 DB
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """테스트용 DB 세션 생성"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """테스트용 FastAPI 클라이언트"""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """테스트용 사용자 생성"""
    from app.models.user import UserRole

    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=get_password_hash("TestPassword123!"),
        role=UserRole.OPERATOR,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_user(db_session):
    """테스트용 관리자 생성"""
    from app.models.user import UserRole

    user = User(
        username="admin",
        email="admin@example.com",
        password_hash=get_password_hash("AdminPassword123!"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    """인증된 요청 헤더"""
    token_data = {
        "sub": test_user.id,
        "username": test_user.username,
        "role": test_user.role.value,
    }
    access_token = create_access_token(token_data)
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def admin_auth_headers(admin_user):
    """관리자 인증 헤더"""
    token_data = {
        "sub": admin_user.id,
        "username": admin_user.username,
        "role": admin_user.role.value,
    }
    access_token = create_access_token(token_data)
    return {"Authorization": f"Bearer {access_token}"}

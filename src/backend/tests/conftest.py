import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Force test configuration
os.environ["USE_SQLITE"] = "true"
os.environ["SQLITE_PATH"] = ":memory:"
os.environ["AWS_MOCK_MODE"] = "true"
os.environ["AI_SERVICE_URL"] = ""

from app.database import Base, get_db
from app.main import app
from app.utils.security import hash_password, create_access_token
from app.models.user import User

# Test in-memory SQLite database
TEST_SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
    expire_on_commit=False
)


@pytest.fixture(scope="function")
def db_session():
    """Creates a fresh database schema for every test function."""
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI TestClient with overridden get_db dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """Creates a sample authenticated user."""
    user = User(
        email="test_user@festival.com",
        full_name="Test User",
        hashed_password=hash_password("securepassword123"),
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    """Generates valid Authorization header with JWT for test_user."""
    token = create_access_token(data={"sub": test_user.email, "user_id": test_user.id})
    return {"Authorization": f"Bearer {token}"}

import os
import shutil
import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app


@pytest.fixture
def tmp_db():
    """Create a fresh SQLite DB per test session."""
    db_path = os.path.join(tempfile.gettempdir(), "test_app.db")
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)  # noqa: N806
    yield TestingSession
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    os.unlink(db_path)


@pytest.fixture
def client(tmp_db):
    def override_get_db():
        db = tmp_db()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client):
    """Register a test user and return auth headers."""
    client.post("/api/auth/register", json={"email": "test@test.com", "password": "secret123"})
    res = client.post("/api/auth/login", json={"email": "test@test.com", "password": "secret123"})
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def upload_dir():
    d = tempfile.mkdtemp()
    from app import config

    old = config.UPLOAD_DIR
    config.UPLOAD_DIR = d
    yield d
    config.UPLOAD_DIR = old
    shutil.rmtree(d, ignore_errors=True)

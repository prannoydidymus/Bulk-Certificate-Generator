import os
import shutil
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.database as database
from app.database import Base, get_db
from app.main import app
import app.config as config
import app.services.storage as storage_module


@pytest.fixture(scope="session")
def test_temp_dir():
    temp_dir = tempfile.mkdtemp(prefix="cert_test_")
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope="function")
def db_session(test_temp_dir):
    # Isolated SQLite database per test function
    test_db_path = test_temp_dir / f"test_{os.getpid()}_{id(test_temp_dir)}.db"
    test_engine = create_engine(
        f"sqlite:///{test_db_path}",
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    Base.metadata.create_all(bind=test_engine)

    # Patch storage directory for tests
    test_storage_dir = test_temp_dir / "storage"
    test_storage_dir.mkdir(parents=True, exist_ok=True)
    storage_module.STORAGE_DIR = test_storage_dir
    config.STORAGE_DIR = test_storage_dir

    # Patch database.SessionLocal for background tasks
    original_session_local = database.SessionLocal
    database.SessionLocal = TestingSessionLocal

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        database.SessionLocal = original_session_local
        Base.metadata.drop_all(bind=test_engine)
        if test_db_path.exists():
            try:
                os.remove(test_db_path)
            except OSError:
                pass


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

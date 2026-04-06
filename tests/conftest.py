"""Fixtures compartilhadas para todos os testes."""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Garante que src/ está no path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.core.database import get_db, init_db, make_session_factory
from src.core.models import Base


@pytest.fixture(scope="function")
def engine():
    """Engine SQLite em memória — isolado por teste."""
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    init_db(eng)
    yield eng
    eng.dispose()


@pytest.fixture(scope="function")
def session(engine):
    """Session vinculada ao engine em memória."""
    factory = make_session_factory(engine)
    db = factory()
    yield db
    db.close()


@pytest.fixture(scope="function")
def client(engine):
    """TestClient FastAPI com DB em memória injetado."""
    from src.api.main import app

    factory = make_session_factory(engine)

    def _override_get_db():
        db = factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

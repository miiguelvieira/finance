"""Engine SQLAlchemy, session factory e utilitários de banco."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from src.core.models import Base


def get_engine(database_url: str = "sqlite:///data/finance.db") -> Engine:
    # Garante que o diretório existe para SQLite
    if database_url.startswith("sqlite:///"):
        db_path = Path(database_url.replace("sqlite:///", ""))
        db_path.parent.mkdir(parents=True, exist_ok=True)

    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False} if "sqlite" in database_url else {},
    )

    # Habilita foreign keys no SQLite
    if "sqlite" in database_url:
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_conn, _):
            dbapi_conn.execute("PRAGMA foreign_keys=ON")

    return engine


def init_db(engine: Engine) -> None:
    """Cria todas as tabelas se não existirem."""
    Base.metadata.create_all(bind=engine)


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_session(session_factory: sessionmaker[Session]) -> Generator[Session, None, None]:
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ── Instância global (criada sob demanda) ────────────────────────────────────

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def setup(database_url: str = "sqlite:///data/finance.db") -> Engine:
    global _engine, _SessionLocal
    _engine = get_engine(database_url)
    _SessionLocal = make_session_factory(_engine)
    init_db(_engine)
    return _engine


def get_db() -> Generator[Session, None, None]:
    """Dependência FastAPI — yield session e fecha ao fim do request."""
    if _SessionLocal is None:
        raise RuntimeError("Banco não inicializado. Chame setup() primeiro.")
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()

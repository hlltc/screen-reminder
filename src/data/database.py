"""Database initialization and session management."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.data.models import Base


_engine = None
_SessionLocal: sessionmaker | None = None


def init_db(db_path: Path) -> None:
    """Create engine and tables.  Safe to call multiple times."""
    global _engine, _SessionLocal

    db_path.parent.mkdir(parents=True, exist_ok=True)
    _engine = create_engine(f"sqlite:///{db_path}", echo=False)
    Base.metadata.create_all(_engine)
    _SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False)


def get_session() -> Session:
    """Return a new SQLAlchemy session.  Caller must close it."""
    if _SessionLocal is None:
        raise RuntimeError("Database not initialised – call init_db() first")
    return _SessionLocal()


def get_engine():
    if _engine is None:
        raise RuntimeError("Database not initialised – call init_db() first")
    return _engine

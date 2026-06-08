import os
import sys
from pathlib import Path

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError


# Ensure the tests database config is used before importing database/models.
os.environ.setdefault("ENVIRONMENT", "tests")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database import Base, SessionLocal, engine  # noqa: E402


def _truncate_all_tables(session):
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    if not table_names:
        return

    quoted = ", ".join(f'"{name}"' for name in table_names)
    session.execute(text(f"TRUNCATE TABLE {quoted} RESTART IDENTITY CASCADE"))
    session.commit()


@pytest.fixture(scope="session")
def db_engine():
    """Provide a live engine for the configured test database."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        pytest.skip(f"Could not connect to test database: {exc}")

    Base.metadata.create_all(bind=engine)
    yield engine


@pytest.fixture()
def db_session(db_engine):
    """Return a clean SQLAlchemy session for each test."""
    session = SessionLocal()
    _truncate_all_tables(session)
    try:
        yield session
    finally:
        session.rollback()
        _truncate_all_tables(session)
        session.close()

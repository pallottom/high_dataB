import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import URL
from sqlalchemy.exc import OperationalError

from database import DB_HOST, DB_NAME, DB_PASS, DB_PORT, DB_USER


def test_configured_test_database_exists():
    maintenance_url = URL.create(
        "postgresql+psycopg2",
        username=DB_USER,
        password=DB_PASS,
        host=DB_HOST,
        port=int(DB_PORT),
        database="postgres",
    )
    maintenance_engine = create_engine(maintenance_url, future=True)

    try:
        try:
            with maintenance_engine.connect() as conn:
                result = conn.execute(
                    text("SELECT 1 FROM pg_database WHERE datname = :db_name"),
                    {"db_name": DB_NAME},
                )
                assert result.scalar() == 1, f"Database {DB_NAME!r} does not exist on {DB_HOST}:{DB_PORT}"
        except OperationalError as exc:
            pytest.skip(f"Test database not available: {exc}")
    finally:
        maintenance_engine.dispose()


def test_db_connection(db_engine):
    with db_engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        assert result.scalar() == 1


def test_required_tables_exist(db_engine):
    inspector = inspect(db_engine)
    tables = set(inspector.get_table_names())

    required_tables = {
        "projects",
        "screens",
        "plates",
        "wells",
        "specimens",
        "human_donor",
        "mouse_donor",
        "virus",
        "bacteria",
        "essay",
        "measurement_values",
        "substances",
        "conditionclasses",
        "conditions",
        "treatments",
        "experiments",
    }

    missing = sorted(required_tables - tables)
    assert not missing, f"Missing tables: {missing}. Existing tables: {sorted(tables)}"

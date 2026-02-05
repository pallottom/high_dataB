from config.db_loader import get_engine
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
import pytest


# Can I connect to the DB? Does the DB exist?
def test_db_connection():
    engine = get_engine("test")
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1
    except OperationalError as e:
        pytest.skip(f"Test database not available: {e}")


# Does the table specimen exist? Change name or list all the tables
def test_specimens_table_exists():
    engine = get_engine("test")
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_name = 'specimens' 
                );
            """))
            assert result.scalar() is True
    except OperationalError as e:
        pytest.skip(f"Test database not available: {e}")


if __name__ == "__main__":
    test_db_connection()
    print("Schema test passed")
    test_specimens_table_exists()
    print("Tables test passed")

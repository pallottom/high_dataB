"""
Create only the single-table measurement schema.

Tables:
- measurement_experiments
- primary_features
- measurement_values
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import inspect
from sqlalchemy_utils import create_database, database_exists

from database import Base, engine
from models.measurement import Essay, PrimaryFeature, MeasurementValue


TARGET_TABLES = [
    Essay.__table__,
    PrimaryFeature.__table__,
    MeasurementValue.__table__,
]


if __name__ == "__main__":
    if not database_exists(engine.url):
        create_database(engine.url)
        print(f"Database created at {engine.url}")
    else:
        print(f"Database already exists at {engine.url}")

    inspector = inspect(engine)
    existing = set(inspector.get_table_names())

    to_create = [table for table in TARGET_TABLES if table.name not in existing]
    already_present = [table for table in TARGET_TABLES if table.name in existing]

    if to_create:
        Base.metadata.create_all(bind=engine, tables=to_create)
        print("Created single-measurement tables:")
        for table in to_create:
            print(f" - {table.name}")
    else:
        print("No new single-measurement tables needed.")

    if already_present:
        print("Already present:")
        for table in already_present:
            print(f" - {table.name}")

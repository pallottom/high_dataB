# create_db.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database import engine, Base
from models import *
from sqlalchemy_utils import database_exists, create_database


if __name__ == "__main__":
    # Create the database if it doesn't exist
    if not database_exists(engine.url):
        create_database(engine.url)
        print(f"📀 Database created at {engine.url}")
    else:
        print(f"ℹ️ Database already exists at {engine.url}")

    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✅ All tables created")
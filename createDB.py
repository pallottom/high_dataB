# create_db.py
from database import engine, Base
from models import *
from sqlalchemy_utils import database_exists, create_database


if __name__ == "__main__":
    # 1. Create the database if it doesn't exist
    if not database_exists(engine.url):
        create_database(engine.url)
        print(f"📀 Database created at {engine.url}")
    else:
        print(f"ℹ️ Database already exists at {engine.url}")

    # 2. Create all tables
    Base.metadata.create_all(bind=engine)
    print("✅ All tables created")
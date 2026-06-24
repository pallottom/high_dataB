# drop_db.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy_utils import database_exists, drop_database
from sqlalchemy import text, create_engine
from database import SessionLocal, engine


"""# Create a session
db = SessionLocal()

try:
    # do queries here
    result = db.execute(text("SELECT now()")).fetchone()
    print("Current time:", result[0])
finally:
    db.close()
"""

db_name = engine.url.database

engine.dispose()

admin_url = engine.url.set(database="postgres")
admin_engine = create_engine(admin_url)

with admin_engine.begin() as conn:
    conn.execute(text("""
        SELECT pg_terminate_backend(pid)
        FROM pg_stat_activity
        WHERE datname = :db
          AND pid <> pg_backend_pid()
    """), {"db": db_name})

drop_database(engine.url)



if __name__ == "__main__":
    if database_exists(engine.url):
        confirm = input(f"⚠️  Are you sure you want to permanently delete the database '{engine.url.database}'? (y/N): ")
        if confirm.lower() == "y":
            engine.dispose()
            drop_database(engine.url)
            print(f"💥 Database '{engine.url.database}' dropped successfully!")
        else:
            print("❌ Operation cancelled. Database was not dropped.")
    else:
        print(f"ℹ️ Database '{engine.url.database}' does not exist.")

    
# drop_db.py
from sqlalchemy_utils import database_exists, drop_database
from sqlalchemy import text
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



if __name__ == "__main__":
    if database_exists(engine.url):
        confirm = input(f"⚠️  Are you sure you want to permanently delete the database '{engine.url.database}'? (y/N): ")
        if confirm.lower() == "y":
            drop_database(engine.url)
            print(f"💥 Database '{engine.url.database}' dropped successfully!")
        else:
            print("❌ Operation cancelled. Database was not dropped.")
    else:
        print(f"ℹ️ Database '{engine.url.database}' does not exist.")

    
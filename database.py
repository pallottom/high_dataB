import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

# Load environment variables from a .env file (optional but recommended)
load_dotenv()

# Build connection string dynamically
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "test_marta_5")

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create engine
engine = create_engine(
    DATABASE_URL,
    echo=True,            # Logs SQL queries
    pool_size=10,         # Connection pool size
    max_overflow=20,      # Extra connections allowed above pool_size
    pool_timeout=30,      # Timeout before giving up on getting a connection
    pool_pre_ping=True,   # Checks connections before using them (avoids stale connections)
    future=True           # Use SQLAlchemy 2.0 style
)

# Session factory
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

# Base class for models
Base = declarative_base()

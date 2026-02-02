import os
import toml
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Get the current environment (default to 'development')
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Load config from TOML file
with open("config.toml", "r") as config_file:
    config = toml.load(config_file)

# Get environment-specific config
env_config = config.get(ENVIRONMENT, config.get("development"))
db_config = env_config.get("database", {})
engine_config = env_config.get("engine", {})

# Build connection string - allow env vars to override config file
DB_USER = os.getenv("DB_USER", db_config.get("user", "postgres"))
DB_PASS = os.getenv("DB_PASS", db_config.get("password", "postgres"))
DB_HOST = os.getenv("DB_HOST", db_config.get("host", "localhost"))
DB_PORT = os.getenv("DB_PORT", db_config.get("port", "5432"))
DB_NAME = os.getenv("DB_NAME", db_config.get("name", "hi_dataB_dev"))

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create engine with environment-specific settings
engine = create_engine(
    DATABASE_URL,
    echo=engine_config.get("echo", True),
    pool_size=engine_config.get("pool_size", 10),
    max_overflow=engine_config.get("max_overflow", 20),
    pool_timeout=engine_config.get("pool_timeout", 30),
    pool_pre_ping=engine_config.get("pool_pre_ping", True),
    future=True
)

# Session factory
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

# Base class for models
Base = declarative_base()


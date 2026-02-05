import os
import toml
from sqlalchemy import create_engine
from dotenv import load_dotenv
from pathlib import Path

# Load .env if present
load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT.joinpath("config.toml")

# Read toml config
if CONFIG_PATH.exists():
    config = toml.load(CONFIG_PATH)
else:
    config = {}


def _resolve_env_name(env_name: str | None) -> str:
    if not env_name:
        return os.getenv("ENVIRONMENT", "development")
    # Accept 'test' or 'tests'
    if env_name == "test":
        return "tests"
    return env_name


def get_engine(env: str | None = None):
    """Return a SQLAlchemy engine for the given environment.

    env can be one of: 'development', 'tests', 'operational'. If None,
    uses ENVIRONMENT env var or defaults to 'development'.
    """
    env = _resolve_env_name(env)
    env_config = config.get(env, config.get("development", {}))
    db_config = env_config.get("database", {})
    engine_cfg = env_config.get("engine", {})

    # Allow environment variables to override
    DB_USER = os.getenv("DB_USER", db_config.get("user", "postgres"))
    DB_PASS = os.getenv("DB_PASS", db_config.get("password", "postgres"))
    DB_HOST = os.getenv("DB_HOST", db_config.get("host", "localhost"))
    DB_PORT = os.getenv("DB_PORT", db_config.get("port", "5432"))
    DB_NAME = os.getenv("DB_NAME", db_config.get("name", "hi_dataB_test"))

    DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

    engine = create_engine(
        DATABASE_URL,
        echo=engine_cfg.get("echo", False),
        pool_size=engine_cfg.get("pool_size", 5),
        max_overflow=engine_cfg.get("max_overflow", 10),
        pool_timeout=engine_cfg.get("pool_timeout", 30),
        pool_pre_ping=engine_cfg.get("pool_pre_ping", True),
        future=True,
    )

    return engine

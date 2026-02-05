import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Ensure project root is on sys.path so tests can import project packages
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Force tests to use the test environment file and environment
# Load .env.tests (override any existing env vars)
env_path = PROJECT_ROOT.joinpath('.env.tests')
if env_path.exists():
    load_dotenv(dotenv_path=str(env_path), override=True)

# Ensure ENVIRONMENT is set to 'tests'
os.environ.setdefault('ENVIRONMENT', 'tests')

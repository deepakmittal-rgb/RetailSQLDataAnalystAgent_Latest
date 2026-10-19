"""
Retail SQL Data Analyst Agent - Configuration
Manages environment variables, database credentials, safety thresholds, and model parameters.
"""

import os
import sys
from pathlib import Path

# Ensure root in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Load .env if present (try python-dotenv, otherwise simple parser)
env_file = BASE_DIR / ".env"
if env_file.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=env_file)
    except ImportError:
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    val = val.strip().strip("'\"")
                    if key.strip() not in os.environ:
                        os.environ[key.strip()] = val
DATA_DIR = BASE_DIR / "data"
DATABASE_DIR = BASE_DIR / "database"
OUTPUTS_DIR = BASE_DIR / "outputs"
EVIDENCE_DIR = BASE_DIR / "evidence"

# Database Configuration
DB_TYPE = os.getenv("DB_TYPE", "sqlite").lower()  # "sqlite" or "mysql"
SQLITE_DB_PATH = Path(os.getenv("SQLITE_DB_PATH", str(BASE_DIR / "retail.db")))

MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "retail_db")

# Model & Tiger Gateway Configuration
TIGER_GATEWAY_URL = os.getenv("TIGER_GATEWAY_URL", "https://api.tigeranalytics.com/gateway/v1")
TIGER_GATEWAY_API_KEY = os.getenv("TIGER_GATEWAY_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemini-3.8-flash")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.0"))

# Safety Configuration
MAX_ROW_LIMIT = int(os.getenv("MAX_ROW_LIMIT", "100"))
DEFAULT_ROW_LIMIT = int(os.getenv("DEFAULT_ROW_LIMIT", "25"))
QUERY_TIMEOUT_SECONDS = int(os.getenv("QUERY_TIMEOUT_SECONDS", "10"))

# Memory Configuration
MEMORY_WINDOW_SIZE = int(os.getenv("MEMORY_WINDOW_SIZE", "5"))

# Allowed Tables in Retail Schema
ALLOWED_TABLES = {
    "customers",
    "products",
    "stores",
    "sales_transactions",
    "returns",
    "v_sales_extended"
}

# Forbidden SQL keywords and tokens for read-only safety
FORBIDDEN_KEYWORDS = [
    "DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE",
    "REPLACE", "CREATE", "GRANT", "REVOKE", "EXEC", "EXECUTE",
    "CALL", "MERGE", "UPSERT", "INTO OUTFILE", "DUMPFILE", "LOAD DATA"
]

"""Configuration Module for Notion Tracker.

Loads settings from environment variables or defaults to secure development parameters.
Provides typed access to API secrets, rate limits, and network options.
"""

import os
from pathlib import Path

# Load .env if present
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
try:
    from dotenv import load_dotenv
    if ENV_PATH.exists():
        load_dotenv(ENV_PATH)
    else:
        load_dotenv()
except ImportError:
    pass


def _safe_int(val: str, default: int) -> int:
    if not val or not str(val).strip():
        return default
    try:
        return int(val)
    except (ValueError, TypeError):
        return default

def _safe_float(val: str, default: float) -> float:
    if not val or not str(val).strip():
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


# Webhook Ingestion Security
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "super_secret_enterprise_notion_key_2026")
MAX_TIMESTAMP_DRIFT_SECONDS = _safe_int(os.getenv("MAX_TIMESTAMP_DRIFT_SECONDS"), 300)

# Notion Configuration
NOTION_TOKEN = os.getenv("NOTION_TOKEN", "")
NOTION_PARENT_PAGE_ID = os.getenv("NOTION_PARENT_PAGE_ID", "")
NOTION_TASKS_DB_ID = os.getenv("NOTION_TASKS_DB_ID", "mock_tasks_db_001")
NOTION_LOGS_DB_ID = os.getenv("NOTION_LOGS_DB_ID", "mock_logs_db_002")
NOTION_USERS_DB_ID = os.getenv("NOTION_USERS_DB_ID", "mock_users_db_003")


# Storage Mode: "live" (requires valid token), "mock" (in-memory/file SQLite), "hybrid" (auto-fallback)
STORAGE_MODE = os.getenv("STORAGE_MODE", "hybrid")

# Token Bucket Rate Limiter
RATE_LIMIT_CAPACITY = _safe_float(os.getenv("RATE_LIMIT_CAPACITY"), 10.0)
RATE_LIMIT_REPLENISH_RATE = _safe_float(os.getenv("RATE_LIMIT_REPLENISH_RATE"), 2.0)

# Outbound Notification Targets
TEAMS_WEBHOOK_URL = os.getenv("TEAMS_WEBHOOK_URL", "")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
SENDGRID_FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL", "aryansharma10122006@gmail.com")
NOTIFICATION_RECIPIENT_EMAIL = os.getenv("NOTIFICATION_RECIPIENT_EMAIL", "aryansharma10122006@gmail.com")

# Biometric & OTP Gate
SMS_OTP_SECRET = os.getenv("SMS_OTP_SECRET", "enterprise_totp_random_seed_key_99")
ADMIN_OVERRIDE_PIN = os.getenv("ADMIN_OVERRIDE_PIN", "748291")

# Server & Network Ports
GATEWAY_HOST = os.getenv("GATEWAY_HOST", "0.0.0.0")
GATEWAY_PORT = _safe_int(os.getenv("PORT") or os.getenv("GATEWAY_PORT"), 8000)
DASHBOARD_PORT = _safe_int(os.getenv("DASHBOARD_PORT"), 8501)


# 60-Minute Background Daemon Polling & State Synchronization
POLL_INTERVAL_MINUTES = _safe_int(os.getenv("POLL_INTERVAL_MINUTES"), 60)
POLL_INTERVAL_SECONDS = _safe_float(os.getenv("POLL_INTERVAL_SECONDS"), float(POLL_INTERVAL_MINUTES * 60))


# Storage paths
import tempfile

is_serverless = bool(os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME") or os.getenv("LAMBDA_TASK_ROOT"))

if is_serverless:
    DATA_DIR = Path(tempfile.gettempdir()) / "notion_tracker_data"
    REPORTS_DIR = Path(tempfile.gettempdir()) / "notion_tracker_reports"
else:
    DATA_DIR = BASE_DIR / "data"
    REPORTS_DIR = BASE_DIR / "reports"

try:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
except (PermissionError, OSError):
    DATA_DIR = Path(tempfile.gettempdir()) / "notion_tracker_data"
    DATA_DIR.mkdir(parents=True, exist_ok=True)

try:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
except (PermissionError, OSError):
    REPORTS_DIR = Path(tempfile.gettempdir()) / "notion_tracker_reports"
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

DB_FILE = DATA_DIR / "notion_tracker.sqlite"
CONFIG_FILE = DATA_DIR / "system_config.json"




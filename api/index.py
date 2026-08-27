"""Vercel Serverless Entry Point for Notion Tracker FastAPI Gateway."""
import sys
from pathlib import Path

# Add project root to sys.path for Vercel Serverless runtime
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from webhook_gateway import app

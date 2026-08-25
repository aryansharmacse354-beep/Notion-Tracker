"""Notion Tracker Enterprise Platform Launcher.

Launches:
1. Streamlit Control Portal on http://localhost:8501
2. FastAPI Single-Page Web App & Webhook Gateway on http://localhost:8000
3. Background Worker Daemon (main.py)
"""

import sys
from run_all import start_all_services

if __name__ == "__main__":
    start_all_services()

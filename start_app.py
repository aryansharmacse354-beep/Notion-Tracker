"""One-Click Launcher for Notion Tracker Enterprise Platform.

Double-clicking or running `python start_app.py`:
1. Cleanly recycles any stale processes on ports 8000 and 8501.
2. Launches FastAPI, Streamlit, and the background daemon.
3. Automatically opens your default web browser to http://localhost:8000 and http://localhost:8501.
"""

import subprocess
import sys
import time
import webbrowser
import os

def launch():
    print("=" * 65)
    print(" 🚀 LAUNCHING NOTION TRACKER ENTERPRISE PLATFORM")
    print("=" * 65)

    # 1. Clean up stale ports
    print("[*] Releasing any stale port locks on 8000 and 8501...")
    try:
        if os.name == 'nt':
            subprocess.run(
                ["powershell", "-Command", "Get-Process -Id (Get-NetTCPConnection -LocalPort 8000,8501 -ErrorAction SilentlyContinue).OwningProcess -ErrorAction SilentlyContinue | Stop-Process -Force"],
                capture_output=True,
                text=True,
            )
    except Exception:
        pass

    time.sleep(1)

    # 2. Start FastAPI on 8000
    print("[*] Starting Web App & Gateway on http://127.0.0.1:8000...")
    p_gw = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "webhook_gateway:app", "--host", "127.0.0.1", "--port", "8000"],
    )

    # 3. Start Background Daemon
    print("[*] Starting Worker Daemon...")
    p_daemon = subprocess.Popen(
        [sys.executable, "main.py"],
    )

    # 4. Start Streamlit on 8501
    print("[*] Starting Streamlit Portal on http://127.0.0.1:8501...")
    p_ui = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "dashboard.py", "--server.address", "127.0.0.1", "--server.port", "8501", "--server.headless", "true", "--browser.gatherUsageStats", "false"],
    )

    # 5. Wait for servers to spin up, then open browser
    print("[*] Waiting 2 seconds for services to bind...")
    time.sleep(2.5)

    print("[*] Automatically opening browser...")
    webbrowser.open("http://localhost:8000")
    webbrowser.open("http://localhost:8501")

    print("\n" + "=" * 65)
    print(" ✅ NOTION TRACKER IS RUNNING!")
    print(" • Single-Page Web App: http://localhost:8000")
    print(" • Streamlit Portal:    http://localhost:8501")
    print(" • OpenAPI Docs:        http://localhost:8000/docs")
    print("=" * 65 + "\n")

    try:
        p_gw.wait()
    except KeyboardInterrupt:
        print("\n[*] Stopping all services...")
        p_gw.terminate()
        p_daemon.terminate()
        p_ui.terminate()

if __name__ == "__main__":
    launch()

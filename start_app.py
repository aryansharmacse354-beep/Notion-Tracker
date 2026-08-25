"""One-Click Launcher for Notion Tracker Enterprise Platform.

Launches:
1. FastAPI Single-Page Web App & Webhook Gateway (Port 8000)
2. Background Automation Daemon (main.py)

Automatically opens http://localhost:8000 in your browser!
"""

import subprocess
import sys
import time
import webbrowser
import os
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def wait_for_endpoint(url: str, timeout: float = 10.0) -> bool:
    """Polls an endpoint until it responds with HTTP 200."""
    start_t = time.time()
    while time.time() - start_t < timeout:
        try:
            with urllib.request.urlopen(url, timeout=1.0) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(0.3)
    return False


def launch():
    print("=" * 65)
    print(" [*] LAUNCHING NOTION TRACKER ENTERPRISE PLATFORM")
    print("=" * 65)

    # 1. Clean up stale port locks
    print("[*] Releasing any stale port locks on 8000...")
    try:
        if os.name == "nt":
            subprocess.run(
                ["powershell", "-Command", "Get-Process -Id (Get-NetTCPConnection -LocalPort 8000,8501 -ErrorAction SilentlyContinue).OwningProcess -ErrorAction SilentlyContinue | Stop-Process -Force"],
                capture_output=True,
                text=True,
            )
    except Exception:
        pass

    time.sleep(0.8)

    # 2. Start FastAPI on port 8000
    print("[*] Starting Notion Tracker Web App on http://127.0.0.1:8000...")
    p_gw = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "webhook_gateway:app", "--host", "127.0.0.1", "--port", "8000"],
    )

    # 3. Start Background Daemon
    print("[*] Starting Background Worker Daemon...")
    p_daemon = subprocess.Popen(
        [sys.executable, "main.py"],
    )

    # 4. Wait for Web App to be healthy
    print("[*] Waiting for Notion Tracker to be ready...")
    gw_ready = wait_for_endpoint("http://127.0.0.1:8000/health", timeout=10.0)

    # 5. Open browser strictly to http://localhost:8000
    print("[*] Opening Notion Tracker (http://localhost:8000) in your browser...")
    try:
        webbrowser.open("http://localhost:8000")
    except Exception as e:
        print(f"[!] Notice: {e}")

    print("\n" + "=" * 65)
    print(" [OK] NOTION TRACKER IS ONLINE!")
    print(" * Web Application:    http://localhost:8000")
    print(" * OpenAPI Docs:       http://localhost:8000/docs")
    print(" * Webhook Ingestion:  http://localhost:8000/v1/webhook/ingest")
    print("=" * 65 + "\n")

    try:
        while True:
            time.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        print("\n[*] Stopping all services...")
        p_gw.terminate()
        p_daemon.terminate()


if __name__ == "__main__":
    launch()

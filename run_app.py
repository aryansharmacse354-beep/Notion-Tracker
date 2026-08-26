"""Unified Application Launcher for Notion Tracker.

Runs all platform services concurrently:
1. FastAPI Webhook Gateway & SPA (Port 8000)
2. Background Automation Daemon (main.py)
3. Streamlit HITL Control Portal (Port 8501)
"""

import subprocess
import sys
import time
import os
import webbrowser
import urllib.request
from config import GATEWAY_HOST, GATEWAY_PORT, DASHBOARD_PORT

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def wait_for_endpoint(url: str, timeout: float = 12.0) -> bool:
    """Polls an endpoint until it responds with HTTP 200."""
    start_t = time.time()
    while time.time() - start_t < timeout:
        try:
            with urllib.request.urlopen(url, timeout=1.0) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(0.4)
    return False


def run_app():
    print("=" * 65)
    print(" [*] LAUNCHING NOTION TRACKER ENTERPRISE PLATFORM (run_app)")
    print("=" * 65)

    # 1. Clean up stale port locks on Windows
    print("[*] Releasing any stale port locks on 8000 / 8501...")
    try:
        if os.name == "nt":
            subprocess.run(
                ["powershell", "-Command", "Get-Process -Id (Get-NetTCPConnection -LocalPort 8000,8501 -ErrorAction SilentlyContinue).OwningProcess -ErrorAction SilentlyContinue | Stop-Process -Force"],
                capture_output=True,
                text=True,
            )
    except Exception:
        pass

    time.sleep(1.0)
    processes = []

    try:
        # 1. Start FastAPI Gateway
        print(f"[*] Starting FastAPI Webhook Gateway on http://127.0.0.1:{GATEWAY_PORT}...")
        p_gw = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "webhook_gateway:app", "--host", "127.0.0.1", "--port", str(GATEWAY_PORT)],
        )
        processes.append(("FastAPI Gateway", p_gw))

        time.sleep(1.2)

        # 2. Start Background Daemon
        print("[*] Starting Background Automation Daemon (main.py)...")
        p_daemon = subprocess.Popen(
            [sys.executable, "main.py"],
        )
        processes.append(("Worker Daemon", p_daemon))

        time.sleep(1.0)

        # 3. Start Streamlit HITL Dashboard
        print(f"[*] Starting Streamlit HITL Dashboard on http://127.0.0.1:{DASHBOARD_PORT}...")
        p_ui = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", "dashboard.py", "--server.address", "127.0.0.1", "--server.port", str(DASHBOARD_PORT), "--server.headless", "false", "--server.enableCORS", "false", "--server.enableXsrfProtection", "false", "--browser.gatherUsageStats", "false"],
        )
        processes.append(("Streamlit Dashboard", p_ui))

        # 4. Wait for services to be ready
        print("[*] Waiting for services to initialize...")
        wait_for_endpoint(f"http://127.0.0.1:{GATEWAY_PORT}/health", timeout=8.0)

        print("\n" + "=" * 65)
        print(" [OK] ALL NOTION TRACKER SERVICES ONLINE!")
        print(f" * Streamlit Dashboard:   http://localhost:{DASHBOARD_PORT}")
        print(f" * Web Application (SPA): http://localhost:{GATEWAY_PORT}")
        print(f" * OpenAPI Interactive:   http://localhost:{GATEWAY_PORT}/docs")
        print(f" * Ingestion Webhook:     http://localhost:{GATEWAY_PORT}/v1/webhook/ingest")
        print(" Press Ctrl+C in terminal to stop all services.")
        print("=" * 65 + "\n")

        # Open Dashboard in browser
        try:
            webbrowser.open(f"http://localhost:{DASHBOARD_PORT}")
        except Exception:
            pass

        while True:
            for name, proc in processes:
                ret = proc.poll()
                if ret is not None:
                    print(f"[!] Notice: {name} (PID {proc.pid}) stopped with code {ret}.")
            time.sleep(2)

    except (KeyboardInterrupt, SystemExit):
        print("\n[*] Stopping all Notion Tracker services...")
        for name, proc in processes:
            if proc.poll() is None:
                print(f"[*] Terminating {name} (PID {proc.pid})...")
                proc.terminate()
                try:
                    proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    proc.kill()
        print("[*] All services stopped cleanly.")


if __name__ == "__main__":
    run_app()

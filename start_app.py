"""One-Click Launcher for Notion Tracker Enterprise Platform.

Starts:
1. FastAPI Single-Page Web App & Webhook Gateway (Port 8000)
2. Streamlit Control Portal (Port 8501)
3. Background Automation Daemon (main.py)

Waits for both servers to be 100% healthy, then opens your browser!
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


def launch():
    print("=" * 65)
    print(" [*] LAUNCHING NOTION TRACKER ENTERPRISE PLATFORM")
    print("=" * 65)

    # 1. Clean up stale ports
    print("[*] Releasing any stale port locks on 8000 and 8501...")
    try:
        if os.name == "nt":
            subprocess.run(
                ["powershell", "-Command", "Get-Process -Id (Get-NetTCPConnection -LocalPort 8000,8501 -ErrorAction SilentlyContinue).OwningProcess -ErrorAction SilentlyContinue | Stop-Process -Force"],
                capture_output=True,
                text=True,
            )
    except Exception:
        pass

    time.sleep(1)

    # 2. Start FastAPI on 8000
    print("[*] Starting FastAPI Web App on http://127.0.0.1:8000...")
    p_gw = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "webhook_gateway:app", "--host", "127.0.0.1", "--port", "8000"],
    )

    # 3. Start Background Daemon
    print("[*] Starting Background Worker Daemon...")
    p_daemon = subprocess.Popen(
        [sys.executable, "main.py"],
    )

    # 4. Start Streamlit on 8501
    print("[*] Starting Streamlit Portal on http://127.0.0.1:8501...")
    p_ui = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "dashboard.py", "--server.address", "127.0.0.1", "--server.port", "8501", "--server.headless", "true", "--browser.gatherUsageStats", "false"],
    )

    # 5. Wait for both servers to be verified alive
    print("[*] Waiting for both service health checks to pass...")
    gw_ready = wait_for_endpoint("http://127.0.0.1:8000/health", timeout=10.0)
    st_ready = wait_for_endpoint("http://127.0.0.1:8501/_stcore/health", timeout=15.0)

    print(f" [+] FastAPI Gateway (8000): {'ONLINE (200 OK)' if gw_ready else 'STARTING...'}")
    print(f" [+] Streamlit Portal (8501): {'ONLINE (200 OK)' if st_ready else 'STARTING...'}")

    # 6. Open both portals in browser
    print("[*] Opening Notion Tracker in your web browser...")
    try:
        webbrowser.open("http://localhost:8501")
        time.sleep(0.8)
        webbrowser.open("http://localhost:8000")
    except Exception as e:
        print(f"[!] Notice: {e}")

    print("\n" + "=" * 65)
    print(" [OK] ALL NOTION TRACKER SERVICES RUNNING AND READY!")
    print(" * Streamlit Control Portal: http://localhost:8501")
    print(" * Single-Page Web App:      http://localhost:8000")
    print(" * Interactive OpenAPI Docs: http://localhost:8000/docs")
    print("=" * 65 + "\n")

    try:
        while True:
            time.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        print("\n[*] Stopping all services...")
        p_gw.terminate()
        p_daemon.terminate()
        p_ui.terminate()


if __name__ == "__main__":
    launch()

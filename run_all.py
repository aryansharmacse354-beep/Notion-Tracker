"""Multi-process launcher for Notion Tracker.

Launches the FastAPI Webhook Gateway, the persistent Worker Daemon, and the
interactive Streamlit Control Portal concurrently.
"""

import subprocess
import sys
import time
import signal
import os
from config import GATEWAY_HOST, GATEWAY_PORT, DASHBOARD_PORT


def start_all_services():
    print("=" * 65)
    print(" [*] STARTING NOTION TRACKER ENTERPRISE SERVICES")
    print("=" * 65)

    processes = []

    try:
        # 1. Start FastAPI Webhook Ingestion Gateway
        print(f"[*] Starting Webhook Gateway on http://{GATEWAY_HOST}:{GATEWAY_PORT}...")
        p_gw = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "webhook_gateway:app", "--host", GATEWAY_HOST, "--port", str(GATEWAY_PORT)],
        )
        processes.append(("Webhook Gateway", p_gw))

        time.sleep(1.5)

        # 2. Start Background Worker Daemon (1-Minute Rapid Cadence)
        print("[*] Starting Background Polling Daemon (1-Minute Rapid Cadence)...")
        p_daemon = subprocess.Popen(
            [sys.executable, "main.py", "--minutes", "1"],
        )
        processes.append(("Worker Daemon", p_daemon))

        time.sleep(1)

        # 3. Start Streamlit HITL Dashboard
        print(f"[*] Starting Streamlit HITL Dashboard on http://{GATEWAY_HOST}:{DASHBOARD_PORT}...")
        p_ui = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", "dashboard.py", "--server.address", GATEWAY_HOST, "--server.port", str(DASHBOARD_PORT), "--server.headless", "true", "--server.enableCORS", "false", "--server.enableXsrfProtection", "false", "--browser.gatherUsageStats", "false"],
        )
        processes.append(("Streamlit Dashboard", p_ui))

        print("\n" + "=" * 65)
        print(" [OK] ALL NOTION TRACKER SERVICES RUNNING")
        print(f" * Webhook Ingestion URL: http://127.0.0.1:{GATEWAY_PORT}/v1/webhook/ingest")
        print(f" * Streamlit Dashboard:   http://127.0.0.1:{DASHBOARD_PORT}")
        print(f" * Throttle Status:       http://127.0.0.1:{GATEWAY_PORT}/api/v1/throttle-state")

        print(f" * Signature Verifier:    python verify_signatures.py")
        print(" Press Ctrl+C to terminate all services.")
        print("=" * 65 + "\n")

        while True:
            for name, proc in processes:
                ret = proc.poll()
                if ret is not None:
                    print(f"[!] Warning: {name} (PID {proc.pid}) stopped with code {ret}.")
            time.sleep(2)

    except (KeyboardInterrupt, SystemExit):
        print("\n[*] Stopping Notion Tracker services...")
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
    start_all_services()

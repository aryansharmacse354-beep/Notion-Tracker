"""One-Click Launcher for Notion Tracker Enterprise Platform (Vercel Production)."""

import sys
import os
import webbrowser

VERCEL_PROD_URL = os.getenv("VERCEL_PROD_URL", "https://notion-tracker-ai-experts1.vercel.app/")

def launch():
    print("=" * 65)
    print(" [*] LAUNCHING NOTION TRACKER PRODUCTION WEBSITE")
    print("=" * 65)
    print(f"[*] Opening Live Production Portal: {VERCEL_PROD_URL}")
    try:
        webbrowser.open(VERCEL_PROD_URL)
    except Exception as e:
        print(f"[!] Could not open browser automatically: {e}")

    print("\n" + "=" * 65)
    print(" [OK] NOTION TRACKER PRODUCTION WEBSITE LAUNCHED!")
    print(f" * Live Vercel Website: {VERCEL_PROD_URL}")
    print("=" * 65 + "\n")

if __name__ == "__main__":
    launch()

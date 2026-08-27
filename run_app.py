"""Unified Application Launcher for Notion Tracker (Vercel Production)."""

import sys
import os
import webbrowser

VERCEL_PROD_URL = "https://notion-tracker-pearl.vercel.app/"

def run_app():
    print("=" * 65)
    print(" [*] LAUNCHING NOTION TRACKER PRODUCTION WEBSITE (run_app)")
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
    run_app()

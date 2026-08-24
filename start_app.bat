@echo off
title Notion Tracker Enterprise Platform
cls
echo ====================================================================
echo  🚀 NOTION TRACKER ENTERPRISE PLATFORM (Zero-Trust HITL)
echo ====================================================================
echo [*] Initializing services in user session...
echo.

start "Notion Tracker - Streamlit Control Portal" python -m streamlit run dashboard.py --server.address 127.0.0.1 --server.port 8501 --server.headless false --browser.gatherUsageStats false
start "Notion Tracker - FastAPI Gateway" python -m uvicorn webhook_gateway:app --host 127.0.0.1 --port 8000
start "Notion Tracker - Worker Daemon" python main.py

echo [OK] All 3 microservices have been launched in your session!
echo.
echo  • Streamlit Control Portal: http://127.0.0.1:8501
echo  • FastAPI Webhook Gateway:   http://127.0.0.1:8000
echo  • Swagger API Docs:          http://127.0.0.1:8000/docs
echo.
echo Press any key to exit this launcher window (services keep running in background).
pause >nul

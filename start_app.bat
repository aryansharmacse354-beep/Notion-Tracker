@echo off
title Notion Tracker Enterprise Platform
cls
echo ====================================================================
echo  🚀 NOTION TRACKER ENTERPRISE PLATFORM (Zero-Trust HITL)
echo ====================================================================
echo [*] Initializing services...
echo.

start "Notion Tracker - Streamlit Portal" python -m streamlit run dashboard.py --server.port 8501 --server.headless false
start "Notion Tracker - FastAPI Gateway" python -m uvicorn webhook_gateway:app --host 0.0.0.0 --port 8000
start "Notion Tracker - Worker Daemon" python main.py

timeout /t 2 /nobreak >nul
start http://localhost:8501
start http://localhost:8000

echo [OK] All services launched!
echo.
echo  • Streamlit Control Portal:    http://localhost:8501
echo  • Single-Page Web App:         http://localhost:8000
echo  • Swagger API Documentation:   http://localhost:8000/docs
echo.
echo Press any key to close this launcher (services keep running in background).
pause >nul

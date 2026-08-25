@echo off
title Notion Tracker Enterprise Platform Launcher
cls
echo ====================================================================
echo  🚀 NOTION TRACKER ENTERPRISE PLATFORM (Zero-Trust HITL)
echo ====================================================================
echo [*] Cleaning up any previous port locks...

powershell -Command "Get-Process -Id (Get-NetTCPConnection -LocalPort 8000,8501 -ErrorAction SilentlyContinue).OwningProcess -ErrorAction SilentlyContinue | Stop-Process -Force" >nul 2>&1

echo [*] Launching FastAPI Webhook Gateway & Web App (Port 8000)...
start /min "Notion Tracker - Web App & Gateway" python -m uvicorn webhook_gateway:app --host 127.0.0.1 --port 8000

echo [*] Launching Streamlit Control Portal (Port 8501)...
start /min "Notion Tracker - Streamlit Portal" python -m streamlit run dashboard.py --server.port 8501 --server.headless true --browser.gatherUsageStats false

echo [*] Launching Background Automation Daemon...
start /min "Notion Tracker - Automation Daemon" python main.py

echo.
echo [*] Waiting for services to initialize...
timeout /t 3 /nobreak >nul

echo [*] Opening browser to Notion Tracker...
start http://localhost:8000/
start http://localhost:8501/

echo.
echo ====================================================================
echo  ✅ ALL SERVICES SUCCESSFULLY LAUNCHED!
echo ====================================================================
echo.
echo  • Instant Single-Page Web App: http://localhost:8000/
echo  • Streamlit Control Portal:    http://localhost:8501/
echo  • Interactive OpenAPI Docs:    http://localhost:8000/docs
echo.
echo (You can close this window at any time; services will keep running.)
timeout /t 5 >nul
exit

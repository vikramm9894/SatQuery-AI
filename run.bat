@echo off
title SatQuery AI Launcher
echo ============================================================
echo           Starting SatQuery AI Services
echo ============================================================
set PYTHONPATH=%CD%;%CD%\backend

start "SatQuery AI Backend (Port 8000)" cmd /k "python main.py"
start "SatQuery AI Frontend (Port 3000)" cmd /k "python -m http.server 3000 --directory frontend"

echo.
echo Services launched!
echo - Main App (UI + API): http://localhost:8000
echo - Standalone UI      : http://localhost:3000
echo - Backend Health     : http://localhost:8000/api/health
echo - Swagger Docs       : http://localhost:8000/docs
echo ============================================================
timeout /t 3 >nul
start http://localhost:8000

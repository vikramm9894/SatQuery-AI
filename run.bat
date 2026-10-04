@echo off
title SatQuery AI Launcher
echo ============================================================
echo           Starting SatQuery AI Services
echo ============================================================
set PYTHONPATH=.;backend

start "SatQuery AI Frontend (Port 3000)" cmd /k "python -m http.server 3000 --directory frontend"
start "SatQuery AI Backend (Port 8000)" cmd /k "python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

echo.
echo Services launched!
echo - Frontend UI : http://localhost:3000 (or http://localhost:8000)
echo - Backend API : http://localhost:8000/api/health
echo - API Docs    : http://localhost:8000/docs
echo ============================================================
timeout /t 2 >nul
start http://localhost:3000

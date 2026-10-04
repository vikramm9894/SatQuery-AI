# SatQuery AI PowerShell Launcher
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "           Starting SatQuery AI Services" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$projectRoot = $PSScriptRoot
$env:PYTHONPATH = "$projectRoot;$projectRoot\backend"

# Launch Backend + Integrated Frontend on port 8000
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$host.UI.RawUI.WindowTitle = 'SatQuery AI Server (8000)'; cd '$projectRoot'; python main.py"

# Optionally launch standalone Frontend on port 3000
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$host.UI.RawUI.WindowTitle = 'SatQuery Frontend (3000)'; cd '$projectRoot'; python -m http.server 3000 --directory frontend"

Write-Host "Services started!" -ForegroundColor Green
Write-Host "- Main Application (UI + API): http://localhost:8000" -ForegroundColor Yellow
Write-Host "- Standalone UI              : http://localhost:3000" -ForegroundColor Yellow
Write-Host "- Backend API Healthcheck    : http://localhost:8000/api/health" -ForegroundColor Yellow
Write-Host "- Interactive Swagger Docs   : http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan

Start-Sleep -Seconds 3
Start-Process "http://localhost:8000"

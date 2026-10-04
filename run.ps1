# SatQuery AI PowerShell Launcher
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "           Starting SatQuery AI Services" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$env:PYTHONPATH = ".;backend"

# Launch Frontend on port 3000
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$host.UI.RawUI.WindowTitle = 'SatQuery Frontend (3000)'; python -m http.server 3000 --directory frontend"

# Launch Backend on port 8000
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$host.UI.RawUI.WindowTitle = 'SatQuery Backend (8000)'; `$env:PYTHONPATH='.;backend'; python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

Write-Host "Services started!" -ForegroundColor Green
Write-Host "- Frontend UI : http://localhost:3000 (and http://localhost:8000)" -ForegroundColor Yellow
Write-Host "- Backend API : http://localhost:8000/api/health" -ForegroundColor Yellow
Write-Host "- Swagger Docs: http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan

Start-Sleep -Seconds 2
Start-Process "http://localhost:3000"

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "   Starting AdaptIQ - Adaptive Assessment Platform     " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

Write-Host "`n[1/2] Starting Backend API on http://localhost:8000 ..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python -m uvicorn backend.main:app --reload --port 8000"

Write-Host "[2/2] Starting Frontend UI on http://localhost:5173 ..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"

Write-Host "`nBoth services are now running in separate windows!" -ForegroundColor Yellow
Write-Host " - Web App: http://localhost:5173" -ForegroundColor Yellow
Write-Host " - API Docs: http://localhost:8000/docs" -ForegroundColor Yellow

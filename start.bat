@echo off
echo ========================================================
echo   Starting AdaptIQ - Adaptive Assessment Platform
echo ========================================================

echo [1/2] Starting Backend API on http://localhost:8000 ...
start "AdaptIQ Backend" cmd /k "python -m uvicorn backend.main:app --reload --port 8000"

echo [2/2] Starting Frontend UI on http://localhost:5173 ...
start "AdaptIQ Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo Both services are now launching in separate windows!
echo - Web App: http://localhost:5173
echo - API Docs: http://localhost:8000/docs
echo.

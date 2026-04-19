@echo off
title Smart Price Finder - Setup
color 0A
echo.
echo  ============================================================
echo    Smart Price Finder  ^|  Setup ^& Launch
echo  ============================================================
echo.

:: ── Kill any existing stuck processes ────────────────────────
echo [Step 0] Cleaning up old processes...
taskkill /F /IM python.exe /T 2>nul
taskkill /F /IM node.exe /T 2>nul
timeout /t 1 >nul
echo          Done.
echo.

:: ── Verify venv exists ────────────────────────────────────────
if not exist "venv\Scripts\python.exe" (
    echo [ERROR] venv not found at .\venv\
    echo         Create it first:  python -m venv venv
    pause
    exit /b 1
)

:: ── Upgrade pip silently first ────────────────────────────────
echo [Step 1] Upgrading pip...
venv\Scripts\python.exe -m pip install --upgrade pip --quiet
echo          Done.
echo.

:: ── Install Python packages one by one (easier to debug) ─────
echo [Step 2] Installing Python packages...
venv\Scripts\python.exe -m pip install fastapi --quiet
echo          fastapi ... installed
venv\Scripts\python.exe -m pip install "uvicorn[standard]" --quiet
echo          uvicorn ... installed
venv\Scripts\python.exe -m pip install httpx --quiet
echo          httpx ... installed
venv\Scripts\python.exe -m pip install beautifulsoup4 --quiet
echo          beautifulsoup4 ... installed
venv\Scripts\python.exe -m pip install lxml --quiet
echo          lxml ... installed
echo.

:: ── Verify install ────────────────────────────────────────────
echo [Step 3] Verifying install...
venv\Scripts\python.exe check_deps.py
echo.

:: ── Start FastAPI backend in a new window ─────────────────────
echo [Step 4] Starting FastAPI backend on port 8000...
rem Use --reload-dir to ONLY watch price_scraper.py - prevents Vite's file changes from killing the backend
start "Backend - FastAPI (port 8000)" cmd /k "color 0B && echo FastAPI Backend && echo ======================== && venv\Scripts\python.exe -m uvicorn price_scraper:app --reload --reload-dir . --reload-include price_scraper.py --port 8000"
timeout /t 4 >nul
echo          Backend window opened.
echo.

:: ── Install Node deps & start frontend ───────────────────────
echo [Step 5] Installing Node.js packages (frontend)...
cd frontend
call npm install --prefer-offline 2>nul || call npm install
echo.

echo [Step 6] Starting React frontend on port 5173...
start "Frontend - React (port 5173)" cmd /k "color 0D && echo React Frontend && echo ======================== && npm run dev"
timeout /t 3 >nul
echo.

:: ── Open browser ─────────────────────────────────────────────
echo  ============================================================
echo    Backend  :  http://localhost:8000
echo    Frontend :  http://localhost:5173
echo    API Docs :  http://localhost:8000/docs
echo  ============================================================
echo.
start http://localhost:5173
cd ..
echo  Press any key to exit this setup window...
pause >nul

# run.ps1 — Smart Price Finder launcher
# Usage: Right-click this file → "Run with PowerShell"
# OR in PowerShell: .\run.ps1

Write-Host ""
Write-Host "  Smart Price Finder - Launcher" -ForegroundColor Cyan
Write-Host "  ==============================" -ForegroundColor Cyan
Write-Host ""

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

# ── Step 1: Kill anything on port 8000 ───────────────────────
Write-Host "[1/4] Freeing port 8000..." -ForegroundColor Yellow
$pids = netstat -ano | Select-String ":8000 " | ForEach-Object {
    ($_ -split '\s+')[-1]
} | Select-Object -Unique
foreach ($p in $pids) {
    if ($p -match '^\d+$') {
        taskkill /F /PID $p 2>$null | Out-Null
        Write-Host "      Killed PID $p" -ForegroundColor DarkGray
    }
}

# ── Step 2: Install Python packages if needed ─────────────────
Write-Host "[2/4] Installing Python packages..." -ForegroundColor Yellow
& "$root\venv\Scripts\pip.exe" install fastapi "uvicorn[standard]" httpx beautifulsoup4 lxml --quiet
Write-Host "      Done." -ForegroundColor Green

# ── Step 3: Start FastAPI backend ────────────────────────────
Write-Host "[3/4] Starting FastAPI backend (port 8000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "
  Set-Location '$root';
  Write-Host 'FastAPI Backend - port 8000' -ForegroundColor Cyan;
  .\venv\Scripts\python.exe -m uvicorn price_scraper:app --port 8000
" -WindowStyle Normal

Start-Sleep 3

# ── Step 4: Start React frontend ─────────────────────────────
Write-Host "[4/4] Starting React frontend (port 5173)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "
  Set-Location '$root\frontend';
  Write-Host 'React Frontend - port 5173' -ForegroundColor Magenta;
  npm run dev
" -WindowStyle Normal

Start-Sleep 4

Write-Host ""
Write-Host "  ==============================" -ForegroundColor Cyan
Write-Host "  Backend:   http://localhost:8000" -ForegroundColor White
Write-Host "  Frontend:  http://localhost:5173  <-- Open this!" -ForegroundColor Green
Write-Host "  API Docs:  http://localhost:8000/docs" -ForegroundColor White
Write-Host "  ==============================" -ForegroundColor Cyan
Write-Host ""

# Open the browser
Start-Process "http://localhost:5173"
Write-Host "  Browser opened. Press Enter to close this window." -ForegroundColor DarkGray
Read-Host

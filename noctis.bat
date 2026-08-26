@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8

set PID_FILE=noctis_run.pid

:: ── Double-launch guard with stale PID cleanup ───────────────────
if exist "%PID_FILE%" (
    set STALE=1
    for /f "usebackq" %%p in ("%PID_FILE%") do (
        tasklist /FI "PID eq %%p" 2>nul | find "%%p" >nul
        if !ERRORLEVEL!==0 set STALE=0
    )
    if !STALE!==1 (
        echo [Noctis] Stale PID file found, no matching process. Cleaning up.
        del "%PID_FILE%"
    ) else (
        echo [Noctis] ERROR: Instance already running. Run stop_noctis.bat first.
        exit /b 1
    )
)

echo.
echo   ======================================
echo    N-0CT15  ::  Shadow Monarch v9.0
echo    DevilCore System Boot Sequence
echo   ======================================
echo.

:: ── Step 1 & 2: Start API server and Voice Loop in background ─────
echo [Boot] Starting core services (API server ^& Voice loop)...
venv\Scripts\python.exe -c "import os, sys, subprocess; py = sys.executable; p1 = subprocess.Popen([py, '-m', 'uvicorn', 'api.server:app', '--host', '127.0.0.1', '--port', '8000']); p2 = subprocess.Popen([py, 'noctis_voice.py']); open('noctis_run.pid', 'w').write(f'{p1.pid}\n{p2.pid}\n')"

:: ── Step 3: Launch UI immediately (Edge Chromium App Mode) ───────
echo [Boot] Launching Command UI...
echo.
set EDGE_PROFILE=%TEMP%\noctis_edge_profile
if exist "%EDGE_PROFILE%" rmdir /s /q "%EDGE_PROFILE%" >nul 2>&1
start "" "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --user-data-dir="%EDGE_PROFILE%" --app=http://127.0.0.1:8000/ --no-first-run --no-default-browser-check

:: ── Step 4: Wait for API server to become ready ──────────────────
echo [Boot] Connecting UI to core...
set READY=0
for /L %%i in (1,1,20) do (
    if !READY!==0 (
        venv\Scripts\python.exe -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=1)" >nul 2>&1
        if !ERRORLEVEL!==0 (
            set READY=1
            echo [Boot] Noctis Core Online.
        ) else (
            ping 127.0.0.1 -n 2 >nul
        )
    )
)

:: ── Step 5: Keep alive & monitor until UI/server closes ──────────
ping 127.0.0.1 -n 3 >nul
:MONITOR_LOOP
venv\Scripts\python.exe -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)" >nul 2>&1
if !ERRORLEVEL!==0 (
    ping 127.0.0.1 -n 3 >nul
    goto MONITOR_LOOP
)

echo.
echo [Shutdown] UI closed or server stopped. Cleaning up...
call stop_noctis.bat

exit /b 0

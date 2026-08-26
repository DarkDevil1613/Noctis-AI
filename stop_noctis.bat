@echo off
setlocal
cd /d "%~dp0"

echo [Noctis] Initiating full system shutdown...

set PID_FILE=noctis_run.pid

:: STEP 1: Kill tracked PIDs explicitly (with child tree)
if exist "%PID_FILE%" (
    echo [Noctis] Terminating tracked processes...
    for /f "usebackq tokens=*" %%a in ("%PID_FILE%") do (
        taskkill /PID %%a /T /F >nul 2>&1
    )
    del "%PID_FILE%"
) else (
    echo [Noctis] No PID file found, engaging fail-safe sweep...
)

:: STEP 2: The Fail-Safe Sweep
:: Kills any python.exe whose command line matches Noctis scripts
echo [Noctis] Sweeping for orphaned background instances...
powershell -NoProfile -Command "$procs = Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'python.exe' -and $_.CommandLine -and ($_.CommandLine -match 'noctis_voice\.py' -or $_.CommandLine -match 'noctis_ui\.py' -or $_.CommandLine -match 'ws_bridge\.py' -or $_.CommandLine -match 'api\.server:app') }; if ($procs) { foreach ($p in $procs) { try { Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue } catch {} } }"

echo [Noctis] System Offline. All processes terminated.
ping 127.0.0.1 -n 2 >nul
exit /b 0

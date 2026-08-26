@echo off
setlocal
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8

set PID_FILE=noctis_run.pid

if exist "%PID_FILE%" (
    echo [Noctis] ERROR: Instance already running. Please run stop_noctis.bat first.
    exit /b 1
)

echo [Noctis] Starting API server (uvicorn)...
powershell -Command "try { $p = Start-Process 'venv\Scripts\python.exe' -ArgumentList '-m uvicorn api.server:app --host 0.0.0.0 --port 8000' -WindowStyle Hidden -PassThru -ErrorAction Stop; $p.Id | Out-File -FilePath '%PID_FILE%' -Encoding ascii } catch { exit 1 }"

echo [Noctis] Starting Voice Loop (noctis_voice.py)...
powershell -Command "try { $p = Start-Process 'venv\Scripts\python.exe' -ArgumentList 'noctis_voice.py' -WindowStyle Hidden -PassThru -ErrorAction Stop; $p.Id | Out-File -FilePath '%PID_FILE%' -Encoding ascii -Append } catch { exit 1 }"

echo [Noctis] System Online. Processes tracked in %PID_FILE%.
exit /b 0

@echo off
setlocal EnableDelayedExpansion

title CFAP Launcher

REM ============================================================================
REM 1. RESOLVE PROJECT ROOT & SET PROCESS ENVIRONMENT
REM ============================================================================
set "PROJECT_ROOT=%~dp0"
if "%PROJECT_ROOT:~-1%"=="\" set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"
cd /d "%PROJECT_ROOT%"

REM Enforce consistent Redis and Celery endpoints (overriding any stale .env values)
set "REDIS_URL=redis://127.0.0.1:6380/0"
set "CELERY_BROKER_URL=redis://127.0.0.1:6380/0"
set "CELERY_RESULT_BACKEND=redis://127.0.0.1:6380/0"

echo ============================================================
echo                    CFAP STARTUP LAUNCHER
echo        Cognitive Feedback Analytics Platform
echo ============================================================
echo [*] Project Root: "%PROJECT_ROOT%"
echo [*] Redis Endpoint: 127.0.0.1:6380
echo.

REM ============================================================================
REM 2. PREREQUISITE AND FILE VALIDATION
REM ============================================================================
echo [*] Validating project directories and entry points...

if not exist "%PROJECT_ROOT%\backend\app\main.py" (
    echo [ERROR] Backend entry point missing:
    echo         "%PROJECT_ROOT%\backend\app\main.py"
    goto :fatal_error
)

if not exist "%PROJECT_ROOT%\backend\app\core\celery_app.py" (
    echo [ERROR] Celery application missing:
    echo         "%PROJECT_ROOT%\backend\app\core\celery_app.py"
    goto :fatal_error
)

if not exist "%PROJECT_ROOT%\frontend\package.json" (
    echo [ERROR] Frontend package manifest missing:
    echo         "%PROJECT_ROOT%\frontend\package.json"
    goto :fatal_error
)

if not exist "%PROJECT_ROOT%\frontend" (
    echo [ERROR] Frontend directory missing:
    echo         "%PROJECT_ROOT%\frontend"
    goto :fatal_error
)

REM Check for required CLI tools
where curl.exe >nul 2>&1
if errorlevel 1 (
    echo [ERROR] 'curl.exe' is not found in PATH.
    echo         Windows built-in curl is required for health probes.
    goto :fatal_error
)

where npm >nul 2>&1
if errorlevel 1 (
    echo [ERROR] 'npm' is not found in PATH.
    echo         Node.js and npm are required to run the frontend application.
    goto :fatal_error
)

where wsl >nul 2>&1
if errorlevel 1 (
    echo [ERROR] 'wsl' command is not found in PATH.
    echo         WSL 2 is required to run Redis.
    goto :fatal_error
)

REM Locate and validate Python runtime (.venv first, then system PATH)
set "PYTHON_EXE="
if exist "%PROJECT_ROOT%\.venv\Scripts\python.exe" (
    "%PROJECT_ROOT%\.venv\Scripts\python.exe" -c "import uvicorn, celery, redis" >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON_EXE=%PROJECT_ROOT%\.venv\Scripts\python.exe"
    )
)

if not defined PYTHON_EXE (
    where python >nul 2>&1
    if not errorlevel 1 (
        python -c "import uvicorn, celery, redis" >nul 2>&1
        if not errorlevel 1 (
            set "PYTHON_EXE=python"
        )
    )
)

if not defined PYTHON_EXE (
    echo [ERROR] Could not find a Python environment with required packages:
    echo         uvicorn, celery, redis
    echo         Checked: "%PROJECT_ROOT%\.venv\Scripts\python.exe" and system PATH 'python'.
    echo         Please ensure the virtual environment is set up.
    goto :fatal_error
)

echo [OK] Verified project files, Python runtime, npm, curl, and WSL.
echo [INFO] Python executable: "!PYTHON_EXE!"
echo.

REM Initialize service status variables
set "POSTGRES_STATUS=NOT CHECKED"
set "REDIS_WSL_STATUS=NOT CHECKED"
set "REDIS_WIN_STATUS=NOT CHECKED"
set "BACKEND_STATUS=NOT CHECKED"
set "CELERY_STATUS=NOT CHECKED"
set "FRONTEND_STATUS=NOT CHECKED"
set "FRONTEND_CONFIRMED=0"
set "REDIS_WIN_OK=0"

REM ============================================================================
REM 3. POSTGRESQL SERVICE (postgresql-x64-17) & DATABASE CONNECTIVITY
REM ============================================================================
echo [*] Checking PostgreSQL Windows service [postgresql-x64-17]...
sc query postgresql-x64-17 2>nul | findstr /i "STATE" | findstr /i "RUNNING" >nul 2>&1
if not errorlevel 1 (
    set "POSTGRES_STATUS=RUNNING"
    echo [OK] PostgreSQL service [postgresql-x64-17] is running.
) else (
    echo [*] PostgreSQL service is stopped. Attempting to start...
    net start postgresql-x64-17 >nul 2>&1
    ping -n 3 127.0.0.1 >nul
    sc query postgresql-x64-17 2>nul | findstr /i "STATE" | findstr /i "RUNNING" >nul 2>&1
    if not errorlevel 1 (
        set "POSTGRES_STATUS=STARTED"
        echo [OK] PostgreSQL service started successfully.
    ) else (
        set "POSTGRES_STATUS=FAILED"
        echo [ERROR] PostgreSQL service 'postgresql-x64-17' could not be started.
        echo         Note: Starting Windows services typically requires Administrator privileges.
        echo         Corrective action: Open an elevated Command Prompt and run:
        echo           net start postgresql-x64-17
    )
)

REM Verify database query execution from Python
if not "!POSTGRES_STATUS!"=="FAILED" (
    "!PYTHON_EXE!" -c "import sys; from backend.app.db.database import engine; from sqlalchemy import text; sys.exit(0 if engine.connect().execute(text('SELECT 1')).scalar() == 1 else 1)" >nul 2>&1
    if not errorlevel 1 (
        set "POSTGRES_STATUS=READY (Database Connected)"
        echo [OK] CFAP database connection verified successfully.
    ) else (
        set "POSTGRES_STATUS=FAILED (Database Query Failed)"
        echo [ERROR] PostgreSQL service is running but CFAP database query failed.
    )
)
echo.

REM ============================================================================
REM 4. REDIS IN WSL 2 & WINDOWS-SIDE CONNECTIVITY TEST (Port 6380)
REM ============================================================================
echo [*] Checking Redis connectivity on 127.0.0.1:6380...

REM Check if Redis is already accepting connections from Windows
"!PYTHON_EXE!" -c "import sys, redis; sys.exit(0 if redis.Redis(host='127.0.0.1', port=6380, socket_connect_timeout=2).ping() else 1)" >nul 2>&1
if not errorlevel 1 (
    set "REDIS_WIN_OK=1"
    set "REDIS_WSL_STATUS=ALREADY RUNNING"
    set "REDIS_WIN_STATUS=READY (Connected)"
    echo [OK] Redis is already active and responsive on 127.0.0.1:6380.
) else (
    echo [*] Redis on 127.0.0.1:6380 is not active. Initializing WSL Redis session...
    REM Ensure persistent system service is started and WSL distribution stays active
    start "CFAP - Redis (WSL)" /min cmd.exe /c "wsl -d Ubuntu -u root -- bash -c 'service redis-server start; exec sleep infinity'"
    echo [*] Waiting for Redis on 127.0.0.1:6380 [timeout: 15 seconds]...
    for /l %%k in (1,1,15) do (
        if "!REDIS_WIN_OK!"=="0" (
            ping -n 2 127.0.0.1 >nul
            "!PYTHON_EXE!" -c "import sys, redis; sys.exit(0 if redis.Redis(host='127.0.0.1', port=6380, socket_connect_timeout=2).ping() else 1)" >nul 2>&1
            if not errorlevel 1 (
                set "REDIS_WIN_OK=1"
                set "REDIS_WSL_STATUS=READY (Started)"
                set "REDIS_WIN_STATUS=READY (Connected)"
                echo [OK] Windows Python verified connectivity to Redis at 127.0.0.1:6380.
            )
        )
    )
    if "!REDIS_WIN_OK!"=="0" (
        set "REDIS_WSL_STATUS=FAILED"
        set "REDIS_WIN_STATUS=FAILED (Unreachable on 127.0.0.1:6380)"
        echo [ERROR] Redis on 127.0.0.1:6380 failed to respond within 15 seconds.
        echo         Corrective action: Check WSL Ubuntu status with:
        echo           wsl -d Ubuntu -u root -- service redis-server status
        echo         Celery worker startup will be skipped.
    )
)
echo.

REM ============================================================================
REM 5. FASTAPI BACKEND (Uvicorn on 127.0.0.1:8000)
REM ============================================================================
echo [*] Checking CFAP Backend status [http://127.0.0.1:8000/health]...
curl.exe -s --connect-timeout 2 http://127.0.0.1:8000/health 2>nul | findstr /i "CFAP Backend" >nul 2>&1
if not errorlevel 1 (
    set "BACKEND_STATUS=ALREADY RUNNING"
    echo [INFO] CFAP Backend is already running and healthy at http://127.0.0.1:8000.
) else (
    REM Check if port 8000 is occupied by an unrelated process
    netstat -ano -p tcp 2>nul | findstr /i /c:"LISTENING" | findstr ":8000\>" >nul 2>&1
    if not errorlevel 1 (
        set "BACKEND_STATUS=CONFLICT (Port 8000 in use by another process)"
        echo [WARNING] Port 8000 is in use by another process that is not CFAP Backend.
        echo           FastAPI startup skipped to avoid conflict or terminating unrelated tasks.
    ) else (
        echo [*] Launching FastAPI Backend in a dedicated window...
        start "CFAP - Backend (FastAPI)" cmd.exe /k ""!PYTHON_EXE!" -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000"
        echo [*] Waiting for Backend health endpoint [timeout: 45 seconds]...
        set "BACKEND_STATUS=FAILED (Health check timed out)"
        for /l %%i in (1,1,45) do (
            if "!BACKEND_STATUS!"=="FAILED (Health check timed out)" (
                ping -n 2 127.0.0.1 >nul
                curl.exe -s --connect-timeout 1 http://127.0.0.1:8000/health 2>nul | findstr /i "CFAP Backend" >nul 2>&1
                if not errorlevel 1 (
                    set "BACKEND_STATUS=READY (Started)"
                    echo [OK] CFAP Backend is healthy at http://127.0.0.1:8000/health.
                )
            )
        )
        if "!BACKEND_STATUS!"=="FAILED (Health check timed out)" (
            echo [ERROR] CFAP Backend failed to report healthy within 45 seconds.
            echo         Check the "CFAP - Backend (FastAPI)" terminal window for traceback details.
        )
    )
)
echo.

REM ============================================================================
REM 6. CELERY WORKER
REM ============================================================================
echo [*] Checking CFAP Celery Worker status...
if "!REDIS_WIN_OK!"=="1" (
    set "CELERY_PID="
    del "%TEMP%\cfap_celery_pid.txt" >nul 2>&1
    powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object Name -match 'python' | Where-Object CommandLine -match 'backend\.app\.core\.celery_app' | Select-Object -ExpandProperty ProcessId" > "%TEMP%\cfap_celery_pid.txt" 2>nul
    if exist "%TEMP%\cfap_celery_pid.txt" (
        set /p CELERY_PID=<"%TEMP%\cfap_celery_pid.txt"
        del "%TEMP%\cfap_celery_pid.txt" >nul 2>&1
    )
    if defined CELERY_PID (
        set "CELERY_STATUS=ALREADY RUNNING (PID !CELERY_PID!)"
        echo [INFO] CFAP Celery worker is already running [PID !CELERY_PID!]. Skipping startup.
    ) else (
        echo [*] Launching CFAP Celery Worker in a dedicated window...
        start "CFAP - Celery Worker" cmd.exe /k ""!PYTHON_EXE!" -m celery -A backend.app.core.celery_app.celery_app worker --loglevel=info --pool=solo"
        echo [*] Verifying Celery worker process...
        ping -n 4 127.0.0.1 >nul
        set "CELERY_PID="
        del "%TEMP%\cfap_celery_pid.txt" >nul 2>&1
        powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object Name -match 'python' | Where-Object CommandLine -match 'backend\.app\.core\.celery_app' | Select-Object -ExpandProperty ProcessId" > "%TEMP%\cfap_celery_pid.txt" 2>nul
        if exist "%TEMP%\cfap_celery_pid.txt" (
            set /p CELERY_PID=<"%TEMP%\cfap_celery_pid.txt"
            del "%TEMP%\cfap_celery_pid.txt" >nul 2>&1
        )
        if defined CELERY_PID (
            set "CELERY_STATUS=READY (PID !CELERY_PID!)"
            echo [OK] CFAP Celery worker process confirmed active [PID !CELERY_PID!].
        ) else (
            set "CELERY_STATUS=LAUNCHED (Dedicated Window)"
            echo [INFO] CFAP Celery worker launched in dedicated window.
            echo        Check the "CFAP - Celery Worker" terminal window for runtime status.
        )
    )
) else (
    set "CELERY_STATUS=SKIPPED (Redis Unreachable)"
    echo [WARNING] Celery worker skipped because Redis is unreachable on 127.0.0.1:6380.
)
echo.

REM ============================================================================
REM 7. FRONTEND (Next.js dev server on http://localhost:3000)
REM ============================================================================
echo [*] Checking CFAP Frontend status [http://localhost:3000]...
curl.exe -s -I --connect-timeout 2 http://localhost:3000 2>nul | findstr /i "HTTP/" >nul 2>&1
if not errorlevel 1 (
    set "FRONTEND_STATUS=ALREADY RUNNING"
    set "FRONTEND_CONFIRMED=1"
    echo [INFO] CFAP Frontend is already running and responsive at http://localhost:3000.
) else (
    REM Check if port 3000 is occupied by an unrelated process
    netstat -ano -p tcp 2>nul | findstr /i /c:"LISTENING" | findstr ":3000\>" >nul 2>&1
    if not errorlevel 1 (
        set "FRONTEND_STATUS=CONFLICT (Port 3000 in use by another process)"
        echo [WARNING] Port 3000 is occupied by another process that is not CFAP Frontend.
        echo           Frontend startup skipped to avoid conflicts.
    ) else (
        if not exist "%PROJECT_ROOT%\frontend\node_modules" (
            echo [*] Frontend dependencies missing. Installing using npm ci...
            cd /d "%PROJECT_ROOT%\frontend"
            call npm ci
            cd /d "%PROJECT_ROOT%"
        )
        echo [*] Launching CFAP Frontend in a dedicated window...
        start "CFAP - Frontend (Next.js)" /D "%PROJECT_ROOT%\frontend" cmd.exe /k "npm run dev"
        echo [*] Waiting for Frontend to respond at http://localhost:3000 [timeout: 45 seconds]...
        set "FRONTEND_STATUS=FAILED (Startup timed out)"
        for /l %%i in (1,1,45) do (
            if "!FRONTEND_CONFIRMED!"=="0" (
                ping -n 2 127.0.0.1 >nul
                curl.exe -s -I --connect-timeout 1 http://localhost:3000 2>nul | findstr /i "HTTP/" >nul 2>&1
                if not errorlevel 1 (
                    set "FRONTEND_STATUS=READY (Started)"
                    set "FRONTEND_CONFIRMED=1"
                    echo [OK] CFAP Frontend is responsive at http://localhost:3000.
                )
            )
        )
        if "!FRONTEND_CONFIRMED!"=="0" (
            echo [ERROR] CFAP Frontend did not respond within 45 seconds.
            echo         Check the "CFAP - Frontend (Next.js)" terminal window for logs.
        )
    )
)
echo.

REM ============================================================================
REM 8. BROWSER LAUNCH
REM ============================================================================
if "!FRONTEND_CONFIRMED!"=="1" (
    echo [*] Opening application in default browser: http://localhost:3000
    start "" "http://localhost:3000"
) else (
    echo [NOTICE] Browser launch skipped because Frontend is not confirmed responsive.
)
echo.

REM ============================================================================
REM 9. FINAL STARTUP SUMMARY
REM ============================================================================
echo ============================================================
echo               CFAP STARTUP LAUNCHER SUMMARY
echo ============================================================
echo   PostgreSQL:                      !POSTGRES_STATUS!
echo   Redis (WSL Ubuntu on 6380):      !REDIS_WIN_STATUS!
echo   Backend (FastAPI :8000):         !BACKEND_STATUS!
echo   Celery Worker:                   !CELERY_STATUS!
echo   Frontend (Next.js :3000):        !FRONTEND_STATUS!
echo ============================================================
echo.

REM Overall readiness evaluation
set "OVERALL_SUCCESS=1"
if not "!POSTGRES_STATUS!"=="READY (Database Connected)" set "OVERALL_SUCCESS=0"
if "!REDIS_WIN_OK!"=="0" set "OVERALL_SUCCESS=0"
if "!BACKEND_STATUS!"=="FAILED (Health check timed out)" set "OVERALL_SUCCESS=0"
if "!BACKEND_STATUS!"=="CONFLICT (Port 8000 in use by another process)" set "OVERALL_SUCCESS=0"
if "!FRONTEND_STATUS!"=="FAILED (Startup timed out)" set "OVERALL_SUCCESS=0"
if "!FRONTEND_STATUS!"=="CONFLICT (Port 3000 in use by another process)" set "OVERALL_SUCCESS=0"

if "!OVERALL_SUCCESS!"=="1" (
    echo [SUCCESS] CFAP services are operational.
    echo           Access the web dashboard at: http://localhost:3000
    echo           Backend API Health:          http://127.0.0.1:8000/health
    echo           Database Health:             http://127.0.0.1:8000/health/db
    echo           API Documentation:           http://127.0.0.1:8000/docs
) else (
    echo [WARNING] CFAP startup finished with errors, conflicts, or skipped components.
    echo           The application is NOT fully operational.
    echo           Review the summary and check individual terminal windows for details.
)
echo.
echo ============================================================
echo               HOW TO SAFELY STOP CFAP SERVICES
echo ============================================================
echo   Quick stop: Run stop.bat from the project directory.
echo   Manual stop:
echo     1. Frontend:      Close or press Ctrl+C in "CFAP - Frontend (Next.js)"
echo     2. Celery Worker: Close or press Ctrl+C in "CFAP - Celery Worker"
echo     3. Backend:       Close or press Ctrl+C in "CFAP - Backend (FastAPI)"
echo     4. Redis Keepalive: Close "CFAP - Redis (WSL)"
echo ============================================================
echo.
pause
exit /b 0

:fatal_error
echo.
echo ============================================================
echo [FATAL ERROR] Startup aborted due to missing prerequisites.
echo ============================================================
echo.
pause
exit /b 1

@echo off
setlocal EnableDelayedExpansion

title CFAP Launcher

REM ============================================================================
REM 1. RESOLVE PROJECT ROOT
REM ============================================================================
set "PROJECT_ROOT=%~dp0"
if "%PROJECT_ROOT:~-1%"=="\" set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"
cd /d "%PROJECT_ROOT%"

echo ============================================================
echo                    CFAP STARTUP LAUNCHER
echo        Cognitive Feedback Analytics Platform
echo ============================================================
echo [*] Project Root: "%PROJECT_ROOT%"
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

REM ============================================================================
REM 3. POSTGRESQL SERVICE (postgresql-x64-17)
REM ============================================================================
echo [*] Checking PostgreSQL Windows service [postgresql-x64-17]...
sc query postgresql-x64-17 2>nul | findstr /i "STATE" | findstr /i "RUNNING" >nul 2>&1
if not errorlevel 1 (
    set "POSTGRES_STATUS=ALREADY RUNNING"
    echo [OK] PostgreSQL service [postgresql-x64-17] is already running.
) else (
    echo [*] PostgreSQL service is stopped. Attempting to start...
    net start postgresql-x64-17 >nul 2>&1
    ping -n 3 127.0.0.1 >nul
    sc query postgresql-x64-17 2>nul | findstr /i "STATE" | findstr /i "RUNNING" >nul 2>&1
    if not errorlevel 1 (
        set "POSTGRES_STATUS=READY (Started)"
        echo [OK] PostgreSQL service started successfully.
    ) else (
        set "POSTGRES_STATUS=FAILED"
        echo [ERROR] PostgreSQL service 'postgresql-x64-17' could not be started.
        echo         Note: Starting Windows services typically requires Administrator privileges.
        echo         Corrective action: Open an elevated Command Prompt and run:
        echo           net start postgresql-x64-17
    )
)
echo.

REM ============================================================================
REM 4. REDIS IN WSL 2 (Ubuntu)
REM ============================================================================
echo [*] Checking Redis inside Ubuntu WSL...
set "WSL_PONG=0"
wsl -d Ubuntu -- redis-cli ping > "%TEMP%\cfap_redis_ping.txt" 2>nul
if exist "%TEMP%\cfap_redis_ping.txt" (
    set /p REDIS_OUT=<"%TEMP%\cfap_redis_ping.txt"
    del "%TEMP%\cfap_redis_ping.txt" >nul 2>&1
    if /i "!REDIS_OUT!"=="PONG" set "WSL_PONG=1"
)

if "!WSL_PONG!"=="1" (
    set "REDIS_WSL_STATUS=ALREADY RUNNING"
    echo [OK] Redis responded with PONG inside Ubuntu WSL.
) else (
    echo [*] Redis is not responding in Ubuntu WSL. Attempting safe start...
    wsl -d Ubuntu -u root -- service redis-server start >nul 2>&1
    ping -n 3 127.0.0.1 >nul
    wsl -d Ubuntu -- redis-cli ping > "%TEMP%\cfap_redis_ping.txt" 2>nul
    if exist "%TEMP%\cfap_redis_ping.txt" (
        set /p REDIS_OUT=<"%TEMP%\cfap_redis_ping.txt"
        del "%TEMP%\cfap_redis_ping.txt" >nul 2>&1
        if /i "!REDIS_OUT!"=="PONG" set "WSL_PONG=1"
    )
    if "!WSL_PONG!"=="1" (
        set "REDIS_WSL_STATUS=READY (Started)"
        echo [OK] Redis started and responded with PONG inside Ubuntu WSL.
    ) else (
        set "REDIS_WSL_STATUS=FAILED"
        echo [ERROR] Redis failed to respond with PONG inside Ubuntu WSL.
        echo         Manual corrective action:
        echo           wsl -d Ubuntu -u root -- service redis-server start
    )
)
echo.

REM ============================================================================
REM 5. WINDOWS-SIDE REDIS CONNECTIVITY TEST
REM ============================================================================
echo [*] Testing Windows Python connectivity to Redis [127.0.0.1:6379]...
if "!WSL_PONG!"=="1" (
    set "WIN_REDIS_OK=0"
    for /l %%k in (1,1,5) do (
        if "!WIN_REDIS_OK!"=="0" (
            "!PYTHON_EXE!" -c "import sys, redis; sys.exit(0 if redis.Redis(host='127.0.0.1', port=6379, socket_connect_timeout=3).ping() else 1)" >nul 2>&1
            if not errorlevel 1 (
                set "WIN_REDIS_OK=1"
            ) else (
                ping -n 2 127.0.0.1 >nul
            )
        )
    )
    if "!WIN_REDIS_OK!"=="1" (
        set "REDIS_WIN_STATUS=READY (Connected)"
        echo [OK] Windows Python verified connectivity to Redis at 127.0.0.1:6379.
    ) else (
        set "REDIS_WIN_STATUS=FAILED (Unreachable from Windows)"
        echo [ERROR] Windows Python cannot connect to Redis at 127.0.0.1:6379.
        echo         WSL 2 mirrored networking did not bridge the Redis port to Windows localhost.
        echo.
        echo         Corrective troubleshooting actions:
        echo         1. Ensure %%USERPROFILE%%\.wslconfig has:
        echo            [wsl2]
        echo            networkingMode=mirrored
        echo            hostAddressLoopback=true
        echo         2. Restart WSL by running in terminal:
        echo            wsl --shutdown
        echo            wsl -d Ubuntu -u root -- service redis-server start
        echo         3. Verify Windows Firewall does not block loopback TCP 6379.
        echo.
        echo         Celery worker startup will be skipped to prevent unhandled connection retries.
    )
) else (
    set "REDIS_WIN_STATUS=SKIPPED (WSL Redis unavailable)"
    echo [WARNING] Skipped Windows Redis test because WSL Redis is not responding.
)
echo.

REM ============================================================================
REM 6. FASTAPI BACKEND (Uvicorn on 127.0.0.1:8000)
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
        start "CFAP - Backend (FastAPI)" cmd.exe /k "cd /d \"%PROJECT_ROOT%\" && \"%PYTHON_EXE%\" -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000"
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
REM 7. CELERY WORKER
REM ============================================================================
echo [*] Checking CFAP Celery Worker status...
if "!REDIS_WIN_STATUS!"=="READY (Connected)" (
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
        start "CFAP - Celery Worker" cmd.exe /k "cd /d \"%PROJECT_ROOT%\" && \"%PYTHON_EXE%\" -m celery -A backend.app.core.celery_app.celery_app worker --loglevel=info --pool=solo"
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
    set "CELERY_STATUS=SKIPPED (Redis Unreachable from Windows)"
    echo [WARNING] Celery worker skipped because Windows cannot connect to Redis.
)
echo.

REM ============================================================================
REM 8. FRONTEND (Next.js dev server on http://localhost:3000)
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
        echo [*] Launching CFAP Frontend in a dedicated window...
        start "CFAP - Frontend (Next.js)" cmd.exe /k "cd /d \"%PROJECT_ROOT%\frontend\" && npm run dev"
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
REM 9. BROWSER LAUNCH
REM ============================================================================
if "!FRONTEND_CONFIRMED!"=="1" (
    echo [*] Opening application in default browser: http://localhost:3000
    start "" "http://localhost:3000"
) else (
    echo [NOTICE] Browser launch skipped because Frontend is not confirmed responsive.
)
echo.

REM ============================================================================
REM 10. FINAL STARTUP SUMMARY
REM ============================================================================
echo ============================================================
echo               CFAP STARTUP LAUNCHER SUMMARY
echo ============================================================
echo   PostgreSQL (postgresql-x64-17):  !POSTGRES_STATUS!
echo   Redis (WSL Ubuntu):              !REDIS_WSL_STATUS!
echo   Redis (Windows Connectivity):    !REDIS_WIN_STATUS!
echo   Backend (FastAPI :8000):         !BACKEND_STATUS!
echo   Celery Worker:                   !CELERY_STATUS!
echo   Frontend (Next.js :3000):        !FRONTEND_STATUS!
echo ============================================================
echo.

REM Overall readiness evaluation
set "OVERALL_SUCCESS=1"
if "!POSTGRES_STATUS!"=="FAILED" set "OVERALL_SUCCESS=0"
if "!REDIS_WSL_STATUS!"=="FAILED" set "OVERALL_SUCCESS=0"
if "!REDIS_WIN_STATUS!"=="FAILED (Unreachable from Windows)" set "OVERALL_SUCCESS=0"
if "!REDIS_WIN_STATUS!"=="SKIPPED (WSL Redis unavailable)" set "OVERALL_SUCCESS=0"
if "!BACKEND_STATUS!"=="FAILED (Health check timed out)" set "OVERALL_SUCCESS=0"
if "!BACKEND_STATUS!"=="CONFLICT (Port 8000 in use by another process)" set "OVERALL_SUCCESS=0"
if "!FRONTEND_STATUS!"=="FAILED (Startup timed out)" set "OVERALL_SUCCESS=0"
if "!FRONTEND_STATUS!"=="CONFLICT (Port 3000 in use by another process)" set "OVERALL_SUCCESS=0"

if "!OVERALL_SUCCESS!"=="1" (
    echo [SUCCESS] CFAP services are operational.
    echo           Access the web dashboard at: http://localhost:3000
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
echo   1. Frontend:      Close or press Ctrl+C in "CFAP - Frontend (Next.js)"
echo   2. Celery Worker: Close or press Ctrl+C in "CFAP - Celery Worker"
echo   3. Backend:       Close or press Ctrl+C in "CFAP - Backend (FastAPI)"
echo   4. PostgreSQL:    Elevated CMD: net stop postgresql-x64-17
echo   5. Redis (WSL):   Terminal: wsl -d Ubuntu -u root -- service redis-server stop
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

@echo off
setlocal EnableDelayedExpansion

title CFAP Shutdown

REM ============================================================================
REM RESOLVE PROJECT ROOT
REM ============================================================================
set "PROJECT_ROOT=%~dp0"
if "%PROJECT_ROOT:~-1%"=="\" set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"
cd /d "%PROJECT_ROOT%"

echo ============================================================
echo                    CFAP SHUTDOWN UTILITY
echo        Cognitive Feedback Analytics Platform
echo ============================================================
echo [*] Stopping CFAP-managed processes...
echo.

REM 1. Close named CFAP console windows
taskkill /fi "WINDOWTITLE eq CFAP - Frontend (Next.js)*" /t /f >nul 2>&1
taskkill /fi "WINDOWTITLE eq CFAP - Backend (FastAPI)*" /t /f >nul 2>&1
taskkill /fi "WINDOWTITLE eq CFAP - Celery Worker*" /t /f >nul 2>&1
taskkill /fi "WINDOWTITLE eq CFAP - Redis (WSL)*" /t /f >nul 2>&1

REM 2. Fallback: Terminate only verified CFAP processes whose path or command line identifies this project root
powershell -NoProfile -Command "$root = '%PROJECT_ROOT%'; Get-CimInstance Win32_Process | Where-Object { $c = $_.CommandLine; $e = $_.ExecutablePath; if (!$c -and !$e) { return $false }; $inRoot = ($c -and $c.IndexOf($root, [System.StringComparison]::OrdinalIgnoreCase) -ge 0) -or ($e -and $e.IndexOf($root, [System.StringComparison]::OrdinalIgnoreCase) -ge 0); if (!$inRoot) { return $false }; if ($_.Name -match 'python' -and ($c -match 'backend\.app\.main' -or $c -match 'backend\.app\.core\.celery_app')) { return $true }; if ($_.Name -match 'node' -and $c -match 'next') { return $true }; return $false } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }" >nul 2>&1

echo [OK] CFAP application processes (Frontend, Backend, Celery, and keepalive) stopped.
echo [NOTE] Persistent services (PostgreSQL and Ubuntu Redis) were left running normally.
echo.
echo ============================================================
echo           CFAP SHUTDOWN COMPLETE
echo ============================================================
echo.
pause
exit /b 0

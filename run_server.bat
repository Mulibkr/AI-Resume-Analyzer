@echo off
title AURA Resume Analyzer Server
echo =======================================================
echo Starting AURA Resume Analyzer Local Server...
echo =======================================================
echo.

REM Try starting on port 8000
.venv\Scripts\python manage.py runserver 127.0.0.1:8000

REM If port 8000 fails (occupied), try port 8080
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [INFO] Port 8000 is unavailable. Trying port 8080...
    echo.
    .venv\Scripts\python manage.py runserver 127.0.0.1:8080
)

pause

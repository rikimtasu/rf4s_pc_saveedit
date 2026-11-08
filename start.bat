@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 (
  py -3 serve.py
) else (
  where python >nul 2>nul
  if errorlevel 1 (
    echo Install Python 3.10 or newer from python.org, then run start.bat again.
    pause
    exit /b 1
  )
  python serve.py
)
if errorlevel 1 pause

@echo off
setlocal
cd /d "%~dp0"
if exist "%~dp0dist\RF4S Save Editor.exe" (
  start "" "%~dp0dist\RF4S Save Editor.exe"
  exit /b 0
)
if exist "%~dp0.venv-desktop\Scripts\python.exe" (
  if not exist "%~dp0web\native-bundle.js" (
    echo Run npm run build:native-core before starting the native source version.
    pause
    exit /b 1
  )
  "%~dp0.venv-desktop\Scripts\python.exe" desktop.py
  if errorlevel 1 pause
  exit /b
)
echo Native executable not found in dist. See README.md for the native build instructions.
echo The portable EXE needs no installation. This launcher does not start a browser or server.
pause
exit /b 1

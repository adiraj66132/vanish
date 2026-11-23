@echo off
setlocal
cd /d "%~dp0"

set "VENV_DIR=.venv-local"
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"
set "PYTHON=py -3"

where py >nul 2>nul
if errorlevel 1 (
  where python >nul 2>nul
  if errorlevel 1 (
    echo Install Python 3 for Windows before running the app.
    goto :error
  )
  set "PYTHON=python"
) else (
  rem pygame 2.6 has no Python 3.14 wheels; prefer the newest supported interpreter.
  py -3.10 -c "import sys" >nul 2>nul && set "PYTHON=py -3.10"
  py -3.11 -c "import sys" >nul 2>nul && set "PYTHON=py -3.11"
  py -3.12 -c "import sys" >nul 2>nul && set "PYTHON=py -3.12"
  py -3.13 -c "import sys" >nul 2>nul && set "PYTHON=py -3.13"
)

if exist "%VENV_PY%" (
  "%VENV_PY%" -c "import sys; raise SystemExit(sys.version_info >= (3, 14))" >nul 2>nul
  if errorlevel 1 (
    echo [Vanish Lab] Replacing the local Python environment; Python 3.14 is not supported.
    rmdir /s /q "%VENV_DIR%"
  )
)
if not exist "%VENV_PY%" (
  echo [Vanish Lab] Creating the local Python environment with %PYTHON%...
  %PYTHON% -m venv "%VENV_DIR%"
  if errorlevel 1 goto :error
)

"%VENV_PY%" -c "import cv2, mediapipe, numpy, pyvirtualcam, pygame, PySide6" >nul 2>nul
if errorlevel 1 (
  echo [Vanish Lab] Installing required packages. Internet is only needed this time...
  "%VENV_PY%" -m pip install --upgrade pip
  if errorlevel 1 goto :error
  "%VENV_PY%" -m pip install -r requirements.txt
  if errorlevel 1 goto :error
)

echo [Vanish Lab] Starting the webcam...
"%VENV_PY%" vanish_cam.py %*
if errorlevel 1 goto :error
exit /b 0

:error
echo.
echo Could not start VanishCam. See README.md for common fixes.
pause
exit /b 1

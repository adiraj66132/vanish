@echo off
setlocal
cd /d "%~dp0"

set "VENV_DIR=.venv-build"
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"
set "PYTHON=py -3"

where py >nul 2>nul
if errorlevel 1 (
  where python >nul 2>nul
  if errorlevel 1 (
    echo Install Python 3 for Windows before building the executable.
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
    echo Replacing the build environment; Python 3.14 is not supported.
    rmdir /s /q "%VENV_DIR%"
  )
)
if not exist "%VENV_PY%" (
  echo Creating the build Python environment with %PYTHON%...
  %PYTHON% -m venv "%VENV_DIR%"
  if errorlevel 1 goto :error
)
if not exist "%VENV_PY%" (
  echo Could not create the build environment in %VENV_DIR%.
  goto :error
)

"%VENV_PY%" -c "import PyInstaller, cv2, mediapipe, numpy, pyvirtualcam, pygame, PySide6" >nul 2>nul
if errorlevel 1 (
  echo Installing build dependencies...
  "%VENV_PY%" -m pip install --upgrade pip
  if errorlevel 1 goto :error
  "%VENV_PY%" -m pip install -r requirements.txt "pyinstaller>=6,<7"
  if errorlevel 1 goto :error
)

echo Checking required MediaPipe models...
"%VENV_PY%" -c "from vanish_cam import download_models; download_models('normal'); download_models('goku')"
if errorlevel 1 goto :error

echo Running unit tests...
"%VENV_PY%" -m unittest discover
if errorlevel 1 goto :error

echo Checking resources...
"%VENV_PY%" vanish_cam.py --self-test
if errorlevel 1 goto :error

"%VENV_PY%" packaging\write_version.py
if errorlevel 1 goto :error

"%VENV_PY%" -m PyInstaller --noconfirm --distpath dist --workpath build VanishCam.spec
if errorlevel 1 goto :error

echo Self-testing the packaged app...
"dist\VanishCam\VanishCam.exe" --self-test
if errorlevel 1 goto :error

if defined SIGNTOOL if defined CERT_FILE if defined CERT_PASSWORD (
  echo Signing the executable...
  "%SIGNTOOL%" sign /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 /f "%CERT_FILE%" /p "%CERT_PASSWORD%" "dist\VanishCam\VanishCam.exe"
  if errorlevel 1 goto :error
)

where ISCC >nul 2>nul
if not errorlevel 1 (
  echo Building the installer...
  ISCC installer\vanishcam.iss
  if errorlevel 1 goto :error
  if defined SIGNTOOL if defined CERT_FILE if defined CERT_PASSWORD (
    "%SIGNTOOL%" sign /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 /f "%CERT_FILE%" /p "%CERT_PASSWORD%" "dist\VanishCamSetup.exe"
    if errorlevel 1 goto :error
  )
) else (
  echo Inno Setup not found; skipping installer. Add ISCC to PATH to build VanishCamSetup.exe.
)

echo.
echo Ready in dist\VanishCam
if exist "dist\VanishCamSetup.exe" echo Installer ready in dist\VanishCamSetup.exe
exit /b 0

:error
echo.
echo Build failed. Check the messages above.
pause
exit /b 1

@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if errorlevel 1 (
  echo Install Python 3 for Windows before building the executable.
  goto :error
)

py -3 -c "import PyInstaller, cv2, mediapipe, numpy, pyvirtualcam, pygame, PySide6" >nul 2>nul
if errorlevel 1 (
  echo Installing build dependencies...
  py -3 -m pip install -r requirements.txt "pyinstaller>=6,<7"
  if errorlevel 1 goto :error
)

echo Checking required MediaPipe models...
py -3 -c "from vanish_cam import download_models; download_models('normal'); download_models('goku')"
if errorlevel 1 goto :error

echo Running unit tests...
py -3 -m unittest discover
if errorlevel 1 goto :error

py -3 packaging\write_version.py
if errorlevel 1 goto :error

py -3 -m PyInstaller --noconfirm --distpath dist --workpath build VanishCam.spec
if errorlevel 1 goto :error

echo Self-testing the packaged app...
"dist\VanishCam\VanishCam.exe" --self-test
if errorlevel 1 goto :error

if defined SIGNTOOL (
  echo Signing the executable...
  "%SIGNTOOL%" sign /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 /f "%CERT_FILE%" /p "%CERT_PASSWORD%" "dist\VanishCam\VanishCam.exe"
  if errorlevel 1 goto :error
)

where ISCC >nul 2>nul
if not errorlevel 1 (
  echo Building the installer...
  ISCC installer\vanishcam.iss
  if errorlevel 1 goto :error
  if defined SIGNTOOL (
    "%SIGNTOOL%" sign /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 /f "%CERT_FILE%" /p "%CERT_PASSWORD%" "dist\VanishCamSetup.exe"
    if errorlevel 1 goto :error
  )
) else (
  echo Inno Setup not found; skipping installer. Install ISCC to build VanishCamSetup.exe.
)

echo.
echo Ready in dist\VanishCam and dist\VanishCamSetup.exe
exit /b 0

:error
echo.
echo Build failed. Check the messages above.
pause
exit /b 1

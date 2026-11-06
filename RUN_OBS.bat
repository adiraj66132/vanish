@echo off
call "%~dp0RUN_LOCAL.bat" --no-virtual-camera %*
exit /b %errorlevel%

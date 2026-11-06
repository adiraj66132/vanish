@echo off
call "%~dp0RUN_LOCAL.bat" --virtual-camera %*
exit /b %errorlevel%

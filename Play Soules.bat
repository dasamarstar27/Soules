@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel% equ 0 (
  py -3 play.py
) else (
  python play.py
)
if errorlevel 1 (
  echo.
  echo Soules could not start. Make sure Python 3.11 or newer is installed from python.org.
  echo If Python asks, choose Add Python to PATH during installation.
  pause
)

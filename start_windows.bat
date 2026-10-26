@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if errorlevel 1 (
  echo Python launcher not found. Install Python 3.10 or newer from https://www.python.org/downloads/
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo Creating Python virtual environment...
  py -m venv .venv
  if errorlevel 1 goto :error
)

echo Installing or checking dependencies...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :error

if not exist ".env" (
  copy ".env.example" ".env" >nul
  echo Created .env. Edit it and add your xAI key for live Grok responses.
)

echo.
echo Starting CareGuide at http://127.0.0.1:5000
".venv\Scripts\python.exe" app.py
goto :eof

:error
echo.
echo Setup failed. Check Python and internet connectivity, then run this file again.
pause
exit /b 1

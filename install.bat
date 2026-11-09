@echo off
cd /d "%~dp0"
echo Installing Python packages...
py -m pip install -r requirements.txt || python -m pip install -r requirements.txt
if not exist .env copy .env.example .env >nul
echo.
echo Done. Open the .env file, paste BOT_TOKEN and ADMIN_IDS, then run run_bot.bat
pause

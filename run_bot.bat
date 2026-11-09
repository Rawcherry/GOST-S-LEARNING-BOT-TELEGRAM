@echo off
rem Manual start with a visible console (for testing). Close the window to stop.
chcp 65001 >nul
cd /d "%~dp0"
py bot.py || python bot.py
pause

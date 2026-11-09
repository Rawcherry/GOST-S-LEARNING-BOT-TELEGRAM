@echo off
chcp 65001 >nul
cd /d "%~dp0"
py restart_bot.py || python restart_bot.py
pause

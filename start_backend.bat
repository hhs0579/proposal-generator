@echo off
cd /d "%~dp0backend"
call venv\Scripts\activate
echo Backend Server is starting...
uvicorn main:app --reload --port 8000
pause

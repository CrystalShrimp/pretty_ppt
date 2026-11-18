@echo off
cd /d "%~dp0"
echo ====================================================
echo   PPT Component Studio - Starting Web Server...
echo   URL: http://127.0.0.1:8765
echo ====================================================
start "" "http://127.0.0.1:8765"
python server.py
pause

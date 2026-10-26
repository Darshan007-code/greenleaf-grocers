@echo off
title GreenLeaf Grocers Production Server
color 0A
echo =========================================================
echo    GREENLEAF GROCERS - INVENTORY & SALES SYSTEM
echo =========================================================
echo.
echo Starting Production Server (Waitress WSGI)...
echo Local URL: http://127.0.0.1:5000
echo.
python serve_production.py
pause

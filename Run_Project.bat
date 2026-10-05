@echo off
title Running Crime Analytics Project
color 0B
echo =======================================================================
echo          CRIME DATA ANALYTICS - STARTING WEB PROJECT
echo =======================================================================
echo.
echo [1/2] Starting Flask Web Server...
start "" "http://127.0.0.1:5000/powerbi"
python app.py
pause

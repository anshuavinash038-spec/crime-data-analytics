@echo off
TITLE Crime Data Analytics - Production WSGI Server (Waitress)
color 0A
echo ======================================================================
echo  CRIME DATA ANALYTICS AND VISUALIZATION - PRODUCTION SERVER (WAITRESS)
echo ======================================================================
echo.
echo Starting Production Multi-Threaded WSGI Server on http://127.0.0.1:5000 ...
echo Press Ctrl+C to terminate the server.
echo.
waitress-serve --listen=127.0.0.1:5000 wsgi:app
pause

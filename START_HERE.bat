@echo off
REM Windows batch file to start the Census Demographics Lookup tool
echo ================================================
echo Census Demographics Lookup Tool
echo ================================================
echo.
echo Starting the application...
echo The app will open in your web browser automatically.
echo.
echo To stop the application, close this window.
echo ================================================
echo.

cd /d "%~dp0"
streamlit run main_app.py
pause

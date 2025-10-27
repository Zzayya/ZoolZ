@echo off
REM ZoolZ Flask App Launcher (Windows)
REM Double-click this file to start the app

cd /d "%~dp0"

echo =========================================
echo    ZoolZ - Multi-Purpose 3D Design Tool
echo =========================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo ERROR: Virtual environment not found!
    echo Please run setup from the project directory first:
    echo   python -m venv venv
    echo   venv\Scripts\activate
    echo   pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if dependencies are installed
echo Checking dependencies...
python -c "import flask" 2>nul
if errorlevel 1 (
    echo ERROR: Dependencies not installed!
    echo Please install dependencies first:
    echo   venv\Scripts\activate
    echo   pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

echo Dependencies OK
echo.
echo Starting ZoolZ...
echo.
echo =========================================
echo    App will open at: http://localhost:5001
echo =========================================
echo.
echo Press Ctrl+C to stop the server
echo.

REM Open browser after 3 seconds (in background)
start /b cmd /c "timeout /t 3 >nul && start http://localhost:5001"

REM Start Flask app
python app.py

echo.
echo Server stopped.
pause

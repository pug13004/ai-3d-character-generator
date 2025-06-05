@echo off
echo ========================================
echo AI-Powered 3D Character Generator
echo Starting Application...
echo ========================================
echo.

:: Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found
    echo Please run install.bat first
    pause
    exit /b 1
)

:: Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

:: Check if ComfyUI is running
echo Checking ComfyUI status...
curl -s http://127.0.0.1:8188/system_stats >nul 2>&1
if errorlevel 1 (
    echo Starting ComfyUI...
    start /B python -m comfyui.main --listen 127.0.0.1 --port 8188
    echo Waiting for ComfyUI to start...
    timeout /t 10 /nobreak >nul
) else (
    echo ComfyUI is already running
)

:: Start the main application
echo.
echo Starting main application...
echo Open your browser to: http://localhost:8080
echo.
echo Press Ctrl+C to stop the application
echo ========================================
python comprehensive_backend.py

echo.
echo Application stopped.
pause

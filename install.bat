@echo off
echo ========================================
echo AI-Powered 3D Character Generator
echo Automated Installation Script
echo ========================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11 or 3.12 from https://python.org
    pause
    exit /b 1
)

:: Check Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Found Python %PYTHON_VERSION%

:: Create virtual environment
echo.
echo Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

:: Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

:: Upgrade pip
echo.
echo Upgrading pip...
python -m pip install --upgrade pip

:: Install requirements
echo.
echo Installing Python dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install Python dependencies
    pause
    exit /b 1
)

:: Download models
echo.
echo Downloading AI models (this may take a while)...
python download_ai_models.py
if errorlevel 1 (
    echo WARNING: Some models may not have downloaded completely
    echo You can run 'python download_ai_models.py' later to retry
)

:: Setup configuration
echo.
echo Setting up configuration...
python setup_config.py

:: Create directories
echo.
echo Creating necessary directories...
if not exist "outputs" mkdir outputs
if not exist "uploads" mkdir uploads
if not exist "models" mkdir models
if not exist "workflows\custom" mkdir workflows\custom
if not exist "logs" mkdir logs

:: Set permissions (Windows)
echo Setting up permissions...
icacls outputs /grant Everyone:(OI)(CI)F /T >nul 2>&1
icacls uploads /grant Everyone:(OI)(CI)F /T >nul 2>&1

echo.
echo ========================================
echo Installation completed successfully!
echo ========================================
echo.
echo To start the application:
echo   1. Run: start.bat
echo   2. Open browser to: http://localhost:8080
echo.
echo For manual start:
echo   1. Run: venv\Scripts\activate.bat
echo   2. Run: python comprehensive_backend.py
echo.
echo Need help? Check README.md or visit:
echo https://github.com/pug13004/ai-3d-character-generator
echo.
pause

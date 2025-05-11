@echo off
REM KSP (Krwinkowy System Prezentowy) Installation Script
echo KSP Installation Script
echo =======================

REM Checking Python installation
echo Checking Python installation...
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python is not installed or not in PATH
    exit /b 1
)

REM Check Python version
for /f "tokens=*" %%a in ('python -c "import sys; print('{}.{}'.format(sys.version_info.major, sys.version_info.minor))"') do set PYTHON_VERSION=%%a
echo Python version detected: %PYTHON_VERSION%

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv
if %ERRORLEVEL% NEQ 0 (
    echo Error: Failed to create virtual environment
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
if %ERRORLEVEL% NEQ 0 (
    echo Error: Failed to activate virtual environment
    exit /b 1
)

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo Error: Failed to install dependencies
    exit /b 1
)

REM Create environment file
if not exist .env (
    echo Creating .env file from example...
    copy .env.example .env
    for /f "tokens=*" %%a in ('python -c "import secrets; print(secrets.token_hex(32))"') do set SECRET_KEY=%%a
    powershell -Command "(Get-Content .env) -replace 'your-secret-key-here', '%SECRET_KEY%' | Set-Content .env"
)

REM Run migrations
echo Setting up database...
python manage.py migrate
if %ERRORLEVEL% NEQ 0 (
    echo Error: Failed to apply database migrations
    exit /b 1
)

echo Setup complete! You can now run the server with:
echo $ python manage.py runserver
echo.
echo To create an admin user, run:
echo $ python manage.py createsuperuser

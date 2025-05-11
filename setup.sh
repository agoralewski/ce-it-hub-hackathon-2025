#!/bin/bash

# KSP (Krwinkowy System Prezentowy) Installation Script
echo "KSP Installation Script"
echo "======================="

# Checking Python installation
echo "Checking Python installation..."
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    echo "Error: Python is not installed or not in PATH"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$($PYTHON_CMD -c "import sys; print('{}.{}'.format(sys.version_info.major, sys.version_info.minor))")
echo "Python version detected: $PYTHON_VERSION"

# Create virtual environment
echo "Creating virtual environment..."
$PYTHON_CMD -m venv venv
if [ $? -ne 0 ]; then
    echo "Error: Failed to create virtual environment"
    exit 1
fi

# Activate virtual environment
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
    echo "Activating virtual environment (Windows)..."
    source venv/Scripts/activate
else
    echo "Activating virtual environment (Unix)..."
    source venv/bin/activate
fi

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Error: Failed to install dependencies"
    exit 1
fi

# Create environment file
if [ ! -f .env ]; then
    echo "Creating .env file from example..."
    cp .env.example .env
    SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
    sed -i.bak "s/your-secret-key-here/$SECRET_KEY/" .env
    rm -f .env.bak
fi

# Run migrations
echo "Setting up database..."
$PYTHON_CMD manage.py migrate
if [ $? -ne 0 ]; then
    echo "Error: Failed to apply database migrations"
    exit 1
fi

echo "Setup complete! You can now run the server with:"
echo "$ python manage.py runserver"
echo ""
echo "To create an admin user, run:"
echo "$ python manage.py createsuperuser"

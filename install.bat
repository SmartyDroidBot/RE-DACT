@echo off
echo --- Step 1: Creating a virtual environment ---
python -m venv .venv
if %errorlevel% neq 0 (
    echo Failed to create virtual environment.
    exit /b %errorlevel%
)
echo Virtual environment created successfully.

echo --- Step 2: Activating the virtual environment ---
call .\.venv\Scripts\activate
if %errorlevel% neq 0 (
    echo Failed to activate virtual environment.
    exit /b %errorlevel%
)
echo Virtual environment activated successfully.

echo --- Step 3: Installing requirements ---
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Failed to install requirements.
    exit /b %errorlevel%
)
echo Requirements installed successfully.

echo --- Step 4: Changing directory to redact and making migrations ---
cd redact
if %errorlevel% neq 0 (
    echo Failed to change directory.
    exit /b %errorlevel%
)
python manage.py makemigrations
if %errorlevel% neq 0 (
    echo Failed to make migrations.
    exit /b %errorlevel%
)
echo Migrations created successfully.

echo --- Step 5: Installing Ollama ---
pip install ollama
if %errorlevel% neq 0 (
    echo Failed to install Ollama.
    exit /b %errorlevel%
)
echo Ollama installed successfully.

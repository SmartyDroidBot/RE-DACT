@echo off
REM Check if Python is installed
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Python is not installed. Please install Python and try again.
    exit /b 1
)

REM Create virtual environment
python -m venv .venv

REM Activate virtual environment
call .venv\Scripts\activate

REM Install packages from requirements.txt
pip install -r requirements.txt

echo Virtual environment setup complete.

REM Clone deberta_finetuned_pii repository
git clone https://github.com/your-repo/deberta_finetuned_pii.git redact/services/deberta_finetuned_pii

echo Repository cloned to redact/services/deberta_finetuned_pii.

REM Change directory to redact
cd redact

REM Make migrations
python manage.py makemigrations
python manage.py migrate

echo Migrations complete.
REM Prompt user for the path to tesseract.exe
set /p TESSERACT_PATH=Enter the path to tesseract.exe: 

REM Update utils.py with the provided path
powershell -Command "(Get-Content utils.py) -replace 'tesseract_cmd = .*', 'tesseract_cmd = \"%TESSERACT_PATH%\"' | Set-Content utils.py"

echo Updated utils.py with the provided tesseract path.

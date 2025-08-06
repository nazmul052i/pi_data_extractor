@echo off
setlocal

REM === 1. Check if Python is installed ===
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.8+ from https://www.python.org/downloads/ and re-run this script.
    pause
    exit /b 1
)

REM === 2. Create venv if it doesn't exist ===
IF NOT EXIST venv (
    echo [INFO] Creating virtual environment...
    python -m venv venv
    IF %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

REM === 3. Activate venv ===
call venv\Scripts\activate
IF ERRORLEVEL 1 (
    echo [ERROR] Failed to activate virtual environment.
    pause
    exit /b 1
)

REM === 4. Check for requirements.txt and install ===
IF EXIST requirements.txt (
    echo [INFO] Checking/installing required packages...
    pip install --upgrade pip
    pip install -r requirements.txt
    IF %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to install requirements.
        pause
        exit /b 1
    )
) ELSE (
    echo [WARNING] requirements.txt not found. Skipping requirements installation.
)

REM === 5. Run the program ===
echo [INFO] Running main.py...
python main.py
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Program exited with errors.
    pause
    exit /b 1
)

REM === End ===
pause
endlocal

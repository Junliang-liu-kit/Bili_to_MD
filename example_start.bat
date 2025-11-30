@echo off
setlocal enabledelayedexpansion

REM Get script directory
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

REM Change to script directory
cd /d "%SCRIPT_DIR%"
if %errorlevel% neq 0 (
    echo [ERROR] Cannot change to directory: %SCRIPT_DIR%
    echo Please check if the path is correct
    pause
    exit /b 1
)

echo ========================================
echo Bilibili Favorite Sync Tool
echo ========================================
echo Working directory: %CD%
echo.

REM Check if uv is installed
where uv >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] uv command not found
    echo Please install uv first: https://github.com/astral-sh/uv
    pause
    exit /b 1
)

REM Check if main.py exists
if not exist "main.py" (
    echo [ERROR] main.py not found
    echo Please make sure the script is in the project root directory
    pause
    exit /b 1
)

REM Run main program using uv (uv will manage virtual environment automatically)
echo Starting program...
echo.
uv run main.py

REM Check program execution result
if %errorlevel% neq 0 (
    echo.
    echo [WARNING] Program exited with error code: %errorlevel%
) else (
    echo.
    echo [SUCCESS] Program completed successfully
)

echo.
pause
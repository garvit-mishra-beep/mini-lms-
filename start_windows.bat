@echo off
setlocal enabledelayedexpansion
title MiniLMS - Learning Management System (DBMS PBL)
cd /d "%~dp0"
color 0B

echo ========================================================================
echo                  MINILMS - DBMS PBL ENTERPRISE UPGRADE
echo          Modular Flask LMS with MySQL 8.0 Architecture ^& Security
echo ========================================================================
echo.

:: 1. Check Python
set PYTHON_CMD=py
where %PYTHON_CMD% >nul 2>nul
if %errorlevel% neq 0 (
    set PYTHON_CMD=python
    where !PYTHON_CMD! >nul 2>nul
    if !errorlevel! neq 0 (
        echo [ERROR] Python was not found on your system PATH.
        echo Please install Python 3.10+ and add it to PATH.
        pause
        exit /b 1
    )
)
echo [*] Python detected: !PYTHON_CMD!

:: 2. Check Environment Configuration (.env)
if not exist ".env" (
    echo.
    echo [WARNING] .env file not found.
    if exist ".env.example" (
        echo [*] Initializing .env from .env.example...
        copy ".env.example" ".env" >nul
        echo [OK] .env created! Please review DB_PASSWORD before proceeding if different from default.
    ) else (
        echo [ERROR] Neither .env nor .env.example exists. Please create .env.
        pause
        exit /b 1
    )
)

:: 3. Verify Dependencies
echo [*] Checking required dependencies from requirements.txt...
!PYTHON_CMD! -m pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo [WARNING] Pip encountered an issue installing dependencies. Proceeding anyway...
)

:MENU
echo.
echo ========================================================================
echo                               OPERATIONS MENU
echo ========================================================================
echo  [1] Start MiniLMS Web Server (Auto-migrates, seeds passwords ^& launches)
echo  [2] Run Automated Security ^& Concurrency Test Suite
echo  [3] Run Database Schema Migrations (v006, v007)
echo  [4] Rollback Latest Database Schema Migration
echo  [5] Seed Password Hashes ^& Reset Demo Role Accounts
echo  [6] Open MySQL CLI Client (minilms_db)
echo  [7] Exit
echo ========================================================================
echo.

set /p CHOICE="Select an option [1-7] (Default is 1): "
if "%CHOICE%"=="" set CHOICE=1

if "%CHOICE%"=="1" goto START_APP
if "%CHOICE%"=="2" goto RUN_TESTS
if "%CHOICE%"=="3" goto RUN_MIGRATIONS
if "%CHOICE%"=="4" goto RUN_ROLLBACK
if "%CHOICE%"=="5" goto SEED_PASSWORDS
if "%CHOICE%"=="6" goto OPEN_MYSQL
if "%CHOICE%"=="7" goto EXIT_SCRIPT

echo [!] Invalid selection. Please choose 1 to 7.
goto MENU

:START_APP
echo.
echo [*] Step 1/3: Checking database migrations...
!PYTHON_CMD! database/migrate.py
echo.
echo [*] Step 2/3: Checking demo password credentials...
!PYTHON_CMD! database/seed_passwords.py
echo.
echo [*] Step 3/3: Launching MiniLMS Flask Server...
echo [!] Server URL: http://127.0.0.1:5000
echo [!] Press CTRL+C to stop the web server.
echo.
!PYTHON_CMD! app.py
goto MENU

:RUN_TESTS
echo.
echo [*] Running MiniLMS Automated Verification Suite...
!PYTHON_CMD! -m unittest tests/test_minilms.py -v
echo.
pause
goto MENU

:RUN_MIGRATIONS
echo.
echo [*] Executing database schema migrations...
!PYTHON_CMD! database/migrate.py
echo.
pause
goto MENU

:RUN_ROLLBACK
echo.
echo [*] Executing migration rollback...
!PYTHON_CMD! database/rollback.py
echo.
pause
goto MENU

:SEED_PASSWORDS
echo.
echo [*] Generating secure scrypt password hashes for users table...
!PYTHON_CMD! database/seed_passwords.py
echo.
pause
goto MENU

:OPEN_MYSQL
echo.
echo [*] Opening MySQL Command Line Client...
mysql -u root -p minilms_db
if %errorlevel% neq 0 (
    echo [!] Standard mysql command failed. Checking default install directory...
    if exist "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" (
        "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -p minilms_db
    ) else (
        echo [ERROR] mysql.exe not found on PATH.
    )
)
goto MENU

:EXIT_SCRIPT
echo.
echo Thank you for using MiniLMS!
exit /b 0

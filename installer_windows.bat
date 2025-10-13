@echo off
:: Installer Script for TTS Library - Windows
chcp 65001 >nul 2>&1

:: SOFORTIGE Python-Prüfung – bevor irgendetwas passiert
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Python is not installed or not in PATH.
    echo.
    echo Supported Python versions: 3.8, 3.9, 3.10, 3.11, 3.12
    echo Python 3.13+ is not supported due to lack of compatible wheels for critical dependencies
    echo.
    echo Please download and install Python 3.12.x Version from:
    echo   https://www.python.org/downloads/
    echo.
    echo IMPORTANT: Check "Add Python to PATH" during installation!
    echo.
    pause
    exit /b 1
)

:: Prüfe, ob Visual C++ Redistributable installiert ist
if not exist "C:\Windows\System32\vcruntime140.dll" (
    echo.
    echo ERROR: Microsoft Visual C++ Redistributable is missing.
    echo Please download and install it from:
    echo   https://aka.ms/vs/17/release/vc_redist_x64.exe
    echo.
    echo After installation, run this script again.
    echo.
    pause
    exit /b 1
)

echo Debug: Script started in directory: %~dp0

echo Debug: Checking log directory creation...
if not exist "logs" mkdir "logs" >nul 2>&1
if not exist "logs" (
    echo Error: Could not create 'logs' directory.
    exit /b 1
)
set "LOG_FILE=%~dp0logs\installer.log"
echo. > "%LOG_FILE%" 2>nul
if errorlevel 1 (
    echo Error: Could not create log file.
    exit /b 1
)

:: Pfade definieren
set "VENV_PATH=%~dp0bin\ai_env"

goto :main_code

:: =============== FUNKTIONEN ===============
:log_message
setlocal enabledelayedexpansion
set "level=%~1"
set "message=%~2"
if "!level!"=="" set "level=INFO"
if "!message!"=="" set "message=(no message)"
for /f "usebackq delims=" %%i in (`powershell -command "Get-Date -UFormat '%%d.%%m.%%Y %%H:%%M'" 2^>nul`) do set "dt=%%i"
if "!dt!"=="" (set "date_str=01.01.1970" & set "time_str=00:00") else (set "date_str=!dt:~0,10!" & set "time_str=!dt:~11,5!")
echo [!date_str! !time_str!] [!level!] !message! >> "!LOG_FILE!"
echo [!date_str! !time_str!] [!level!] !message!
endlocal
goto :eof

:error_exit
setlocal
set "msg=%*"
call :log_message ERROR "!msg!"
echo.
echo Error: !msg!
echo.
exit /b 1
goto :eof

:success
setlocal
set "msg=%*"
call :log_message SUCCESS "!msg!"
echo !msg!
endlocal
goto :eof

:warning
setlocal
set "msg=%*"
call :log_message WARNING "!msg!"
echo !msg!
endlocal
goto :eof

:info
setlocal
set "msg=%*"
call :log_message INFO "!msg!"
echo !msg!
endlocal
goto :eof

:main_code
cls
echo +----------------------------------+
echo ^| TTS Library Installation Script! ^|
echo +----------------------------------+

ver | findstr /i "Windows" >nul
if %errorlevel% neq 0 call :error_exit "This script is for Windows only."

net session >nul 2>&1
if %errorlevel% neq 0 call :warning "No admin rights. Some steps may fail."

call :info "Starting installation..."

python --version >nul 2>&1
if %errorlevel% neq 0 call :error_exit "Python not found. Install from www.python.org/downloads"

for /f "tokens=2" %%v in ('python --version 2^>^&1') do set "PY_VER=%%v"
call :info "Found Python: %PY_VER%"

:: Stelle sicher, dass bin/ existiert
if not exist "bin" mkdir "bin" >nul 2>&1

call :info "Creating virtual environment in 'bin\ai_env'..."
python -m venv "%VENV_PATH%"
if %errorlevel% neq 0 call :error_exit "Failed to create virtual environment in bin\ai_env."
call :success "Virtual environment created."

:: Prüfen, ob setup.py existiert
if not exist "setup.py" if not exist "pyproject.toml" (
    call :error_exit "Missing 'setup.py' or 'pyproject.toml' in %~dp0"
)

:: Installation durchführen
set "TEMP_INSTALL=%TEMP%\install_tts.bat"
(
    echo @echo off
    echo call "%VENV_PATH%\Scripts\activate.bat"
    echo if errorlevel 1 exit /b 1
    echo python -m pip install --upgrade pip
    echo if errorlevel 1 exit /b 1
    echo python -m pip install "%~dp0."
    echo if errorlevel 1 exit /b 1
    echo echo SUCCESS: Package installed.
) > "%TEMP_INSTALL%"

call "%TEMP_INSTALL%"
set "ERR=%errorlevel%"
del "%TEMP_INSTALL%" >nul 2>&1
if %ERR% neq 0 call :error_exit "Package installation failed."

call :success "TTS library installed!"

:: Post-Install-Skript
if exist "post_install.py" (
    call :info "Running post-install script..."
    call "%VENV_PATH%\Scripts\activate.bat"
    python "post_install.py"
    if errorlevel 1 call :warning "Post-install script failed."
    call "%VENV_PATH%\Scripts\deactivate.bat" >nul 2>&1
)

call :success "Installation completed!"

echo.
echo +----------------------------------+
echo ^|      Installation Summary:       ^|
echo +----------------------------------+
echo - Virtual environment: bin\ai_env
echo - Package installed from current directory
if exist "post_install.py" echo - Post-install script executed
echo.
echo To use the TTS library:
echo   bin\ai_env\Scripts\activate.bat
echo.
echo Then run:
echo   python bin\cli_example_tts.py
echo.
call :log_message SUCCESS "Installation finished successfully."
pause

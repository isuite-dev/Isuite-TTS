@echo off
REM Activate script as executable
REM Run this file directly or from command line:
REM run_windows_example.bat

cd /d "%~dp0"
call bin\ai_env\Scripts\activate.bat
python bin\gui_example_tts.py
pause

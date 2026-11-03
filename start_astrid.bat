@echo off
title Astrid Cyber Terminal
cd /d "%~dp0"
python main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] An error occurred while running Astrid.
    pause
)

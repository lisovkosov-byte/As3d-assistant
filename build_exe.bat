@echo off
title Building Astrid Executable
cd /d "%~dp0"
echo ==========================================
echo    СБОРКА ОДНОГО ФАЙЛА ASTRID.EXE (.EXE)
echo ==========================================
echo.
echo [1/2] Очистка старых сборок...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul

echo [2/2] Запуск PyInstaller (OneFile)...
pyinstaller --noconfirm --onefile --windowed ^
    --name "Astrid" ^
    --add-data "presets.json;." ^
    --add-data "config.example.json;." ^
    --hidden-import "speech_recognition" ^
    --hidden-import "edge_tts" ^
    --hidden-import "pygame" ^
    --hidden-import "win32api" ^
    --hidden-import "win32con" ^
    --hidden-import "win32gui" ^
    --hidden-import "winreg" ^
    --hidden-import "requests" ^
    --hidden-import "urllib3" ^
    src\main.py

echo.
if %ERRORLEVEL% equ 0 (
    echo ==========================================
    echo   СБОРКА УСПЕШНО ЗАВЕРШЕНА!
    echo   Готовый один файл: dist\Astrid.exe
    echo ==========================================
) else (
    echo [ОШИБКА] Не удалось собрать проект.
)
pause

@echo off
cd /d "%~dp0"
title Quilltale TRPG Spectator Mode
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" scripts\spectate_launcher.py
) else (
    python scripts\spectate_launcher.py
)
echo.
pause

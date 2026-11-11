@echo off
setlocal
title CyberJobHunter
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo No se encuentra el entorno virtual. Sigue la instalacion del README.
    pause
    exit /b 1
)
echo Iniciando CyberJobHunter...
echo Mantiene esta ventana abierta mientras usas el panel.
echo Para detenerlo, pulsa Ctrl+C o cierra esta ventana.
echo.
".venv\Scripts\python.exe" "frontend.py" --open-browser
if errorlevel 1 (
    echo.
    echo No se ha podido iniciar el panel. Revisa el mensaje anterior.
    pause
)

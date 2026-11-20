@echo off
title Conciliador BDV
cd /d "%~dp0"
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

:: Asegurar que las rutas de Python esten disponibles en la sesion actual
if exist "%LOCALAPPDATA%\Programs\Python\Launcher" set "PATH=%LOCALAPPDATA%\Programs\Python\Launcher;%PATH%"
if exist "%LOCALAPPDATA%\Programs\Python\Python312" set "PATH=%LOCALAPPDATA%\Programs\Python\Python312;%PATH%"

if not exist .venv\Scripts\python.exe (
  echo Primera vez: configurando el entorno, espera un momento...
  py -3.12 -m venv .venv 2>nul || py -m venv .venv 2>nul || python -m venv .venv
  if not exist .venv\Scripts\python.exe (
    echo.
    echo [ERROR] No se pudo encontrar Python instalado en tu equipo.
    echo Asegurate de instalar Python 3.10 o superior y marcar "Add Python to PATH".
    echo.
    pause
    exit /b 1
  )
)

:: Instala dependencias la primera vez y cada vez que cambie requirements.txt
fc /b requirements.txt .venv\requirements.instalado >nul 2>&1
if errorlevel 1 (
  echo Instalando dependencias...
  .venv\Scripts\python -m pip install --default-timeout 1000 -q -r requirements.txt && copy /y requirements.txt .venv\requirements.instalado >nul
)

if not exist .env (
  copy .env.example .env >nul
  echo Llena tus datos en el archivo que se va a abrir, guardalo y cierralo.
  notepad .env
)

.venv\Scripts\python app.py %*
pause

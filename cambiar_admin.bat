@echo off
title Conciliador BDV - Administrador
cd /d "%~dp0"
chcp 65001 >nul
set PYTHONUTF8=1
:: Crea un administrador nuevo o le cambia la clave a uno existente (por si se olvidó).
if not exist .venv\Scripts\python.exe (
  echo Primero abre el programa una vez con iniciar.bat
  pause
  exit /b 1
)
.venv\Scripts\python app.py --nuevo-admin
pause

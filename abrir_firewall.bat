@echo off
title Conciliador BDV - Abrir firewall
cd /d "%~dp0"
:: Permite que las computadoras de las cajeras entren al Conciliador por la red local.
:: Ejecutar UNA vez en la computadora principal: clic derecho -> "Ejecutar como administrador".

net session >nul 2>&1
if errorlevel 1 (
  echo.
  echo [ERROR] Este archivo necesita permisos de administrador.
  echo Cierra esta ventana, haz clic derecho sobre abrir_firewall.bat y elige
  echo "Ejecutar como administrador".
  echo.
  pause
  exit /b 1
)

set PUERTO=5000
if exist .env for /f "tokens=2 delims==" %%a in ('findstr /b /c:"BDV_PUERTO=" .env') do set PUERTO=%%a

netsh advfirewall firewall delete rule name="Conciliador BDV" >nul 2>&1
netsh advfirewall firewall add rule name="Conciliador BDV" dir=in action=allow protocol=TCP localport=%PUERTO% profile=private
if errorlevel 1 (
  echo [ERROR] No se pudo crear la regla del firewall.
) else (
  echo.
  echo Listo: el puerto %PUERTO% queda abierto solo para redes de tipo "Privada".
  echo Verifica que la red de esta computadora este marcada como Privada:
  echo   Configuracion ^> Red e Internet ^> Propiedades de la red ^> Perfil de red: Privada
)
echo.
pause

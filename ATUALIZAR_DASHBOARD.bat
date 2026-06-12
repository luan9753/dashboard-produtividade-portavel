@echo off
title Atualizar Dashboard de Produtividade
cd /d "%~dp0"
set PY=%LOCALAPPDATA%\Programs\Python\Python312\python.exe
if not exist "%PY%" set PY=py -3
echo.
echo  Atualizando dashboard com dados do AuraVTC (ODBC)...
"%PY%" "%~dp0atualizar_dashboard.py"
if %ERRORLEVEL% NEQ 0 (
  echo.
  echo  ERRO ao atualizar. Veja a mensagem acima.
  echo  Se o HTML estiver corrompido, o script tenta restaurar do WorkSpace.
  pause
  exit /b 1
)
echo.
echo  Concluido. Abrindo dashboard...
start "" "%~dp0dashboard_produtividade_completo.html"

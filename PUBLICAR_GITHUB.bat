@echo off
title Publicar Dashboard no GitHub
cd /d "%~dp0"

set PY=%LOCALAPPDATA%\Programs\Python\Python312\python.exe
if not exist "%PY%" set PY=py -3

set GIT=C:\Program Files\Git\bin\git.exe
if not exist "%GIT%" (
  echo.
  echo  ERRO: Git nao encontrado em "%GIT%"
  echo  Instale o Git for Windows ou ajuste o caminho neste .bat
  pause
  exit /b 1
)

echo.
echo  [1/4] Atualizando dashboard com dados do AuraVTC...
"%PY%" "%~dp0atualizar_dashboard.py"
if %ERRORLEVEL% NEQ 0 (
  echo.
  echo  ERRO ao atualizar. Nada foi enviado ao GitHub.
  pause
  exit /b 1
)

echo.
echo  [2/4] Preparando arquivos para o GitHub...
"%GIT%" add dashboard_produtividade_completo.html index.html equip-card-overrides.css
if %ERRORLEVEL% NEQ 0 (
  echo  ERRO ao adicionar arquivos no git.
  pause
  exit /b 1
)

"%GIT%" diff --cached --quiet
if %ERRORLEVEL% EQU 0 (
  echo.
  echo  Nenhuma alteracao detectada no HTML/CSS apos a atualizacao.
  echo  O GitHub ja esta com a mesma versao local.
  echo.
  echo  Link: https://luan9753.github.io/dashboard-produtividade-portavel/
  pause
  exit /b 0
)

echo.
echo  [3/4] Criando commit...
for /f "tokens=1-3 delims=/ " %%a in ("%date%") do set DATA=%%c-%%b-%%a
for /f "tokens=1-2 delims=: " %%a in ("%time%") do set HORA=%%a:%%b
"%GIT%" commit -m "Atualiza dados do dashboard (%DATA% %HORA%)"
if %ERRORLEVEL% NEQ 0 (
  echo  ERRO ao criar commit.
  pause
  exit /b 1
)

echo.
echo  [4/4] Enviando para o GitHub...
"%GIT%" push origin main
if %ERRORLEVEL% NEQ 0 (
  echo.
  echo  ERRO no push. Verifique internet, login no GitHub e branch main.
  pause
  exit /b 1
)

echo.
echo  Publicado com sucesso!
echo.
echo  Aguarde 1-2 minutos e abra:
echo  https://luan9753.github.io/dashboard-produtividade-portavel/
echo.
echo  Dashboard direto:
echo  https://luan9753.github.io/dashboard-produtividade-portavel/dashboard_produtividade_completo.html
echo.
pause
